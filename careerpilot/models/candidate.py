from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, EmailStr, field_validator
import uuid
from datetime import datetime, timezone
from careerpilot.core.constants import SkillCategory, SeniorityLevel, RoleCategory
from careerpilot.models.evidence import CandidateEvidence


def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Skill(BaseModel):
    name: str
    category: SkillCategory = SkillCategory.PROGRAMMING
    years_of_experience: Optional[float] = None
    proficiency_level: str = "Proficient"  # Beginner, Intermediate, Advanced, Expert
    verified: bool = True
    evidence_level: str = "PROFESSIONAL"  # PROFESSIONAL, PERSONAL_PROJECT, LEARNING_KNOWLEDGE
    evidence_status: str = "VERIFIED"  # VERIFIED, PARTIAL, UNVERIFIED
    context: Optional[str] = None  # e.g., "Used in production at Acme Corp and in Personal LLM Project"

    @field_validator("category", mode="before")
    @classmethod
    def parse_category(cls, v: Any) -> SkillCategory:
        if isinstance(v, str):
            try:
                return SkillCategory(v)
            except ValueError:
                return SkillCategory.OTHER
        return v


class Experience(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company: str
    title: str
    location: Optional[str] = None
    start_date: str
    end_date: Optional[str] = "Present"
    is_current: bool = False
    responsibilities: List[str] = Field(default_factory=list)
    technologies_used: List[str] = Field(default_factory=list)
    verified_metrics: List[str] = Field(default_factory=list)


class Project(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    project_type: str = "PERSONAL_PROJECT"  # PERSONAL_PROJECT, PROFESSIONAL_EXPERIENCE, OPEN_SOURCE, RESEARCH
    description: str
    technologies: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    architecture: Optional[str] = None
    outcome: Optional[str] = None
    metrics: List[str] = Field(default_factory=list)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    github_or_demo_url: Optional[str] = None
    highlights: List[str] = Field(default_factory=list)
    verified_metrics: List[str] = Field(default_factory=list)


class Education(BaseModel):
    institution: str
    degree: str
    field_of_study: str
    graduation_year: Optional[str] = None
    gpa_or_honors: Optional[str] = None


class Achievement(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    metrics: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)


class CareerPreference(BaseModel):
    target_roles: List[RoleCategory] = Field(default_factory=list)
    preferred_seniority: SeniorityLevel = SeniorityLevel.SENIOR
    work_modes: List[str] = Field(default_factory=lambda: ["Remote", "Hybrid"])
    target_locations: List[str] = Field(default_factory=list)
    min_desired_comp: Optional[str] = None
    domains_of_interest: List[str] = Field(default_factory=list)
    preferred_company_types: List[str] = Field(default_factory=lambda: ["Service-based", "Product-based"])
    cloud_preferences: List[str] = Field(default_factory=lambda: ["GCP", "AWS"])

    @field_validator("target_roles", mode="before")
    @classmethod
    def parse_roles(cls, v: Any) -> List[RoleCategory]:
        if isinstance(v, list):
            res = []
            for r in v:
                if isinstance(r, str):
                    try:
                        res.append(RoleCategory(r))
                    except ValueError:
                        res.append(RoleCategory.OTHER)
                else:
                    res.append(r)
            return res
        return v

    @field_validator("preferred_seniority", mode="before")
    @classmethod
    def parse_seniority(cls, v: Any) -> SeniorityLevel:
        if isinstance(v, str):
            try:
                return SeniorityLevel(v)
            except ValueError:
                return SeniorityLevel.MID_LEVEL
        return v


class CandidateProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    full_name: str

    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    location: Optional[str] = None
    professional_summary: str
    skills: List[Skill] = Field(default_factory=list)
    experiences: List[Experience] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    achievements: List[Achievement] = Field(default_factory=list)
    preferences: CareerPreference = Field(default_factory=CareerPreference)
    atomic_evidence: List[CandidateEvidence] = Field(default_factory=list)
    last_updated_at: str = Field(default_factory=utc_iso)


class ProfileDiffItem(BaseModel):
    diff_id: str = Field(default_factory=lambda: f"diff_{uuid.uuid4().hex[:8]}")
    section: str  # "skills", "projects", "experiences", "education", "certifications", "summary"
    change_type: str  # "ADDED", "REMOVED", "CHANGED", "UNCHANGED"
    item_name: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    approved: bool = True


class ProfileDiffResult(BaseModel):
    diff_items: List[ProfileDiffItem] = Field(default_factory=list)
    total_added: int = 0
    total_removed: int = 0
    total_changed: int = 0
    total_unchanged: int = 0


class ProfileVersion(BaseModel):
    id: str
    candidate_id: str
    version_tag: str
    change_summary: str
    changed_sections: List[str] = Field(default_factory=list)
    created_at: str
    profile: CandidateProfile


class ProfileHealthSummary(BaseModel):
    completeness_score: float = 100.0  # 0 to 100%
    evidence_coverage_score: float = 100.0
    rag_synchronized: bool = True
    preferences_configured: bool = True
    last_profile_update: str = ""
    last_rag_sync: str = ""
    total_skills: int = 0
    total_projects: int = 0
    total_experiences: int = 0
    total_evidence_chunks: int = 0
    health_notes: List[str] = Field(default_factory=list)
