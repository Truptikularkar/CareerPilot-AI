from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid
from datetime import datetime, timezone
from careerpilot.core.constants import EvidenceStatus, EvidenceType, ProvenanceSourceType


def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class CandidateEvidence(BaseModel):
    """Atomic chunk of verified candidate experience, project, or skill with explicit data provenance."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    fact_id: Optional[str] = None
    candidate_id: str = "default_candidate"
    source_type: ProvenanceSourceType = ProvenanceSourceType.PROFESSIONAL_EXPERIENCE
    source_id: Optional[str] = None
    source_document: str = "SQLite Candidate Profile"
    section: str = "Experience"
    evidence_status: EvidenceStatus = EvidenceStatus.SUPPORTED
    evidence_type: EvidenceType = EvidenceType.WORK_EXPERIENCE
    source_section: str = ""  # e.g., "Experience: Programmer Analyst at Cognizant"
    content: str = ""  # The atomic fact/statement
    skill_tags: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    metrics: List[str] = Field(default_factory=list)
    confidence: float = 1.0
    status: EvidenceStatus = EvidenceStatus.SUPPORTED
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=utc_iso)
    updated_at: str = Field(default_factory=utc_iso)

    def model_post_init(self, __context: Any) -> None:
        if not self.fact_id:
            self.fact_id = self.id
        if not self.source_section:
            self.source_section = f"{self.section}: {self.source_id or 'General'}"
        if self.evidence_status != self.status:
            if self.status != EvidenceStatus.SUPPORTED:
                self.evidence_status = self.status
            else:
                self.status = self.evidence_status



class VerificationResult(BaseModel):
    """Result of truth verification for a generated claim or answer."""
    claim: str
    status: EvidenceStatus
    matched_evidence_ids: List[str] = Field(default_factory=list)
    explanation: str
    unsupported_elements: List[str] = Field(default_factory=list)
