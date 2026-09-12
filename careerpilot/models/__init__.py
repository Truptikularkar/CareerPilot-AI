"""
Pydantic Domain Models for CareerPilot AI
"""
from careerpilot.models.evidence import CandidateEvidence, VerificationResult
from careerpilot.models.candidate import (
    Skill,
    Experience,
    Project,
    Education,
    Achievement,
    CareerPreference,
    CandidateProfile,
    ProfileDiffItem,
    ProfileDiffResult,
    ProfileVersion,
    ProfileHealthSummary,
)

from careerpilot.models.job import (
    JobRequirement,
    JobDescription,
    JobAnalysis,
    MatchScore,
    SkillGap,
)
from careerpilot.models.resume import (
    ResumeStrategy,
    TailoredSection,
    TailoredResume,
    ATSReport,
)
from careerpilot.models.artifact import (
    ResumeArtifact,
    ResumeArtifactBundle,
)

from careerpilot.models.interview import (
    InterviewQuestion,
    InterviewAnswer,
    PrepRoadmap,
    MockTurn,
    MockSession,
    ReadinessScore,
)

from careerpilot.models.mock_interview import (
    TruthAuditItem,
    AnswerEvaluation,
    MockInterviewTurn,
    TopicMastery,
    WeaknessItem,
    StrengthItem,
    JDCoverageItem,
    FinalInterviewReport,
)

from careerpilot.models.application import (
    Application,
    ApplicationCreate,
    ApplicationUpdate,
    ResumeVersionRecord,
    ApplicationFilter,
    DashboardMetrics,
    SkillGapItem,
    SkillGapSummary,
)

__all__ = [
    "CandidateEvidence",
    "VerificationResult",
    "Skill",
    "Experience",
    "Project",
    "Education",
    "CareerPreference",
    "CandidateProfile",
    "JobRequirement",
    "JobDescription",
    "JobAnalysis",
    "MatchScore",
    "SkillGap",
    "ResumeStrategy",
    "TailoredSection",
    "TailoredResume",
    "ATSReport",
    "InterviewQuestion",
    "InterviewAnswer",
    "PrepRoadmap",
    "MockTurn",
    "MockSession",
    "ReadinessScore",
    "TruthAuditItem",
    "AnswerEvaluation",
    "MockInterviewTurn",
    "TopicMastery",
    "WeaknessItem",
    "StrengthItem",
    "JDCoverageItem",
    "FinalInterviewReport",
    "Application",
    "ApplicationCreate",
    "ApplicationUpdate",
    "ResumeVersionRecord",
    "ApplicationFilter",
    "DashboardMetrics",
    "SkillGapItem",
    "SkillGapSummary",
]


