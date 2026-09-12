from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid
from careerpilot.core.constants import (
    ApplicationStatus,
    DecisionRecommendation,
    RoleCategory,
    SeniorityLevel,
)


def utc_iso():
    return datetime.now(timezone.utc).isoformat()


class ResumeVersionRecord(BaseModel):
    """Historical snapshot of a tailored resume generated for an application."""
    resume_id: str
    version_tag: str = "v1.0"
    strategy_type: str = "AUTO"
    ats_score: Optional[float] = None
    docx_file_path: Optional[str] = None
    pdf_file_path: Optional[str] = None
    markdown_file_path: Optional[str] = None
    created_at: str = Field(default_factory=utc_iso)



class StatusHistoryItem(BaseModel):
    """Entry in an application's status transition log."""
    from_status: str
    to_status: str
    timestamp: str = Field(default_factory=utc_iso)
    note: Optional[str] = None


class Application(BaseModel):
    """Complete persistent entity for a candidate job application and workflow state."""
    application_id: str = Field(default_factory=lambda: f"app_{uuid.uuid4().hex[:8]}")
    candidate_id: Optional[str] = None
    canonical_job_id: Optional[str] = None
    company: str

    job_title: str
    source: str = "DIRECT"  # DIRECT, LINKEDIN, NAUKRI, GITHUB, REFERRAL, COMPANY_WEBSITE
    job_location: Optional[str] = "Remote / Flexible"
    job_url: Optional[str] = None
    job_description: Optional[str] = ""
    job_id: str
    job_analysis_id: Optional[str] = None
    system_recommendation: DecisionRecommendation = DecisionRecommendation.REVIEW
    user_decision: DecisionRecommendation = DecisionRecommendation.REVIEW
    fit_score: float = 0.0
    selected_strategy: Optional[str] = None
    resume_id: Optional[str] = None
    resume_version: Optional[str] = None
    ats_score: Optional[float] = None
    interview_prep_id: Optional[str] = None
    application_status: ApplicationStatus = ApplicationStatus.SAVED
    date_added: str = Field(default_factory=utc_iso)
    applied_date: Optional[str] = None
    date_applied: Optional[str] = None
    last_updated: str = Field(default_factory=utc_iso)
    interview_status: Optional[str] = "Not Started"
    recruiter: Optional[str] = None
    final_outcome: Optional[str] = None
    notes: List[str] = Field(default_factory=list)
    resume_versions: List[ResumeVersionRecord] = Field(default_factory=list)
    status_history: List[Dict[str, Any]] = Field(default_factory=list)
    next_action: str = "Analyze job requirements"

    def model_post_init(self, __context: Any) -> None:
        if self.applied_date and not self.date_applied:
            self.date_applied = self.applied_date
        elif self.date_applied and not self.applied_date:
            self.applied_date = self.date_applied


class ApplicationCreate(BaseModel):
    """Payload to create or track a new application."""
    company: str
    job_title: str
    source: str = "DIRECT"
    job_location: Optional[str] = "Remote / Flexible"
    job_url: Optional[str] = None
    job_description: str
    user_decision: Optional[DecisionRecommendation] = None
    status: Optional[ApplicationStatus] = ApplicationStatus.SAVED
    recruiter: Optional[str] = None
    notes: Optional[str] = None


class ApplicationUpdate(BaseModel):
    """Payload to update application state, decision, or status."""
    user_decision: Optional[DecisionRecommendation] = None
    application_status: Optional[ApplicationStatus] = None
    selected_strategy: Optional[str] = None
    resume_id: Optional[str] = None
    resume_version: Optional[str] = None
    ats_score: Optional[float] = None
    interview_prep_id: Optional[str] = None
    date_applied: Optional[str] = None
    applied_date: Optional[str] = None
    interview_status: Optional[str] = None
    recruiter: Optional[str] = None
    final_outcome: Optional[str] = None
    new_note: Optional[str] = None


class ApplicationFilter(BaseModel):
    """Filter criteria for querying applications."""
    status: Optional[ApplicationStatus] = None
    recommendation: Optional[DecisionRecommendation] = None
    role_category: Optional[str] = None
    search_query: Optional[str] = None
    location: Optional[str] = None
    source: Optional[str] = None


class DashboardMetrics(BaseModel):
    """KPI summary metrics for CareerPilot Dashboard."""
    total_jobs: int = 0
    total_jobs_analyzed: int = 0
    jobs_to_apply: int = 0
    worth_applying: int = 0
    jobs_reviewed: int = 0
    under_review: int = 0
    jobs_skipped: int = 0
    applications_submitted: int = 0
    applications_sent: int = 0
    interviews: int = 0
    offers: int = 0
    rejected: int = 0
    no_response: int = 0
    interview_preps_completed: int = 0
    mock_interviews_completed: int = 0
    average_mock_score: float = 0.0
    average_ats_score: float = 0.0





class SkillGapItem(BaseModel):
    """Cross-application aggregated skill demand item."""
    skill_name: str
    frequency_count: int = 1
    candidate_status: str = "Genuine Gap"  # "Verified Strong", "Transferable", "Genuine Gap"
    target_role: Optional[str] = None
    recommendation: str = ""


class SkillGapSummary(BaseModel):
    """Aggregated intelligence on skill demand and candidate strengths/gaps."""
    top_missing_skills: List[SkillGapItem] = Field(default_factory=list)
    top_demanded_skills: List[SkillGapItem] = Field(default_factory=list)
    priority_learning_topics: List[str] = Field(default_factory=list)
