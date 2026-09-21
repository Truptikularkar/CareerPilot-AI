import hashlib
import secrets
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, Dict, Any, List

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError

from careerpilot.core.logging import get_logger
from careerpilot.core.config import settings
from careerpilot.db.session import get_db
from careerpilot.db.schema import UserDB, UserSessionDB, CandidateProfileDB
from careerpilot.models.auth import User, UserCreate, UserLogin, UserSession, PasswordChange
from careerpilot.models.candidate import CandidateProfile

logger = get_logger("careerpilot.auth")
_ph = PasswordHasher()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AuthService:
    """
    Production authentication and session management service.
    Features:
    - Argon2id password hashing (RFC 9106)
    - High-entropy cryptographic session tokens (SHA-256 stored hash)
    - Multi-device session tracking and timeout enforcement
    - Streamlit auth gatekeeper (require_auth)
    """

    DEFAULT_EXPIRY_HOURS = 168  # 7 days

    @classmethod
    def hash_password(cls, password: str) -> str:
        """Hashes password using Argon2id."""
        return _ph.hash(password)

    @classmethod
    def _hash_token(cls, token: str) -> str:
        """Computes SHA-256 hash of raw session token for secure database storage."""
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @classmethod
    def validate_password_strength(cls, password: str) -> Tuple[bool, str]:
        """
        Validates password strength according to security standards:
        - Minimum 8 characters
        - At least 1 uppercase letter
        - At least 1 lowercase letter
        - At least 1 numeric digit
        - At least 1 special character
        """
        if not password or len(password) < 8:
            return False, "Password must be at least 8 characters long."
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter."
        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter."
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one number."
        special_chars = set("!@#$%^&*()-_=+[]{}|;:'\",.<>?/`~\\")
        if not any(c in special_chars for c in password):
            return False, "Password must contain at least one special character."
        return True, "Password meets security requirements."

    @classmethod
    def verify_password(cls, password_hash: str, candidate_password: str) -> bool:
        """Verifies candidate password against Argon2id hash without timing leaks."""
        try:
            return _ph.verify(password_hash, candidate_password)
        except (VerifyMismatchError, InvalidHashError):
            return False


    @classmethod
    def register_user(
        cls,
        user_in: Optional[UserCreate] = None,
        *,
        email: Optional[str] = None,
        password: Optional[str] = None,
        full_name: Optional[str] = None,
    ) -> User:
        """
        Registers a new user account, creates an associated CandidateProfileDB,
        and returns the user domain model. Rejects registrations for existing emails.
        """
        if user_in is None:
            if not email or not password or not full_name:
                raise ValueError("email, password, and full_name are required for registration.")
            user_in = UserCreate(email=email, password=password, full_name=full_name)

        email_clean = user_in.email.strip().lower()

        with get_db() as db:
            existing = db.query(UserDB).filter(UserDB.email == email_clean).first()
            if existing:
                raise ValueError(f"An account with email '{email_clean}' is already registered. Please sign in.")

            user_id = f"usr_{uuid.uuid4().hex[:12]}"
            cand_id = f"cand_{user_id}"
            pwd_hash = cls.hash_password(user_in.password)

            new_user = UserDB(
                id=user_id,
                email=email_clean,
                password_hash=pwd_hash,
                full_name=user_in.full_name.strip(),
                is_active=True,
                created_at=utc_now(),
                updated_at=utc_now(),
            )
            db.add(new_user)

            # Create initial user-owned candidate profile
            new_profile = CandidateProfileDB(
                id=cand_id,
                user_id=user_id,
                full_name=user_in.full_name.strip(),
                email=email_clean,
                professional_summary="Professional candidate profile. Update your summary in Candidate Profile.",
                skills_json=[],
                experiences_json=[],
                projects_json=[],
                education_json=[],
                certifications_json=[],
                achievements_json=[],
                preferences_json={},
                created_at=utc_now(),
                updated_at=utc_now(),
            )
            db.add(new_profile)
            db.commit()
            db.refresh(new_user)

            logger.info("Registered new user '%s' (%s)", email_clean, user_id)
            return User(
                id=new_user.id,
                email=new_user.email,
                full_name=new_user.full_name,
                is_active=new_user.is_active,
                created_at=new_user.created_at,
                last_login_at=new_user.last_login_at,
                candidate_id=cand_id,
            )

    @classmethod
    def authenticate(
        cls,
        email: str,
        password: str,
        device_info: str = "Desktop/Laptop",
        ip_address: Optional[str] = None,
    ) -> Tuple[User, str]:
        """
        Authenticates credentials against Argon2id hash.
        Creates an active session and returns (User, raw_session_token).
        """
        email_clean = email.strip().lower()
        password_clean = password.strip()

        from careerpilot.db.session import init_db
        init_db()

        with get_db() as db:
            user_db = db.query(UserDB).filter(UserDB.email == email_clean).first()
            if not user_db:
                logger.warning("Failed login attempt for nonexistent user: %s", email_clean)
                raise ValueError("Invalid email or password.")

            if not user_db.is_active:
                logger.warning("Login attempted for deactivated account: %s", email_clean)
                raise ValueError("Account is deactivated. Please contact support.")

            if not cls.verify_password(user_db.password_hash, password_clean):
                logger.warning("Invalid password for user: %s", email_clean)
                raise ValueError("Invalid email or password.")

            # Update last login timestamp
            now = utc_now()
            user_db.last_login_at = now

            # Issue session token
            token = secrets.token_urlsafe(32)
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            session_id = f"sess_{uuid.uuid4().hex[:12]}"
            expires_at = now + timedelta(hours=cls.DEFAULT_EXPIRY_HOURS)

            new_session = UserSessionDB(
                id=session_id,
                user_id=user_db.id,
                token_hash=token_hash,
                device_info=device_info,
                ip_address=ip_address,
                expires_at=expires_at,
                is_active=True,
                created_at=now,
                last_activity_at=now,
            )
            db.add(new_session)

            # Find linked candidate profile ID
            cand_db = db.query(CandidateProfileDB).filter(CandidateProfileDB.user_id == user_db.id).first()
            if not cand_db and (user_db.id == "usr_trupti_kularkar" or user_db.email in ("kularkartrupti123@gmail.com", "kularkartrupti@gmail.com")):
                cand_db = db.query(CandidateProfileDB).filter(CandidateProfileDB.id == "trupti_kularkar").first()
                if cand_db:
                    cand_db.user_id = user_db.id

            if not cand_db:
                cand_id = f"cand_{uuid.uuid4().hex[:8]}"
                cand_db = CandidateProfileDB(
                    id=cand_id,
                    user_id=user_db.id,
                    full_name=user_db.full_name,
                    email=user_db.email,
                    professional_summary="Professional candidate profile. Update your summary in Candidate Profile.",
                    skills_json=[],
                    experiences_json=[],
                    projects_json=[],
                    education_json=[],
                    certifications_json=[],
                    achievements_json=[],
                    preferences_json={},
                    created_at=now,
                    updated_at=now,
                )
                db.add(cand_db)

            cand_id = cand_db.id
            db.commit()
            logger.info("User '%s' successfully authenticated from %s", email_clean, device_info)

            user_model = User(
                id=user_db.id,
                email=user_db.email,
                full_name=user_db.full_name,
                is_active=user_db.is_active,
                created_at=user_db.created_at,
                last_login_at=user_db.last_login_at,
                candidate_id=cand_id,
            )
            try:
                import streamlit as st
                st.session_state["authenticated_user"] = user_model
                st.session_state["authenticated_candidate_id"] = cand_id
                st.session_state["auth_session_token"] = token
            except Exception:
                pass
            return user_model, token

    @classmethod
    def login_demo_user(cls, device_info: str = "Desktop / Laptop") -> Tuple[User, str]:
        """
        Convenience method to authenticate as the verified sample candidate (Trupti Kularkar)
        for instant 1-click exploration and portfolio evaluation without credentials.
        """
        from careerpilot.db.session import init_db
        init_db()

        with get_db() as db:
            user_db = db.query(UserDB).filter(
                (UserDB.id == "usr_trupti_kularkar") | (UserDB.email == "kularkartrupti123@gmail.com")
            ).first()

            if not user_db:
                user_db = UserDB(
                    id="usr_trupti_kularkar",
                    email="kularkartrupti123@gmail.com",
                    password_hash=cls.hash_password("9834055766@Liza"),
                    full_name="Trupti Kularkar",
                    is_active=True,
                    created_at=utc_now(),
                    updated_at=utc_now(),
                )
                db.add(user_db)
                db.commit()
                db.refresh(user_db)

            cand_db = db.query(CandidateProfileDB).filter(
                (CandidateProfileDB.user_id == user_db.id) | (CandidateProfileDB.id == "trupti_kularkar")
            ).first()

            if cand_db and not cand_db.user_id:
                cand_db.user_id = user_db.id

            now = utc_now()
            user_db.last_login_at = now

            token = secrets.token_urlsafe(32)
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            session_id = f"sess_{uuid.uuid4().hex[:12]}"
            expires_at = now + timedelta(hours=cls.DEFAULT_EXPIRY_HOURS)

            new_session = UserSessionDB(
                id=session_id,
                user_id=user_db.id,
                token_hash=token_hash,
                device_info=device_info,
                expires_at=expires_at,
                is_active=True,
                created_at=now,
                last_activity_at=now,
            )
            db.add(new_session)
            db.commit()

            cand_id = cand_db.id if cand_db else "trupti_kularkar"
            user_model = User(
                id=user_db.id,
                email=user_db.email,
                full_name=user_db.full_name,
                is_active=user_db.is_active,
                created_at=user_db.created_at,
                last_login_at=user_db.last_login_at,
                candidate_id=cand_id,
            )
            try:
                import streamlit as st
                st.session_state["authenticated_user"] = user_model
                st.session_state["authenticated_candidate_id"] = cand_id
                st.session_state["auth_session_token"] = token
            except Exception:
                pass
            logger.info("Demo user '%s' successfully signed in via 1-click guest mode.", user_db.email)
            return user_model, token

    @classmethod
    def login(cls, user_login: UserLogin) -> Tuple[Optional[str], Optional[User], Optional[str]]:
        """
        Convenience login method accepting UserLogin model.
        Returns (raw_session_token, user, error_message).
        """
        try:
            user_model, token = cls.authenticate(
                email=user_login.email,
                password=user_login.password,
                device_info=user_login.device_info or "Desktop/Laptop"
            )
            return token, user_model, None
        except ValueError as e:
            return None, None, str(e)
        except Exception as e:
            return None, None, f"Authentication error: {e}"


    @classmethod
    def validate_session(cls, token: str) -> Optional[User]:
        """
        Validates token against active, non-expired sessions.
        Updates last_activity_at and returns authenticated User or None.
        """
        if not token or len(token) < 16:
            return None

        token_hash = hashlib.sha256(token.encode()).hexdigest()
        now = utc_now()

        with get_db() as db:
            session_db = db.query(UserSessionDB).filter(
                UserSessionDB.token_hash == token_hash,
                UserSessionDB.is_active == True,
            ).first()

            if not session_db:
                return None

            # Handle expiry (compare timestamps)
            exp = session_db.expires_at
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)

            if exp < now:
                logger.info("Session %s expired. Invalidating.", session_db.id)
                session_db.is_active = False
                db.commit()
                return None

            # Refresh activity
            session_db.last_activity_at = now
            user_db = db.query(UserDB).filter(UserDB.id == session_db.user_id).first()

            if not user_db or not user_db.is_active:
                return None

            cand_db = db.query(CandidateProfileDB).filter(CandidateProfileDB.user_id == user_db.id).first()
            cand_id = cand_db.id if cand_db else None

            db.commit()

            return User(
                id=user_db.id,
                email=user_db.email,
                full_name=user_db.full_name,
                is_active=user_db.is_active,
                created_at=user_db.created_at,
                last_login_at=user_db.last_login_at,
                candidate_id=cand_id,
            )

    @classmethod
    def logout(cls, token: Optional[str] = None) -> bool:
        """Revokes active session associated with token and clears Streamlit session state."""
        revoked = False
        if token:
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            with get_db() as db:
                session_db = db.query(UserSessionDB).filter(UserSessionDB.token_hash == token_hash).first()
                if session_db:
                    session_db.is_active = False
                    db.commit()
                    logger.info("Session %s logged out.", session_db.id)
                    revoked = True

        try:
            import streamlit as st
            if hasattr(st, "session_state"):
                st.session_state.pop("authenticated_user", None)
                st.session_state.pop("authenticated_candidate_id", None)
                st.session_state.pop("auth_session_token", None)
                st.session_state.pop("careerpilot_initialized", None)
        except Exception:
            pass

        return revoked or token is None

    @classmethod
    def change_password(
        cls,
        user_id: str,
        current_password: str,
        new_password: str,
        revoke_other_sessions: bool = True,
        current_token: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Verifies current password, validates new password complexity,
        updates Argon2id hash, and optionally revokes other active sessions.
        Returns (success: bool, message: str).
        """
        valid_strength, strength_msg = cls.validate_password_strength(new_password)
        if not valid_strength:
            return False, strength_msg

        with get_db() as db:
            user_db = db.query(UserDB).filter(UserDB.id == user_id).first()
            if not user_db:
                return False, "User not found."

            if not cls.verify_password(user_db.password_hash, current_password):
                return False, "Current password is incorrect."

            user_db.password_hash = cls.hash_password(new_password)
            user_db.updated_at = utc_now()

            # Revoke sessions
            current_token_hash = cls._hash_token(current_token) if current_token else None
            sessions = db.query(UserSessionDB).filter(UserSessionDB.user_id == user_id).all()
            for s in sessions:
                if revoke_other_sessions:
                    if current_token_hash and s.token_hash == current_token_hash:
                        continue  # Keep current active session alive
                    s.is_active = False
                elif current_token_hash is None:
                    s.is_active = False

            db.commit()
            logger.info("Password successfully updated for user %s.", user_id)
            return True, "Password updated successfully."


    @classmethod
    def get_candidate_for_user(cls, user_id: str) -> Optional[CandidateProfileDB]:
        """Resolves the candidate profile database record owned by user_id."""
        with get_db() as db:
            return db.query(CandidateProfileDB).filter(CandidateProfileDB.user_id == user_id).first()

    # -------------------------------------------------------------------------
    # Streamlit Authentication Helpers
    # -------------------------------------------------------------------------

    @classmethod
    def require_auth(cls) -> Optional[User]:
        """
        Streamlit Gatekeeper:
        Inspects st.session_state for active user. If not logged in,
        renders an unauthorized barrier with navigation to Login and halts execution.
        """
        try:
            import streamlit as st
        except ImportError:
            return None

        user = st.session_state.get("authenticated_user")
        if user and isinstance(user, User):
            return user

        # Attempt to resume from session token in st.session_state
        token = st.session_state.get("auth_session_token")
        if token:
            user = cls.validate_session(token)
            if user:
                st.session_state["authenticated_user"] = user
                st.session_state["authenticated_candidate_id"] = user.candidate_id
                return user

        # Not authenticated: render clean barrier
        st.warning("🔒 **Authentication Required** — Please sign in to access this page.")
        st.info("You must be logged into your CareerPilot account to view your career data.")
        c1, c2 = st.columns([1, 4])
        with c1:
            if st.button("🔑 Go to Login", type="primary", use_container_width=True):
                st.session_state["redirect_to_login"] = True
                st.rerun()
        st.stop()
        return None
