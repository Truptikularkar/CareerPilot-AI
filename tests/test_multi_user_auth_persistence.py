import uuid
import pytest
import streamlit as st

from careerpilot.services.auth_service import AuthService
from careerpilot.db.repository import CandidateRepository, ApplicationRepository, JobRepository
from careerpilot.db.schema import UserDB, CandidateProfileDB
from careerpilot.db.session import get_db_session
from careerpilot.models.candidate import Skill
from careerpilot.models.job import JobDescription
from careerpilot.core.constants import SkillCategory, ApplicationStatus, DecisionRecommendation


@pytest.fixture(autouse=True)
def clean_streamlit_session():
    """Clear Streamlit session state before and after each test."""
    if hasattr(st, "session_state"):
        try:
            st.session_state.clear()
        except Exception:
            pass
    yield
    if hasattr(st, "session_state"):
        try:
            st.session_state.clear()
        except Exception:
            pass


def test_user_registration_creates_isolated_profile():
    """Verify that registering a new user creates a dedicated UserDB and CandidateProfileDB."""
    unique_email = f"candidate_{uuid.uuid4().hex[:8]}@example.com"
    raw_pwd = "StrongPassword123!"
    full_name = "Jane Developer"

    # Register user
    user = AuthService.register_user(
        email=unique_email,
        password=raw_pwd,
        full_name=full_name,
    )

    assert user is not None
    assert user.email == unique_email
    assert user.full_name == full_name
    assert user.id.startswith("usr_")
    assert user.candidate_id is not None
    assert user.candidate_id.startswith("cand_")

    # Verify UserDB and CandidateProfileDB in database
    with get_db_session() as db:
        user_row = db.query(UserDB).filter(UserDB.id == user.id).first()
        assert user_row is not None
        assert user_row.email == unique_email
        assert user_row.password_hash != raw_pwd  # Must be hashed with Argon2id!
        assert AuthService.verify_password(user_row.password_hash, raw_pwd)

        cand_row = db.query(CandidateProfileDB).filter(CandidateProfileDB.user_id == user.id).first()
        assert cand_row is not None
        assert cand_row.full_name == full_name
        assert cand_row.email == unique_email
        assert cand_row.id == user.candidate_id

    # Verify baseline demo profile still exists and was not altered
    demo_profile = CandidateRepository.get_profile("trupti_kularkar")
    assert demo_profile is not None
    assert "Trupti" in demo_profile.full_name


def test_registration_duplicate_email_rejected():
    """Verify that registering an email that already exists raises a ValueError."""
    unique_email = f"dup_{uuid.uuid4().hex[:8]}@example.com"
    AuthService.register_user(email=unique_email, password="Password123!", full_name="First User")

    with pytest.raises(ValueError, match="already registered"):
        AuthService.register_user(email=unique_email, password="DifferentPassword456!", full_name="Second User")

    # Case-insensitive check
    with pytest.raises(ValueError, match="already registered"):
        AuthService.register_user(email=unique_email.upper(), password="DifferentPassword456!", full_name="Upper User")


def test_registration_password_length_validation():
    """Verify that passwords shorter than 8 characters are rejected."""
    with pytest.raises(ValueError, match="at least 8 characters"):
        AuthService.register_user(email="short@example.com", password="short", full_name="Short Pwd")


def test_authentication_with_password_verification():
    """Verify Argon2id password verification during authentication."""
    unique_email = f"auth_{uuid.uuid4().hex[:8]}@example.com"
    raw_pwd = "CorrectPassword789!"
    full_name = "Auth User"

    user = AuthService.register_user(email=unique_email, password=raw_pwd, full_name=full_name)

    # Wrong password raises ValueError
    with pytest.raises(ValueError, match="Invalid email or password"):
        AuthService.authenticate(unique_email, "WrongPassword123!")

    # Non-existent user raises ValueError
    with pytest.raises(ValueError, match="Invalid email or password"):
        AuthService.authenticate("nonexistent@example.com", raw_pwd)

    # Correct password succeeds
    auth_user, token = AuthService.authenticate(unique_email, raw_pwd)
    assert auth_user is not None
    assert auth_user.id == user.id
    assert len(token) > 20
    assert st.session_state.get("authenticated_user") is not None
    assert st.session_state.get("authenticated_candidate_id") == user.candidate_id


def test_profile_persistence_and_isolation():
    """Verify that modifying and saving profile for User A never impacts User B or demo profile."""
    # 1. Register User A
    user_a = AuthService.register_user(
        email=f"user_a_{uuid.uuid4().hex[:8]}@example.com",
        password="Password12345!",
        full_name="User Alpha",
    )
    cand_id_a = user_a.candidate_id

    # 2. Register User B
    user_b = AuthService.register_user(
        email=f"user_b_{uuid.uuid4().hex[:8]}@example.com",
        password="Password12345!",
        full_name="User Beta",
    )
    cand_id_b = user_b.candidate_id

    # 3. Retrieve User A's profile and add a unique skill
    prof_a = CandidateRepository.get_profile(candidate_id=cand_id_a)
    assert prof_a.full_name == "User Alpha"
    prof_a.skills.append(
        Skill(
            name="SuperCustomSkill_Alpha",
            category=SkillCategory.DATA_ENGINEERING,
            verified=True,
            experience_years=5,
        )
    )
    CandidateRepository.save_profile(prof_a, candidate_id=cand_id_a)

    # 4. Fetch User B's profile and verify it does NOT contain User A's skill
    prof_b = CandidateRepository.get_profile(candidate_id=cand_id_b)
    assert prof_b.full_name == "User Beta"
    assert not any(s.name == "SuperCustomSkill_Alpha" for s in prof_b.skills)

    # 5. Fetch demo profile and verify it does NOT contain User A's skill
    prof_demo = CandidateRepository.get_profile(candidate_id="trupti_kularkar")
    assert not any(s.name == "SuperCustomSkill_Alpha" for s in prof_demo.skills)


def test_demo_user_1_click_login():
    """Verify that 1-click sample profile exploration logs in the demo user."""
    demo_user, token = AuthService.login_demo_user()
    assert demo_user is not None
    assert len(token) > 20
    assert st.session_state.get("authenticated_user") is not None
    assert st.session_state.get("authenticated_candidate_id") is not None
    cand_id = st.session_state["authenticated_candidate_id"]

    # Profile retrieved matches sample candidate
    prof = CandidateRepository.get_profile(cand_id)
    assert prof is not None
    assert "Trupti" in prof.full_name


def test_logout_clears_authenticated_state():
    """Verify logout removes all user credentials and candidate identifiers from session."""
    user, token = AuthService.login_demo_user()
    assert "authenticated_user" in st.session_state
    assert "authenticated_candidate_id" in st.session_state

    AuthService.logout(token)
    assert "authenticated_user" not in st.session_state
    assert "authenticated_candidate_id" not in st.session_state


def test_application_isolation_by_candidate():
    """Verify applications created by Candidate A are not visible when querying for Candidate B."""
    # Register Candidate A and Candidate B so they have valid DB profiles
    user_a = AuthService.register_user(
        email=f"app_iso_a_{uuid.uuid4().hex[:8]}@example.com",
        password="Password123!",
        full_name="App Tester A",
    )
    user_b = AuthService.register_user(
        email=f"app_iso_b_{uuid.uuid4().hex[:8]}@example.com",
        password="Password123!",
        full_name="App Tester B",
    )

    cand_a = user_a.candidate_id
    cand_b = user_b.candidate_id
    job_id = f"job_iso_{uuid.uuid4().hex[:6]}"

    # Save a job
    jd = JobDescription(
        id=job_id,
        company_name="Isolation Corp",
        job_title="Security Engineer",
        raw_text="Job description for isolation testing.",
    )
    JobRepository.save_job_description(jd)

    # Candidate A creates an application
    app_a = ApplicationRepository.create_application(
        app_id=f"app_{uuid.uuid4().hex[:6]}",
        job_id=job_id,
        company="Isolation Corp",
        job_title="Security Engineer",
        candidate_id=cand_a,
    )

    # Candidate B queries applications -> must NOT see Candidate A's application
    apps_for_b = ApplicationRepository.list_applications(candidate_id=cand_b)
    assert not any(a.application_id == app_a.application_id for a in apps_for_b)

    # Candidate A queries applications -> must see Candidate A's application
    apps_for_a = ApplicationRepository.list_applications(candidate_id=cand_a)
    assert any(a.application_id == app_a.application_id for a in apps_for_a)
