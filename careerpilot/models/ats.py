from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from careerpilot.core.constants import (
    MatchLevel,
    RequirementImportance,
    RiskSeverity,
    FormattingRiskType,
    SuggestionPriority,
    TruthValidationStatus,
)


class ATSScoreComponent(BaseModel):
    """Individual ATS score component with weight and explainable reasoning."""
    name: str
    score: float
    max_score: float = 100.0
    weight: float
    weighted_score: float
    explanation: str

    @property
    def keyword_score(self) -> float:
        """Alias for score when accessed on keyword alignment components."""
        return self.score



class RequirementCoverageItem(BaseModel):
    """Matrix item comparing JD requirement against resume and verified candidate evidence."""
    requirement: str
    importance: RequirementImportance = RequirementImportance.MUST_HAVE
    match_level: MatchLevel = MatchLevel.GAP
    resume_evidence: Optional[str] = None
    candidate_evidence: Optional[str] = None
    truth_status: str = "SUPPORTED"
    recommendation: str = ""


class TaxonomyAlignmentItem(BaseModel):
    """Alignment breakdown for a specific technical domain/taxonomy category."""
    category_name: str
    jd_skills_count: int
    resume_skills_count: int
    alignment_pct: float


class FormattingRiskItem(BaseModel):
    """Detected ATS layout/formatting risk."""
    risk_type: FormattingRiskType
    severity: RiskSeverity
    description: str
    location: str = "Document Body"
    recommendation: str


class OptimizationSuggestion(BaseModel):
    """Actionable, truth-grounded resume optimization recommendation."""
    priority: SuggestionPriority
    category: str
    current_state: str
    recommended_action: str
    reason: str
    evidence: str = "Verified candidate profile"


class MissingRequirement(BaseModel):
    """Missing JD requirement with truthful recommendation."""
    requirement: str
    importance: RequirementImportance
    candidate_status: str
    resume_status: str
    explanation: str
    recommendation: str


class InterviewReadinessSeed(BaseModel):
    """Seed data contract prepared for Milestone 6 Interview Preparation Engine."""
    job_id: str
    target_role: str
    high_priority_skills: List[str] = Field(default_factory=list)
    candidate_strengths: List[str] = Field(default_factory=list)
    candidate_gaps: List[str] = Field(default_factory=list)
    likely_interview_topics: List[str] = Field(default_factory=list)
    risky_requirements: List[str] = Field(default_factory=list)
    challenged_claims: List[str] = Field(default_factory=list)
    scenario_topics: List[str] = Field(default_factory=list)
    system_design_topics: List[str] = Field(default_factory=list)
    behavioral_themes: List[str] = Field(default_factory=list)


class ATSReport(BaseModel):
    """Comprehensive ATS-Style Compatibility and Resume Optimization Report."""
    resume_id: str
    job_id: str
    job_title: str
    company_name: Optional[str] = None
    target_strategy: str
    overall_score: float  # 0.0 to 100.0
    score_interpretation: str
    components: Dict[str, ATSScoreComponent] = Field(default_factory=dict)
    must_have_coverage_ratio: str = "0/0"
    nice_to_have_coverage_ratio: str = "0/0"
    coverage_matrix: List[RequirementCoverageItem] = Field(default_factory=list)
    taxonomy_alignments: List[TaxonomyAlignmentItem] = Field(default_factory=list)
    formatting_risks: List[FormattingRiskItem] = Field(default_factory=list)
    keyword_density_findings: List[str] = Field(default_factory=list)
    missing_requirements: List[MissingRequirement] = Field(default_factory=list)
    suggestions: List[OptimizationSuggestion] = Field(default_factory=list)
    truth_status: TruthValidationStatus = TruthValidationStatus.PASS
    truth_violations_count: int = 0
    interview_seed: Optional[InterviewReadinessSeed] = None

    @property
    def score(self) -> float:
        """Alias for overall_score for backward compatibility."""
        return self.overall_score

    @property
    def keyword_coverage(self) -> Optional[ATSScoreComponent]:
        """Direct accessor for Keyword & Requirement Coverage component."""
        return self.components.get("keyword_coverage")

    @property
    def keyword_alignment(self) -> Optional[ATSScoreComponent]:
        """Alias for keyword_coverage component."""
        return self.components.get("keyword_coverage")

    @property
    def skill_taxonomy(self) -> Optional[ATSScoreComponent]:
        """Direct accessor for Skill Taxonomy Alignment component."""
        return self.components.get("skill_taxonomy")

    @property
    def semantic_alignment(self) -> Optional[ATSScoreComponent]:
        """Direct accessor for Semantic Role Alignment component."""
        return self.components.get("semantic_alignment")

    @property
    def experience_alignment(self) -> Optional[ATSScoreComponent]:
        """Direct accessor for Experience & Seniority Alignment component."""
        return self.components.get("experience_alignment")

    @property
    def structure(self) -> Optional[ATSScoreComponent]:
        """Direct accessor for Resume Structure & Completeness component."""
        return self.components.get("structure")

    @property
    def formatting(self) -> Optional[ATSScoreComponent]:
        """Direct accessor for Formatting & Layout Compatibility component."""
        return self.components.get("formatting")

    @property
    def readability(self) -> Optional[ATSScoreComponent]:
        """Direct accessor for Readability & Keyword Density component."""
        return self.components.get("readability")


