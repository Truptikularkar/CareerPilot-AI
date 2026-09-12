"""
CareerPilot AI Database Package
"""
from careerpilot.db.session import engine, SessionLocal, get_db, init_db
from careerpilot.db.schema import (
    Base,
    CandidateProfileDB,
    CandidateEvidenceDB,
    JobDescriptionDB,
    JobAnalysisDB,
    ApplicationDB,
    ResumeVersionDB,
    InterviewQuestionDB,
    MockSessionDB,
    SkillGapDB,
)

__all__ = [
    "engine",
    "SessionLocal",
    "get_db",
    "init_db",
    "Base",
    "CandidateProfileDB",
    "CandidateEvidenceDB",
    "JobDescriptionDB",
    "JobAnalysisDB",
    "ApplicationDB",
    "ResumeVersionDB",
    "InterviewQuestionDB",
    "MockSessionDB",
    "SkillGapDB",
]

# Ensure DB schema is initialized
init_db()

