"""
CareerPilot AI — Naukri Integration
Adheres strictly to zero-scraping policy. Supports:
1. Authorized API integration status abstraction
2. Manual JD paste / export parsing with automatic job deduplication
3. Manual candidate resume / profile parsing with provenance tracking
"""
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from careerpilot.analysis.job_deduplicator import JobDeduplicator
from careerpilot.core.constants import ProvenanceSourceType
from careerpilot.core.logging import get_logger
from careerpilot.db.repository import ExternalProfileRepository
from careerpilot.db.schema import CandidateEvidenceDB
from careerpilot.db.session import get_db

logger = get_logger("careerpilot.integrations.naukri")


class NaukriConnector:
    """Zero-scraping Naukri job connector and manual parser."""

    @classmethod
    def get_status(cls, candidate_id: str = "trupti_kularkar") -> Dict[str, Any]:
        """Returns Naukri API connector status and policies."""
        db_record = ExternalProfileRepository.get_profile("NAUKRI", candidate_id=candidate_id)
        return {
            "platform": "NAUKRI",
            "is_connected": db_record.is_connected if db_record else False,
            "api_status": "DISABLED",
            "message": "Naukri API integration is disabled (requires authorized Naukri Recruiter/Partner API credentials).",
            "scraping_policy": "STRICTLY_PROHIBITED (Zero Scraping Enforced)",
            "supported_alternatives": [
                "Manual Job Description paste / import",
                "Manual Candidate Profile / Resume import",
            ],
        }

    @classmethod
    def parse_and_deduplicate_job(
        cls,
        company_name: str,
        job_title: str,
        raw_text: str,
        location: Optional[str] = "Bangalore",
        naukri_job_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Ingests a manually exported/pasted Naukri JD, passes it through the JobDeduplicator,
        and links it to a canonical job record.
        """
        source_url = naukri_job_url or "https://www.naukri.com/manual-import"
        dedup_res = JobDeduplicator.deduplicate_job(
            company_name=company_name,
            job_title=job_title,
            location=location,
            source_url=source_url,
            raw_text=raw_text,
        )

        return {
            "status": "SUCCESS",
            "source": "NAUKRI",
            "canonical_job_id": dedup_res["canonical_job_id"],
            "is_duplicate": dedup_res["is_duplicate"],
            "matched_by": dedup_res.get("matched_by"),
            "company_name": dedup_res["company_name"],
            "job_title": dedup_res["job_title"],
            "location": dedup_res["location"],
            "source_urls": dedup_res["source_urls"],
        }

    @classmethod
    def import_manual_profile_text(
        cls,
        profile_text: str,
        candidate_id: str = "trupti_kularkar",
    ) -> int:
        """
        Parses manually pasted Naukri profile text into verified candidate evidence.
        """
        lines = [line.strip() for line in profile_text.splitlines() if line.strip()]
        imported_count = 0

        with get_db() as db:
            for idx, line in enumerate(lines):
                if len(line) < 10:
                    continue
                fact_id = f"naukri_fact_{idx}"
                existing = db.query(CandidateEvidenceDB).filter(CandidateEvidenceDB.id == f"ev_{fact_id}").first()
                if existing:
                    existing.content = line
                    existing.status = "VERIFIED"
                    existing.updated_at = datetime.now(timezone.utc)
                else:
                    new_ev = CandidateEvidenceDB(
                        id=f"ev_{fact_id}",
                        candidate_id=candidate_id,
                        fact_id=fact_id,
                        section="summary",
                        source_section="summary",
                        evidence_type="SUMMARY",
                        content=line,
                        source_type=ProvenanceSourceType.NAUKRI.value,
                        source_id="naukri_manual_paste",
                        source_document="Naukri_Profile_Export",
                        status="VERIFIED",
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc),
                    )
                    db.add(new_ev)
                imported_count += 1

            db.commit()

        logger.info(f"Imported {imported_count} facts from Naukri profile text.")
        return imported_count
