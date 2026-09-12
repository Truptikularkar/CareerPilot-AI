"""
CareerPilot AI — LinkedIn Integration
Adheres strictly to zero-scraping policy. Supports:
1. Official OAuth/API integration state tracking
2. Explicit field limitation explanations
3. Manual data archive import (CSV/JSON/PDF) as official fallback
"""
import csv
import io
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from careerpilot.core.constants import ProvenanceSourceType
from careerpilot.core.logging import get_logger
from careerpilot.db.repository import ExternalProfileRepository, CandidateRepository
from careerpilot.db.schema import CandidateEvidenceDB
from careerpilot.db.session import get_db

logger = get_logger("careerpilot.integrations.linkedin")


class LinkedInConnector:
    """Zero-scraping LinkedIn connector and manual data export parser."""

    @classmethod
    def resolve_profile_url(
        cls,
        candidate_id: str = "trupti_kularkar",
        explicit_url: Optional[str] = None,
    ) -> str:
        """Resolves candidate's LinkedIn profile URL from explicit URL or database."""
        if explicit_url and explicit_url.strip():
            url = explicit_url.strip()
            if url.startswith("http"):
                return url
            return f"https://www.linkedin.com/in/{url.lstrip('/')}"
        db_record = ExternalProfileRepository.get_profile("LINKEDIN", candidate_id=candidate_id)
        if db_record and db_record.profile_url:
            return db_record.profile_url
        profile = CandidateRepository.get_profile(candidate_id=candidate_id)
        if profile and profile.linkedin_url:
            return profile.linkedin_url
        return "https://www.linkedin.com/in/trupti-kularkar-579062210/"


    @classmethod
    def get_status(cls, candidate_id: str = "trupti_kularkar") -> Dict[str, Any]:
        """Returns the LinkedIn connection status and field limitations."""
        db_record = ExternalProfileRepository.get_profile("LINKEDIN", candidate_id=candidate_id)
        is_connected = db_record.is_connected if db_record else False
        profile_url = cls.resolve_profile_url(candidate_id=candidate_id)

        return {
            "platform": "LINKEDIN",
            "is_connected": is_connected,
            "profile_url": profile_url,
            "api_tier": "Basic Member Profile (Self-Serve)",
            "scraping_policy": "STRICTLY_PROHIBITED (Zero Scraping Enforced)",
            "api_field_limitations": {
                "recommendations": "LinkedIn API access does not provide this field (requires enterprise LinkedIn Talent Solutions partner tier).",
                "network_connections": "LinkedIn API access does not provide this field (restricted for member privacy).",
                "inmail_messaging": "LinkedIn API access does not provide this field (requires Recruiter enterprise tier).",
            },
            "last_synced_at": db_record.last_synced_at.isoformat() if db_record and db_record.last_synced_at else None,
        }

    @classmethod
    def fetch_profile_data(cls, candidate_id: str = "trupti_kularkar") -> Dict[str, Any]:
        """Returns LinkedIn profile data status adhering to strict zero-scraping compliance."""
        status = cls.get_status(candidate_id=candidate_id)
        return {
            **status,
            "scraping_permitted": False,
            "data_source_mode": "Official Member API / Manual Archive Only (Browser automation prohibited)",
        }


    @classmethod
    def connect_profile(
        cls,
        candidate_id: str = "trupti_kularkar",
        profile_url: Optional[str] = None,
        is_connected: bool = True,
    ) -> Dict[str, Any]:
        """Records connected profile status in SQLite."""
        target_url = profile_url or cls.resolve_profile_url(candidate_id=candidate_id)
        username = target_url.rstrip("/").split("/")[-1] if target_url else "candidate"
        record = ExternalProfileRepository.save_profile(
            platform="LINKEDIN",
            candidate_id=candidate_id,
            username=username,
            profile_url=target_url,
            is_connected=is_connected,
            sync_status="CONNECTED" if is_connected else "DISCONNECTED",
            raw_data={"connected_at": datetime.now(timezone.utc).isoformat()},
        )
        return {"status": "SUCCESS", "is_connected": record.is_connected}

    @classmethod
    def parse_manual_csv_export(
        cls,
        csv_content: str,
        section: str = "positions",
        candidate_id: str = "trupti_kularkar",
    ) -> List[Dict[str, Any]]:
        """
        Parses official candidate-downloaded LinkedIn export CSV (e.g. Positions.csv, Skills.csv).
        Persists parsed items into CandidateEvidenceDB with full provenance.
        """
        reader = csv.DictReader(io.StringIO(csv_content))
        imported_items = []

        with get_db() as db:
            for idx, row in enumerate(reader):
                fact_id = f"li_{section}_{idx}"
                stmt = ""
                if section == "positions":
                    title = row.get("Title") or row.get("Role") or "Role"
                    company = row.get("Company Name") or row.get("Company") or "Company"
                    dates = f"{row.get('Started On', '')} - {row.get('Finished On', 'Present')}"
                    stmt = f"{title} at {company} ({dates})"
                elif section == "skills":
                    skill_name = row.get("Name") or row.get("Skill") or ""
                    if not skill_name:
                        continue
                    stmt = f"Verified skill: {skill_name}"
                else:
                    stmt = ", ".join(f"{k}: {v}" for k, v in row.items() if v)

                if not stmt:
                    continue

                ev_type = "EXPERIENCE" if section == "positions" else ("SKILL" if section == "skills" else "GENERAL")

                existing = db.query(CandidateEvidenceDB).filter(CandidateEvidenceDB.id == f"ev_{fact_id}").first()
                if existing:
                    existing.content = stmt
                    existing.status = "VERIFIED"
                    existing.updated_at = datetime.now(timezone.utc)
                else:
                    new_ev = CandidateEvidenceDB(
                        id=f"ev_{fact_id}",
                        candidate_id=candidate_id,
                        fact_id=fact_id,
                        section=section,
                        source_section=section,
                        evidence_type=ev_type,
                        content=stmt,
                        source_type=ProvenanceSourceType.LINKEDIN_EXPORT.value,

                        source_id=f"export_{section}",
                        source_document="LinkedIn_Export_Archive",
                        status="VERIFIED",
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc),
                    )
                    db.add(new_ev)
                imported_items.append({"fact_id": fact_id, "statement": stmt})

            db.commit()

        logger.info(f"Imported {len(imported_items)} LinkedIn export items for section '{section}'.")
        return imported_items

    @classmethod
    def import_manual_profile_text(
        cls,
        profile_text: str,
        section: str = "summary",
        candidate_id: str = "trupti_kularkar",
    ) -> int:
        """
        Parses manually pasted LinkedIn profile text into verified candidate evidence.
        """
        lines = [line.strip() for line in profile_text.splitlines() if line.strip()]
        imported_count = 0

        with get_db() as db:
            for idx, line in enumerate(lines):
                if len(line) < 8:
                    continue
                fact_id = f"li_text_{section}_{idx}_{int(datetime.now(timezone.utc).timestamp())}"
                ev_type = "EXPERIENCE" if section == "experience" else ("SKILL" if section == "skills" else "SUMMARY")
                new_ev = CandidateEvidenceDB(
                    id=f"ev_{fact_id}",
                    candidate_id=candidate_id,
                    fact_id=fact_id,
                    section=section,
                    source_section=section,
                    evidence_type=ev_type,
                    content=line,
                    source_type=ProvenanceSourceType.LINKEDIN_EXPORT.value,
                    source_id="linkedin_manual_paste",
                    source_document="LinkedIn_Profile_Paste",
                    status="VERIFIED",
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                db.add(new_ev)
                imported_count += 1

            db.commit()

        logger.info(f"Imported {imported_count} facts from LinkedIn profile text ({section}).")
        return imported_count

    @classmethod
    def parse_linkedin_pdf(
        cls,
        pdf_bytes: bytes,
        candidate_id: str = "trupti_kularkar",
    ) -> Dict[str, Any]:
        """
        Parses an official LinkedIn profile PDF generated via LinkedIn's 'More > Save to PDF' feature.
        Extracts sections (Summary, Experience, Education, Skills) and records verified evidence.
        """
        import pymupdf

        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        full_text = "\n".join([page.get_text() or "" for page in doc])
        doc.close()

        lines = [l.strip() for l in full_text.splitlines() if l.strip()]
        imported_items = []
        current_section = "summary"

        with get_db() as db:
            for idx, line in enumerate(lines):
                lower = line.lower()
                if lower in ["summary", "about"]:
                    current_section = "summary"
                    continue
                elif lower in ["experience", "work experience"]:
                    current_section = "experience"
                    continue
                elif lower in ["education"]:
                    current_section = "education"
                    continue
                elif lower in ["top skills", "skills"]:
                    current_section = "skills"
                    continue
                elif lower in ["certifications", "licenses & certifications"]:
                    current_section = "certifications"
                    continue

                if len(line) < 5 or line.startswith("Page ") or "www.linkedin.com" in line:
                    continue

                fact_id = f"li_pdf_{current_section}_{idx}_{int(datetime.now(timezone.utc).timestamp())}"
                ev_type = (
                    "EXPERIENCE" if current_section == "experience"
                    else "SKILL" if current_section == "skills"
                    else "EDUCATION" if current_section == "education"
                    else "SUMMARY"
                )
                new_ev = CandidateEvidenceDB(
                    id=f"ev_{fact_id}",
                    candidate_id=candidate_id,
                    fact_id=fact_id,
                    section=current_section,
                    source_section=current_section,
                    evidence_type=ev_type,
                    content=line,
                    source_type=ProvenanceSourceType.LINKEDIN_EXPORT.value,
                    source_id="linkedin_profile_pdf",
                    source_document="LinkedIn_Profile_PDF",
                    status="VERIFIED",
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                db.add(new_ev)
                imported_items.append({"section": current_section, "statement": line})

            db.commit()

        logger.info(f"Imported {len(imported_items)} items from LinkedIn Profile PDF.")
        return {
            "status": "SUCCESS",
            "imported_count": len(imported_items),
            "items": imported_items[:10],
        }

