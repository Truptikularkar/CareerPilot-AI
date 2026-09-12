from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid
from careerpilot.core.constants import (
    ResumeStrategyType,
    TruthValidationStatus,
    ClaimType,
    EvidenceType,
)


class ResumeHeader(BaseModel):
    """Candidate contact and identity header."""
    full_name: str = "Trupti Kularkar"
    email: Optional[str] = "kularkartrupti123@gmail.com"
    phone: Optional[str] = "+91 9834055766"
    location: Optional[str] = "Pune, Maharashtra, India"
    linkedin_url: Optional[str] = "https://linkedin.com/in/trupti-kularkar"
    github_url: Optional[str] = "https://github.com/trupti-kularkar"
    portfolio_url: Optional[str] = None


class ResumeSummary(BaseModel):
    """Targeted professional summary."""
    text: str
    target_title: str
    experience_years_stated: str = "1.9+ years"
    evidence_references: List[str] = Field(default_factory=list)


class ResumeSkillCategory(BaseModel):
    """Categorized technical skills section entry."""
    category_name: str
    skills: List[str] = Field(default_factory=list)


class ResumeBullet(BaseModel):
    """Individual atomic bullet point with grounding evidence linkage."""
    text: str
    evidence_id: Optional[str] = None
    metrics_included: List[str] = Field(default_factory=list)
    technologies_included: List[str] = Field(default_factory=list)
    experience_type: str = "PROFESSIONAL"  # PROFESSIONAL or PERSONAL_PROJECT


class ResumeExperienceEntry(BaseModel):
    """Professional work experience section entry."""
    company: str = "Cognizant"
    title: str = "Programmer Analyst"
    location: Optional[str] = "Pune, India"
    start_date: str = "2023"
    end_date: str = "Present"
    bullets: List[str] = Field(default_factory=list)
    bullet_objects: List[ResumeBullet] = Field(default_factory=list)
    technologies_used: List[str] = Field(default_factory=list)


class ResumeProjectEntry(BaseModel):
    """Personal or production project section entry."""
    name: str
    technologies: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    bullets: List[str] = Field(default_factory=list)
    bullet_objects: List[ResumeBullet] = Field(default_factory=list)
    is_personal_project: bool = True


class ResumeEducationEntry(BaseModel):
    """Education record entry."""
    institution: str
    degree: str
    field_of_study: str
    graduation_year: Optional[str] = None
    honors: Optional[str] = None


class ResumeCertificationEntry(BaseModel):
    """Certification record entry."""
    name: str
    issuer: Optional[str] = None
    year: Optional[str] = None


ResumeExperience = ResumeExperienceEntry
ResumeProject = ResumeProjectEntry
ResumeEducation = ResumeEducationEntry
ResumeCertification = ResumeCertificationEntry


class ResumeStrategy(BaseModel):
    """Target role resume tailoring strategy configuration."""
    strategy_type: ResumeStrategyType = ResumeStrategyType.AI_DATA_ENGINEER
    target_role: str = "AI Data Engineer"
    emphasis_keywords: List[str] = Field(default_factory=list)
    summary_tone: str = "AI + Data Engineering"
    project_priorities: List[str] = Field(default_factory=list)
    skill_priorities: List[str] = Field(default_factory=list)
    reasoning: str = ""


class ATSPrecheckResult(BaseModel):
    """ATS compliance and readability precheck result."""
    passed: bool = True
    score: float = 95.0
    detected_sections: List[str] = Field(default_factory=list)
    missing_sections: List[str] = Field(default_factory=list)
    keyword_alignment_pct: float = 90.0
    formatting_flags: List[str] = Field(default_factory=list)
    word_count: int = 450
    estimated_pages: int = 1


class TruthClaimCheck(BaseModel):
    """Validation record for a single extracted resume claim."""
    claim_text: str
    claim_type: ClaimType
    status: TruthValidationStatus = TruthValidationStatus.PASS
    matched_evidence_id: Optional[str] = None
    evidence_text: Optional[str] = None
    violation_reason: Optional[str] = None


class TruthValidationReport(BaseModel):
    """Comprehensive Truth Guard validation report for a tailored resume draft."""
    status: TruthValidationStatus = TruthValidationStatus.PASS
    verified_claims_count: int = 0
    flagged_claims: List[TruthClaimCheck] = Field(default_factory=list)
    blocked_claims: List[TruthClaimCheck] = Field(default_factory=list)
    metric_checks: List[TruthClaimCheck] = Field(default_factory=list)
    tech_checks: List[TruthClaimCheck] = Field(default_factory=list)
    experience_type_checks: List[TruthClaimCheck] = Field(default_factory=list)
    summary_reasoning: str = "All resume claims are 100% grounded in verified candidate evidence."

    @property
    def claims_evaluated(self) -> List[TruthClaimCheck]:
        return self.flagged_claims + self.blocked_claims + self.metric_checks + self.tech_checks + self.experience_type_checks

    @property
    def blocked_claims_count(self) -> int:
        return len(self.blocked_claims)

    @property
    def summary(self) -> str:
        return self.summary_reasoning



class TailoredResume(BaseModel):
    """Full evidence-grounded tailored resume document."""
    id: str = Field(default_factory=lambda: f"resume_{uuid.uuid4().hex[:8]}")
    job_id: str
    candidate_id: str = "trupti_kularkar"
    strategy: ResumeStrategy
    header: ResumeHeader = Field(default_factory=ResumeHeader)
    summary: ResumeSummary
    skills_categories: List[ResumeSkillCategory] = Field(default_factory=list)
    experiences: List[ResumeExperienceEntry] = Field(default_factory=list)
    projects: List[ResumeProjectEntry] = Field(default_factory=list)
    education: List[ResumeEducationEntry] = Field(default_factory=list)
    certifications: List[ResumeCertificationEntry] = Field(default_factory=list)
    truth_report: Optional[TruthValidationReport] = None
    ats_precheck: Optional[ATSPrecheckResult] = None
    audit_metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def truth_validation(self) -> Optional[TruthValidationReport]:
        return self.truth_report

    @property
    def docx_path(self) -> Optional[str]:
        return self.audit_metadata.get("docx_path")

    @property
    def pdf_path(self) -> Optional[str]:
        return self.audit_metadata.get("pdf_path")

    @property
    def markdown_path(self) -> Optional[str]:
        return self.audit_metadata.get("markdown_path")


    @property
    def experience(self) -> List[ResumeExperienceEntry]:
        return self.experiences

    @property
    def skills_sections(self) -> List[ResumeSkillCategory]:
        return self.skills_categories



class TailoredSection(BaseModel):
    """Legacy section container."""
    title: str = "Section"
    content: str = ""
    bullets: List[str] = Field(default_factory=list)


# Re-export canonical ATSReport and ResumeArtifact for compatibility
from careerpilot.models.ats import ATSReport
from careerpilot.models.artifact import ResumeArtifact, ResumeArtifactBundle



