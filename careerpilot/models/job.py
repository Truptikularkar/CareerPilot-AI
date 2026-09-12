from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid
from careerpilot.core.constants import (
    SeniorityLevel,
    RoleCategory,
    RequirementImportance,
    TaxonomyCategory,
    MatchStatus,
    CloudTransferabilityStatus,
    RiskSeverity,
    RiskType,
    DecisionRecommendation,
)


class JobRequirement(BaseModel):
    """Atomic requirement extracted from a Job Description."""
    requirement_id: str = Field(default_factory=lambda: f"req_{uuid.uuid4().hex[:8]}")
    skill_name: str = ""
    normalized_skill: str = ""
    category: TaxonomyCategory = TaxonomyCategory.OTHER
    importance: RequirementImportance = RequirementImportance.MUST_HAVE
    years_required: Optional[float] = None
    experience_type: str = "professional"  # professional, personal, education, general
    evidence_expected: Optional[str] = None
    source_text: str = ""
    confidence: float = 1.0

    # Optional legacy fields for backward compatibility
    title: Optional[str] = None
    description: Optional[str] = None
    target_skills: List[str] = Field(default_factory=list)
    requirement_type: Optional[RequirementImportance] = None

    def model_post_init(self, __context: Any) -> None:
        if self.title and not self.skill_name:
            self.skill_name = self.title
        if self.description and not self.source_text:
            self.source_text = self.description
        if self.target_skills and not self.normalized_skill:
            self.normalized_skill = self.target_skills[0]
        elif not self.normalized_skill and self.skill_name:
            self.normalized_skill = self.skill_name
        if self.requirement_type and not self.importance:
            self.importance = self.requirement_type



class RoleClassification(BaseModel):
    """Classification of the actual role family and seniority."""
    primary_role: RoleCategory = RoleCategory.OTHER
    secondary_role: Optional[RoleCategory] = None
    role_family: str = "Engineering"
    seniority: SeniorityLevel = SeniorityLevel.MID
    confidence: float = 0.90
    reasoning: str = ""


class RoleReality(BaseModel):
    """Work distribution and practical day-to-day responsibilities."""
    detected_role: RoleCategory = RoleCategory.OTHER
    work_distribution: Dict[str, float] = Field(default_factory=dict)
    primary_work_type: str = "Data Engineering"
    secondary_work_types: List[str] = Field(default_factory=list)
    confidence: float = 0.85
    supporting_evidence: List[str] = Field(default_factory=list)
    disclaimer: str = "AI-derived interpretation based on stated responsibilities"


class SeniorityDetection(BaseModel):
    """Detailed seniority requirement analysis."""
    detected_seniority: SeniorityLevel = SeniorityLevel.MID
    explicit_years_required: Optional[float] = None
    reasoning: str = ""
    confidence: float = 0.90

    @property
    def estimated_level(self) -> SeniorityLevel:
        """Alias for detected_seniority for backward compatibility."""
        return self.detected_seniority

    @property
    def seniority(self) -> SeniorityLevel:
        """Alias for detected_seniority."""
        return self.detected_seniority


class CloudTransferability(BaseModel):
    """Explicit cloud experience transferability reasoning (e.g. GCP -> AWS)."""
    cloud_requested: str = "GCP"
    is_must_have: bool = True
    is_nice_to_have: bool = False
    centrality: str = "Core"  # Core, Secondary, Incidental
    candidate_cloud: str = "GCP"
    transferability_status: CloudTransferabilityStatus = CloudTransferabilityStatus.MATCH
    transferability_reasoning: str = ""

    @property
    def primary_target_cloud(self) -> str:
        return self.cloud_requested

    @property
    def candidate_verified_cloud(self) -> str:
        return self.candidate_cloud

    @property
    def status(self) -> CloudTransferabilityStatus:
        return self.transferability_status

    @property
    def explanation(self) -> str:
        return self.transferability_reasoning

    @property
    def recommended_framing(self) -> str:
        return self.transferability_reasoning


class RequirementMatch(BaseModel):
    """Match result for an individual job requirement against candidate evidence."""
    requirement: JobRequirement
    candidate_evidence_text: Optional[str] = None
    candidate_evidence_id: Optional[str] = None
    match_status: MatchStatus = MatchStatus.MATCH
    years_match: MatchStatus = MatchStatus.MATCH
    candidate_years: Optional[float] = None
    required_years: Optional[float] = None
    notes: str = ""

    @property
    def is_matched(self) -> bool:
        return self.match_status in (MatchStatus.MATCH, MatchStatus.PARTIAL)

    @property
    def match_score(self) -> float:
        if self.match_status == MatchStatus.MATCH:
            return 1.0
        elif self.match_status == MatchStatus.PARTIAL:
            return 0.6
        return 0.0

    @property
    def requirement_skill(self) -> str:
        return self.requirement.skill_name or self.requirement.normalized_skill or ""

    @property
    def category(self) -> Any:
        return self.requirement.category

    @property
    def importance(self) -> Any:
        return self.requirement.importance


class RiskItem(BaseModel):
    """Identified risk factor for an application."""
    risk_type: RiskType
    severity: RiskSeverity
    description: str
    supporting_requirement: Optional[str] = None
    candidate_evidence: Optional[str] = None
    mitigation: Optional[str] = None

    @property
    def title(self) -> str:
        return self.risk_type.value.replace("_", " ").title()



class FitScoreBreakdown(BaseModel):
    """Deterministic, explainable component scoring breakdown across 9 calibrated dimensions."""
    must_have_score: float = Field(ge=0.0, le=100.0)
    nice_to_have_score: float = Field(default=80.0, ge=0.0, le=100.0)
    experience_score: float = Field(ge=0.0, le=100.0)
    role_alignment_score: float = Field(ge=0.0, le=100.0)
    evidence_strength_score: float = Field(default=85.0, ge=0.0, le=100.0)
    location_preference_score: float = Field(default=90.0, ge=0.0, le=100.0)
    company_preference_score: float = Field(default=85.0, ge=0.0, le=100.0)
    cloud_score: float = Field(ge=0.0, le=100.0)
    disqualifying_gap_penalty: float = Field(default=0.0)

    # Backward compatible fields
    genai_score: float = Field(default=80.0, ge=0.0, le=100.0)
    data_eng_score: float = Field(default=80.0, ge=0.0, le=100.0)
    preference_score: float = Field(default=85.0, ge=0.0, le=100.0)
    must_have_penalty: float = 0.0
    total_weighted_score: float = Field(ge=0.0, le=100.0)
    weights_used: Dict[str, float] = Field(default_factory=dict)
    penalties: List[Dict[str, Any]] = Field(default_factory=list)
    explanation: str = ""

    @property
    def overall_score(self) -> float:
        return self.total_weighted_score



class JobDescription(BaseModel):
    """Structured representation of a parsed Job Description."""
    id: str = Field(default_factory=lambda: f"job_{uuid.uuid4().hex[:8]}")
    raw_text: str
    company_name: str = "Target Company"
    job_title: str = "Target Role"
    location: Optional[str] = None
    work_mode: Optional[str] = None  # Remote, Hybrid, Onsite
    extracted_role: RoleCategory = RoleCategory.OTHER
    estimated_seniority: SeniorityLevel = SeniorityLevel.MID
    summary: Optional[str] = None
    responsibilities: List[str] = Field(default_factory=list)
    must_have_skills: List[str] = Field(default_factory=list)
    nice_to_have_skills: List[str] = Field(default_factory=list)
    tech_stack: List[str] = Field(default_factory=list)
    requirements: List[JobRequirement] = Field(default_factory=list)
    compensation_range: Optional[str] = None


class JobAnalysisResult(BaseModel):
    """Comprehensive, explainable job analysis result."""
    id: str = Field(default_factory=lambda: f"analysis_{uuid.uuid4().hex[:8]}")
    job_id: str
    job_title: str
    company_name: str
    role_classification: RoleClassification
    role_reality: RoleReality
    seniority_detection: SeniorityDetection
    cloud_transferability: CloudTransferability
    requirements: List[JobRequirement] = Field(default_factory=list)
    matches: List[RequirementMatch] = Field(default_factory=list)
    fit_score: FitScoreBreakdown
    recommendation: DecisionRecommendation = DecisionRecommendation.REVIEW
    risks: List[RiskItem] = Field(default_factory=list)
    key_strengths: List[str] = Field(default_factory=list)
    key_gaps: List[str] = Field(default_factory=list)
    transferable_skills: List[str] = Field(default_factory=list)
    explainable_reasoning: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Milestone 14 Explainability & Transparency Fields
    decision_reason: str = ""
    next_action: str = ""
    confidence: float = 1.0
    top_matching_requirements: List[str] = Field(default_factory=list)
    missing_required_requirements: List[str] = Field(default_factory=list)
    missing_preferred_requirements: List[str] = Field(default_factory=list)
    experience_comparison: Dict[str, Any] = Field(default_factory=dict)
    cloud_comparison: Dict[str, Any] = Field(default_factory=dict)
    zero_score_explanation: Optional[Dict[str, Any]] = None
    penalty_details: List[Dict[str, Any]] = Field(default_factory=list)



class MatchScore(BaseModel):
    """Legacy match score structure."""
    overall_fit_score: float = 0.0
    must_have_score: float = 0.0
    nice_to_have_score: float = 0.0
    seniority_fit_score: float = 0.0
    experience_fit_score: float = 0.0
    total_weighted_score: float = 0.0


class JobAnalysis(BaseModel):
    """Legacy job analysis structure."""
    id: str = Field(default_factory=lambda: f"analysis_{uuid.uuid4().hex[:8]}")
    job_id: str
    candidate_id: Optional[str] = None
    scores: Optional[MatchScore] = None
    matched_skills: List[str] = Field(default_factory=list)
    key_strengths: List[str] = Field(default_factory=list)
    recommendation: DecisionRecommendation = DecisionRecommendation.REVIEW
    explainable_reasoning: str = ""

SkillGap = RiskItem
