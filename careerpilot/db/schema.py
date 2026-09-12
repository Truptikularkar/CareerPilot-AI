from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Boolean, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def utc_now():
    return datetime.now(timezone.utc)


class UserDB(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
    last_login_at = Column(DateTime, nullable=True)

    candidate_profile = relationship("CandidateProfileDB", back_populates="user", uselist=False)
    sessions = relationship("UserSessionDB", back_populates="user", cascade="all, delete-orphan")


class UserSessionDB(Base):
    __tablename__ = "user_sessions"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String, unique=True, nullable=False, index=True)
    device_info = Column(String, default="Desktop/Laptop")
    ip_address = Column(String, nullable=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)
    last_activity_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("UserDB", back_populates="sessions")


class CandidateProfileDB(Base):
    __tablename__ = "candidate_profiles"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True, unique=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    linkedin_url = Column(String, nullable=True)
    github_url = Column(String, nullable=True)
    professional_summary = Column(Text, nullable=False)
    skills_json = Column(JSON, default=list)
    experiences_json = Column(JSON, default=list)
    projects_json = Column(JSON, default=list)
    education_json = Column(JSON, default=list)
    certifications_json = Column(JSON, default=list)
    achievements_json = Column(JSON, default=list)
    preferences_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("UserDB", back_populates="candidate_profile")
    evidences = relationship("CandidateEvidenceDB", back_populates="candidate", cascade="all, delete-orphan")
    profile_versions = relationship("ProfileVersionDB", back_populates="candidate", cascade="all, delete-orphan")
    applications = relationship("ApplicationDB", back_populates="candidate")



class CandidateEvidenceDB(Base):
    __tablename__ = "candidate_evidences"

    id = Column(String, primary_key=True)
    fact_id = Column(String, nullable=True)
    candidate_id = Column(String, ForeignKey("candidate_profiles.id"), nullable=False)
    source_type = Column(String, default="PROFESSIONAL_EXPERIENCE")
    source_id = Column(String, nullable=True)
    source_document = Column(String, default="SQLite Candidate Profile")
    section = Column(String, default="Experience")
    evidence_type = Column(String, nullable=False)
    source_section = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    skill_tags_json = Column(JSON, default=list)
    technologies_json = Column(JSON, default=list)
    metrics_json = Column(JSON, default=list)
    confidence = Column(Float, default=1.0)
    status = Column(String, default="SUPPORTED")
    extra_metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    candidate = relationship("CandidateProfileDB", back_populates="evidences")



class JobDescriptionDB(Base):
    __tablename__ = "job_descriptions"

    id = Column(String, primary_key=True)
    company_name = Column(String, nullable=True)
    job_title = Column(String, nullable=True)
    location = Column(String, nullable=True)
    work_mode = Column(String, nullable=True)
    extracted_role = Column(String, default="Other")
    estimated_seniority = Column(String, default="Mid-Level")
    raw_text = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    responsibilities_json = Column(JSON, default=list)
    must_have_skills_json = Column(JSON, default=list)
    nice_to_have_skills_json = Column(JSON, default=list)
    tech_stack_json = Column(JSON, default=list)
    requirements_json = Column(JSON, default=list)
    created_at = Column(DateTime, default=utc_now)

    analyses = relationship("JobAnalysisDB", back_populates="job", cascade="all, delete-orphan")
    applications = relationship("ApplicationDB", back_populates="job")


class JobAnalysisDB(Base):
    __tablename__ = "job_analyses"

    id = Column(String, primary_key=True)
    job_id = Column(String, ForeignKey("job_descriptions.id"), nullable=False)
    candidate_id = Column(String, nullable=False)
    overall_fit_score = Column(Float, nullable=False)
    scores_json = Column(JSON, default=dict)
    matched_skills_json = Column(JSON, default=list)
    missing_skills_json = Column(JSON, default=list)
    key_strengths_json = Column(JSON, default=list)
    risk_factors_json = Column(JSON, default=list)
    recommendation = Column(String, default="PREPARE")
    explainable_reasoning = Column(Text, nullable=False)
    suggested_resume_strategy = Column(String, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    job = relationship("JobDescriptionDB", back_populates="analyses")


class ApplicationDB(Base):
    __tablename__ = "applications"

    id = Column(String, primary_key=True)
    canonical_job_id = Column(String, nullable=True, index=True)
    candidate_id = Column(String, ForeignKey("candidate_profiles.id"), nullable=False, default="trupti_kularkar")
    job_id = Column(String, ForeignKey("job_descriptions.id"), nullable=False)
    company_name = Column(String, nullable=False)
    role_title = Column(String, nullable=False)
    source = Column(String, default="DIRECT")  # DIRECT, LINKEDIN, NAUKRI, GITHUB, REFERRAL, COMPANY_WEBSITE
    job_location = Column(String, default="Remote / Flexible")
    job_url = Column(String, nullable=True)
    job_description_text = Column(Text, nullable=True)
    job_analysis_id = Column(String, nullable=True)
    system_recommendation = Column(String, default="REVIEW")
    user_decision = Column(String, default="REVIEW")
    fit_score = Column(Float, default=0.0)
    selected_strategy = Column(String, nullable=True)
    resume_id = Column(String, nullable=True)
    resume_version = Column(String, nullable=True)
    ats_score = Column(Float, nullable=True)
    interview_prep_id = Column(String, nullable=True)
    status = Column(String, default="SAVED")
    interview_status = Column(String, default="Not Started")
    recruiter = Column(String, nullable=True)
    final_outcome = Column(String, nullable=True)
    notes_json = Column(JSON, default=list)
    resume_versions_json = Column(JSON, default=list)
    status_history_json = Column(JSON, default=list)
    applied_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    candidate = relationship("CandidateProfileDB", back_populates="applications")
    job = relationship("JobDescriptionDB", back_populates="applications")


class CanonicalJobDB(Base):
    __tablename__ = "canonical_jobs"

    id = Column(String, primary_key=True)
    company_name = Column(String, nullable=False)
    company_normalized = Column(String, nullable=False, index=True)
    job_title = Column(String, nullable=False)
    title_normalized = Column(String, nullable=False, index=True)
    location = Column(String, nullable=True)
    location_normalized = Column(String, nullable=True)
    text_hash = Column(String, nullable=False, index=True)
    source_urls_json = Column(JSON, default=list)
    job_ids_json = Column(JSON, default=list)  # mapped JobDescriptionDB IDs
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)


class ExternalProfileDB(Base):
    __tablename__ = "external_profiles"

    id = Column(String, primary_key=True)
    candidate_id = Column(String, nullable=False, default="trupti_kularkar")
    platform = Column(String, nullable=False)  # GITHUB, LINKEDIN, NAUKRI
    profile_url = Column(String, nullable=True)
    username = Column(String, nullable=True)
    is_connected = Column(Boolean, default=False)
    sync_status = Column(String, default="NOT_SYNCED")  # NOT_SYNCED, SYNCED, ERROR
    last_synced_at = Column(DateTime, nullable=True)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)




class ResumeVersionDB(Base):
    __tablename__ = "resume_versions"

    id = Column(String, primary_key=True)
    job_id = Column(String, nullable=False)
    candidate_id = Column(String, nullable=False, default="trupti_kularkar")
    strategy_type = Column(String, nullable=False)
    version_tag = Column(String, default="v1.0")
    tailored_resume_json = Column(JSON, nullable=False)
    ats_score = Column(Float, default=0.0)
    ats_report_json = Column(JSON, default=dict)
    truth_audit_json = Column(JSON, default=list)
    docx_file_path = Column(String, nullable=True)
    pdf_file_path = Column(String, nullable=True)
    markdown_file_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=utc_now)



class InterviewPrepDB(Base):
    __tablename__ = "interview_preparations"

    id = Column(String, primary_key=True)
    job_id = Column(String, nullable=False)
    candidate_id = Column(String, nullable=False, default="trupti_kularkar")
    target_role = Column(String, nullable=False)
    readiness_score = Column(Float, default=0.0)
    seed_json = Column(JSON, default=dict)
    plan_json = Column(JSON, default=dict)
    roadmap_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utc_now)


class InterviewQuestionDB(Base):
    __tablename__ = "interview_questions"

    id = Column(String, primary_key=True)
    job_id = Column(String, nullable=True)
    category = Column(String, nullable=False)
    difficulty = Column(String, nullable=False)
    target_technology_or_skill = Column(String, nullable=False)
    question_text = Column(Text, nullable=False)
    why_this_matters = Column(Text, nullable=True)
    expected_answer_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=utc_now)


class MockSessionDB(Base):
    __tablename__ = "mock_sessions"

    id = Column(String, primary_key=True)
    job_id = Column(String, nullable=False)
    candidate_id = Column(String, nullable=False, default="trupti_kularkar")
    target_role = Column(String, nullable=False)
    current_difficulty = Column(String, default="Intermediate")
    turns_json = Column(JSON, default=list)
    readiness_json = Column(JSON, default=dict)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)


class SkillGapDB(Base):
    __tablename__ = "skill_gaps"

    id = Column(String, primary_key=True)
    candidate_id = Column(String, nullable=False, default="trupti_kularkar")
    skill_name = Column(String, nullable=False)
    target_role = Column(String, nullable=True)
    frequency_count = Column(Float, default=1.0)
    importance = Column(String, default="High")
    explanation = Column(Text, nullable=True)
    learning_action = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)


class ProfileVersionDB(Base):
    __tablename__ = "profile_versions"

    id = Column(String, primary_key=True)
    candidate_id = Column(String, ForeignKey("candidate_profiles.id"), nullable=False, default="trupti_kularkar")
    version_tag = Column(String, nullable=False, default="v1.0")
    profile_json = Column(JSON, nullable=False)
    change_summary = Column(Text, nullable=False)
    changed_sections_json = Column(JSON, default=list)
    created_at = Column(DateTime, default=utc_now)

    candidate = relationship("CandidateProfileDB", back_populates="profile_versions")



