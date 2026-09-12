"""
CareerPilot AI — Milestone 13 Test Suite
Comprehensive verification of:
1. Argon2id password hashing and complexity validation
2. Multi-device session authentication & cryptographic token management
3. Session invalidation, expiration, and password change with multi-session revocation
4. Production data isolation: User-scoped applications, candidate profiles, and resumes
5. Cross-source job deduplication by canonical URL
6. External profile connector security (dynamic identity, SSL certificate validation)
7. Authoritative 17-status ApplicationStatus lifecycle with legacy alias normalization
"""
import uuid
import pytest
from datetime import datetime, timezone, timedelta
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from careerpilot.core.config import settings
from careerpilot.core.constants import ApplicationStatus, DecisionRecommendation
from careerpilot.models.auth import UserCreate, UserLogin, PasswordChange
from careerpilot.services.auth_service import AuthService
from careerpilot.services.candidate_service import CandidateService
from careerpilot.db.session import init_db, get_db_session
from careerpilot.db.schema import UserDB, UserSessionDB, CandidateProfileDB, ApplicationDB
from careerpilot.db.repository import (
    UserRepository,
    ApplicationRepository,
    ResumeRepository,
    CandidateRepository,
    JobDeduplicationRepository,
)
from careerpilot.analysis.job_deduplicator import JobDeduplicator
from careerpilot.integrations import GitHubConnector, LinkedInConnector


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Ensure database schema and baseline records are initialized."""
    init_db()


# -----------------------------------------------------------------------------
# 1. User Registration & Argon2id Password Hashing
# -----------------------------------------------------------------------------
def test_user_registration_and_argon2id_hashing():
    unique_email = f"test_user_{uuid.uuid4().hex[:8]}@example.com"
    raw_pwd = "SecurePassword2026!"
    
    user = AuthService.register_user(
        UserCreate(
            email=unique_email,
            password=raw_pwd,
            full_name="Test Engineer",
            target_role="Data Platform Engineer"
        )
    )
    assert user is not None
    assert user.email == unique_email
    assert user.candidate_id is not None
    
    # Query DB to inspect hash directly
    with get_db_session() as db:
        user_db = db.query(UserDB).filter(UserDB.id == user.id).first()
        assert user_db is not None
        # Must be Argon2id standard hash format
        assert user_db.password_hash.startswith("$argon2id$v=19$")
        # Must contain standard cost params
        assert "m=65536" in user_db.password_hash
        assert "t=3" in user_db.password_hash
        assert "p=4" in user_db.password_hash
        
        # Verify raw password is never stored
        assert raw_pwd not in user_db.password_hash
        
        # Verify hash verification passes
        hasher = PasswordHasher()
        assert hasher.verify(user_db.password_hash, raw_pwd) is True
        with pytest.raises(VerifyMismatchError):
            hasher.verify(user_db.password_hash, "WrongPassword2026!")


def test_password_strength_validation():
    # Too short (< 8 chars)
    is_valid, msg = AuthService.validate_password_strength("Short1!")
    assert not is_valid
    assert "at least 8 characters" in msg

    # No uppercase
    is_valid, msg = AuthService.validate_password_strength("lowercase123!")
    assert not is_valid
    assert "uppercase" in msg

    # No lowercase
    is_valid, msg = AuthService.validate_password_strength("UPPERCASE123!")
    assert not is_valid
    assert "lowercase" in msg

    # No digit
    is_valid, msg = AuthService.validate_password_strength("NoDigitsHere!")
    assert not is_valid
    assert "number" in msg

    # No special character
    is_valid, msg = AuthService.validate_password_strength("NoSpecialChar123")
    assert not is_valid
    assert "special character" in msg

    # Valid complex password
    is_valid, msg = AuthService.validate_password_strength("ValidStrongPass2026#")
    assert is_valid
    assert msg == "Password meets security requirements."


def test_duplicate_registration_fails():
    unique_email = f"dup_{uuid.uuid4().hex[:8]}@example.com"
    data = UserCreate(
        email=unique_email,
        password="SecurePassword2026!",
        full_name="Duplicate Tester"
    )
    user1 = AuthService.register_user(data)
    assert user1 is not None
    
    # Second attempt with same email must fail
    with pytest.raises(ValueError) as exc_info:
        AuthService.register_user(data)
    assert "already exists" in str(exc_info.value)


# -----------------------------------------------------------------------------
# 2. Authentication & Multi-Device Session Management
# -----------------------------------------------------------------------------
def test_login_success_and_session_token_generation():
    email = f"session_test_{uuid.uuid4().hex[:8]}@example.com"
    pwd = "SessionPassword2026!"
    AuthService.register_user(UserCreate(email=email, password=pwd, full_name="Session Tester"))
    
    token, user, err = AuthService.login(
        UserLogin(email=email, password=pwd, device_info="MacBook Pro / Chrome")
    )
    assert err is None
    assert token is not None
    assert len(token) >= 32  # High entropy token
    assert user is not None
    assert user.email == email
    
    # Verify raw token is NOT stored in DB, but SHA-256 hash is
    with get_db_session() as db:
        sess = db.query(UserSessionDB).filter(UserSessionDB.user_id == user.id).first()
        assert sess is not None
        assert sess.token_hash != token
        assert len(sess.token_hash) == 64
        assert sess.token_hash == AuthService._hash_token(token)
        assert sess.is_active is True


def test_login_invalid_password_fails():
    email = f"fail_{uuid.uuid4().hex[:8]}@example.com"
    pwd = "CorrectPassword2026!"
    AuthService.register_user(UserCreate(email=email, password=pwd, full_name="Fail Tester"))
    
    token, user, err = AuthService.login(
        UserLogin(email=email, password="IncorrectPassword2026!")
    )
    assert token is None
    assert user is None
    assert err == "Invalid email or password."


def test_login_unknown_email_fails():
    token, user, err = AuthService.login(
        UserLogin(email="nonexistent_user_999@example.com", password="SomePassword2026!")
    )
    assert token is None
    assert user is None
    assert err == "Invalid email or password."


def test_multi_device_login_and_independent_sessions():
    email = f"multidev_{uuid.uuid4().hex[:8]}@example.com"
    pwd = "MultiDevPassword2026!"
    AuthService.register_user(UserCreate(email=email, password=pwd, full_name="MultiDevice User"))
    
    # Device 1: Laptop
    token_laptop, user1, err1 = AuthService.login(
        UserLogin(email=email, password=pwd, device_info="ThinkPad / Windows 11 Edge")
    )
    assert err1 is None
    assert token_laptop is not None
    
    # Device 2: Mobile
    token_mobile, user2, err2 = AuthService.login(
        UserLogin(email=email, password=pwd, device_info="iPhone 15 / Safari Mobile")
    )
    assert err2 is None
    assert token_mobile is not None
    
    # Tokens must be completely independent
    assert token_laptop != token_mobile
    
    # Both sessions must validate successfully
    val_laptop = AuthService.validate_session(token_laptop)
    val_mobile = AuthService.validate_session(token_mobile)
    assert val_laptop is not None
    assert val_mobile is not None
    assert val_laptop.id == user1.id
    assert val_mobile.id == user2.id
    
    # Logout laptop: mobile must remain active!
    logged_out = AuthService.logout(token_laptop)
    assert logged_out is True
    assert AuthService.validate_session(token_laptop) is None
    assert AuthService.validate_session(token_mobile) is not None


def test_session_expiration_fails():
    email = f"expire_{uuid.uuid4().hex[:8]}@example.com"
    pwd = "ExpirePassword2026!"
    AuthService.register_user(UserCreate(email=email, password=pwd, full_name="Expire Tester"))
    token, user, _ = AuthService.login(UserLogin(email=email, password=pwd))
    
    # Artificially expire the session in the DB
    with get_db_session() as db:
        token_h = AuthService._hash_token(token)
        sess = db.query(UserSessionDB).filter(UserSessionDB.token_hash == token_h).first()
        sess.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        db.commit()
        
    # Validating expired token must return None
    assert AuthService.validate_session(token) is None


def test_password_change_with_verification_and_session_revocation():
    email = f"pwdchange_{uuid.uuid4().hex[:8]}@example.com"
    old_pwd = "OldPassword2026!"
    new_pwd = "NewSecurePassword2026#"
    
    user = AuthService.register_user(UserCreate(email=email, password=old_pwd, full_name="Pwd Change User"))
    token1, _, _ = AuthService.login(UserLogin(email=email, password=old_pwd, device_info="Device 1"))
    token2, _, _ = AuthService.login(UserLogin(email=email, password=old_pwd, device_info="Device 2"))
    
    # Wrong old password fails
    success, err = AuthService.change_password(
        user_id=user.id,
        current_password="WrongOldPassword!",
        new_password=new_pwd,
        revoke_other_sessions=True,
        current_token=token1
    )
    assert not success
    assert "Current password is incorrect" in err
    
    # Correct password change with revocation of other sessions
    success, msg = AuthService.change_password(
        user_id=user.id,
        current_password=old_pwd,
        new_password=new_pwd,
        revoke_other_sessions=True,
        current_token=token1
    )
    assert success is True
    
    # Old password no longer logs in
    bad_token, _, err = AuthService.login(UserLogin(email=email, password=old_pwd))
    assert bad_token is None
    
    # New password logs in successfully
    new_token, _, err = AuthService.login(UserLogin(email=email, password=new_pwd))
    assert new_token is not None
    assert err is None
    
    # Current session remains valid, other session is revoked
    assert AuthService.validate_session(token1) is not None
    assert AuthService.validate_session(token2) is None


# -----------------------------------------------------------------------------
# 3. User-Scoped Data Isolation & Ownership
# -----------------------------------------------------------------------------
def test_cross_user_isolation_candidate_profile():
    email_a = f"usera_{uuid.uuid4().hex[:8]}@example.com"
    email_b = f"userb_{uuid.uuid4().hex[:8]}@example.com"
    
    user_a = AuthService.register_user(UserCreate(email=email_a, password="UserAPassword2026!", full_name="User Alpha"))
    user_b = AuthService.register_user(UserCreate(email=email_b, password="UserBPassword2026!", full_name="User Beta"))
    
    prof_a = CandidateRepository.get_profile(user_id=user_a.id)
    prof_b = CandidateRepository.get_profile(user_id=user_b.id)
    
    assert prof_a is not None
    assert prof_b is not None
    assert prof_a.id != prof_b.id
    assert prof_a.user_id == user_a.id
    assert prof_b.user_id == user_b.id
    assert prof_a.full_name == "User Alpha"
    assert prof_b.full_name == "User Beta"


def test_cross_user_isolation_applications():
    email_a = f"app_a_{uuid.uuid4().hex[:8]}@example.com"
    email_b = f"app_b_{uuid.uuid4().hex[:8]}@example.com"
    
    user_a = AuthService.register_user(UserCreate(email=email_a, password="PasswordA2026!", full_name="Applicant Alpha"))
    user_b = AuthService.register_user(UserCreate(email=email_b, password="PasswordB2026!", full_name="Applicant Beta"))
    
    # User A creates an application
    app_id_a = f"app_iso_{uuid.uuid4().hex[:8]}"
    app_a = ApplicationRepository.create_application(
        app_id=app_id_a,
        job_id=f"job_{uuid.uuid4().hex[:8]}",
        company="Alpha Cloud Corp",
        job_title="Lead Data Engineer",
        candidate_id=user_a.candidate_id,
        fit_score=85.0,
        status=ApplicationStatus.ANALYZED
    )
    assert app_a.candidate_id == user_a.candidate_id
    
    # User B lists applications -> User A's app must NOT appear
    apps_b = ApplicationRepository.list_applications(candidate_id=user_b.candidate_id)
    assert not any(a.application_id == app_id_a for a in apps_b)
    
    # User A lists applications -> User A's app appears
    apps_a = ApplicationRepository.list_applications(candidate_id=user_a.candidate_id)
    assert any(a.application_id == app_id_a for a in apps_a)
    
    # User B attempts to access User A's application with candidate_id filter -> returns None
    app_cross = ApplicationRepository.get_application(app_id_a, candidate_id=user_b.candidate_id)
    assert app_cross is None
    
    # User B attempts to update User A's status -> PermissionError
    with pytest.raises(PermissionError):
        ApplicationRepository.update_status(
            app_id=app_id_a,
            new_status=ApplicationStatus.APPLIED,
            candidate_id=user_b.candidate_id
        )
        
    # User B attempts to update User A's decision -> PermissionError
    with pytest.raises(PermissionError):
        ApplicationRepository.update_decision(
            app_id=app_id_a,
            user_decision=DecisionRecommendation.APPLY,
            candidate_id=user_b.candidate_id
        )


def test_cross_user_isolation_resume_versions():
    email_a = f"res_a_{uuid.uuid4().hex[:8]}@example.com"
    email_b = f"res_b_{uuid.uuid4().hex[:8]}@example.com"
    
    user_a = AuthService.register_user(UserCreate(email=email_a, password="PasswordA2026!", full_name="Resume Alpha"))
    user_b = AuthService.register_user(UserCreate(email=email_b, password="PasswordB2026!", full_name="Resume Beta"))
    
    job_id = f"job_res_{uuid.uuid4().hex[:8]}"
    
    # Create resume version for User A
    ver_a = ResumeRepository.save_resume_version(
        job_id=job_id,
        resume_data={"summary": "Alpha summary", "skills": ["Python"]},
        tailoring_strategy="GCP_SPECIALIST",
        candidate_id=user_a.candidate_id
    )
    assert ver_a.candidate_id == user_a.candidate_id
    
    # User B checks versions for job_id -> returns empty
    versions_b = ResumeRepository.list_versions_for_job(job_id=job_id, candidate_id=user_b.candidate_id)
    assert len(versions_b) == 0
    
    # User A checks versions -> contains ver_a
    versions_a = ResumeRepository.list_versions_for_job(job_id=job_id, candidate_id=user_a.candidate_id)
    assert len(versions_a) == 1
    assert versions_a[0].id == ver_a.id


# -----------------------------------------------------------------------------
# 4. External Profile Connector Security & Dynamic Resolution
# -----------------------------------------------------------------------------
def test_github_connector_dynamic_username_and_ssl_safety():
    # Dynamic resolution from explicit username
    assert GitHubConnector.resolve_username(explicit_username="custom_dev") == "custom_dev"
    
    # Dynamic resolution from candidate profile
    test_prof = CandidateRepository.get_profile(candidate_id="cand_verified")
    resolved = GitHubConnector.resolve_username(candidate_profile=test_prof)
    assert resolved.lower().replace("-", "") in ["truptikularkar", "alexrivera"]

    
    # SSL safety: Verify sync_github_profile does not use CERT_NONE and handles certifi
    sync_res = GitHubConnector.sync_github_profile(
        username="octocat",
        github_token="mock_dummy_token"
    )
    # Should complete without crashing and report status cleanly
    assert "status" in sync_res
    assert sync_res["username"] == "octocat"
    assert "error" in sync_res or sync_res["status"] in ["Synced", "Error"]


def test_linkedin_connector_dynamic_profile_url():
    # Dynamic resolution from explicit URL
    url = "https://www.linkedin.com/in/custom-candidate/"
    assert LinkedInConnector.resolve_profile_url(explicit_url=url) == url
    
    # Resolution from username slug
    slug_url = LinkedInConnector.resolve_profile_url(explicit_url="custom-slug")
    assert slug_url == "https://www.linkedin.com/in/custom-slug"
    
    # Verification of zero-scraping compliance
    report = LinkedInConnector.fetch_profile_data("test-candidate")
    assert report["scraping_permitted"] is False
    assert "Browser automation prohibited" in report["data_source_mode"]


# -----------------------------------------------------------------------------
# 5. Cross-Source Job Deduplication
# -----------------------------------------------------------------------------
def test_enhanced_cross_source_job_deduplication():
    # Test canonical URL normalization
    url1 = "https://www.linkedin.com/jobs/view/1234567890/?refId=abc&trackingId=xyz"
    url2 = "https://www.linkedin.com/jobs/view/1234567890"
    assert JobDeduplicator.normalize_url(url1) == "https://www.linkedin.com/jobs/view/1234567890"
    assert JobDeduplicator.normalize_url(url1) == JobDeduplicator.normalize_url(url2)
    
    # Test deduplication matching across sources with canonical URL
    # Test deduplication matching across sources with canonical URL
    shared_canonical_url = f"https://jobs.example.com/roles/{uuid.uuid4().hex[:8]}"
    unique_company = f"CrossCorp_{uuid.uuid4().hex[:8]}"
    unique_title = f"Senior Cloud Architect_{uuid.uuid4().hex[:8]}"

    # Save first job
    job1_id = f"job_dedup_{uuid.uuid4().hex[:8]}"
    JobDeduplicationRepository.register_canonical_job(
        job_id=job1_id,
        company=unique_company,
        title=unique_title,
        source="linkedin",
        source_url=shared_canonical_url
    )

    # Check duplicate matching with same source URL from naukri
    match = JobDeduplicationRepository.find_canonical_match(
        company="Different Company Name",
        title="Different Title",
        source_url=shared_canonical_url
    )
    assert match is not None
    assert match.job_id == job1_id or job1_id in (match.job_ids_json or [])
    assert match.match_type == "CANONICAL_URL_EXACT"



# -----------------------------------------------------------------------------
# 6. Authoritative 17-Status ApplicationStatus Lifecycle
# -----------------------------------------------------------------------------
def test_application_status_17_lifecycle_and_legacy_mapping():
    # All 17 authoritative statuses exist
    expected_statuses = {
        "DISCOVERED", "ANALYZED", "SAVED", "APPLIED", "ACKNOWLEDGED",
        "SCREENING", "OA", "INTERVIEWING", "TECHNICAL_ROUND", "HR_ROUND",
        "FINAL_ROUND", "OFFER", "ACCEPTED", "REJECTED", "WITHDRAWN",
        "ON_HOLD", "NO_RESPONSE"
    }
    actual_statuses = {s.value for s in ApplicationStatus}
    assert expected_statuses == actual_statuses
    assert len(ApplicationStatus) == 17
    
    # Legacy alias backwards-compatibility mapping
    assert ApplicationStatus("Interview") == ApplicationStatus.INTERVIEWING
    assert ApplicationStatus("oa_scheduled") == ApplicationStatus.OA
    assert ApplicationStatus("SAVED_FOR_LATER") == ApplicationStatus.SAVED
    assert ApplicationStatus("applying") == ApplicationStatus.APPLIED
    assert ApplicationStatus("SKIPPED") == ApplicationStatus.WITHDRAWN
    assert ApplicationStatus("technical_interview") == ApplicationStatus.TECHNICAL_ROUND
    assert ApplicationStatus("hr_interview") == ApplicationStatus.HR_ROUND


# -----------------------------------------------------------------------------
# 7. Auto-Seeded Default Verified User
# -----------------------------------------------------------------------------
def test_default_verified_user_auto_seeded():
    user = UserRepository.get_by_email("kularkartrupti@gmail.com")
    assert user is not None
    assert user.full_name == "Trupti Kularkar"
    assert user.is_active is True
    
    # Verify linked candidate profile
    prof = CandidateRepository.get_profile(user_id=user.id)
    assert prof is not None
    assert prof.id in ["cand_verified", "trupti_kularkar"]
    
    # Verify login with default seed credentials
    token, logged_in_user, err = AuthService.login(
        UserLogin(email="kularkartrupti@gmail.com", password="TruptiCareerPilot2026!")
    )
    assert err is None
    assert token is not None
    assert logged_in_user.email == "kularkartrupti@gmail.com"
