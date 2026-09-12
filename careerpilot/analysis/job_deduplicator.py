"""
CareerPilot AI — Canonical Job Deduplication Engine
Detects duplicate job listings across sources (LinkedIn, Naukri, Direct Careers)
and resolves them into a single canonical job in SQLite.
"""
from typing import Optional, Dict, Any
from careerpilot.db.repository import JobDeduplicationRepository
from careerpilot.core.logging import get_logger

logger = get_logger("careerpilot.analysis.job_deduplicator")


class JobDeduplicator:
    """
    Canonical job deduplicator identifying identical postings across sources.
    Matches via:
    1. Canonical URL exact match (normalized without query params)
    2. Exact raw text hash (MD5)
    3. Normalized company name + normalized job title + normalized location
    """

    @classmethod
    def normalize_url(cls, url: Optional[str]) -> Optional[str]:
        """Normalizes job posting URL by stripping tracking/query parameters and trailing slashes."""
        if not url:
            return None
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(url.strip())
        path = parsed.path.rstrip("/")
        return urlunparse((parsed.scheme.lower(), parsed.netloc.lower(), path, "", "", ""))

    @classmethod
    def deduplicate_job(

        cls,
        company_name: str,
        job_title: str,
        location: Optional[str] = None,
        source_url: Optional[str] = None,
        raw_text: Optional[str] = None,
        job_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Resolves or registers a job to a canonical job record.
        Returns metadata including canonical_job_id and whether it was an existing duplicate.
        """
        temp_job_id = job_id or f"temp_{abs(hash(company_name + job_title)) % 100000}"
        
        # Check existing first
        existing = JobDeduplicationRepository.find_canonical_match(
            company_name=company_name,
            job_title=job_title,
            location=location,
            source_url=source_url,
            raw_text=raw_text,
        )

        is_duplicate = existing is not None
        matched_by = None
        if existing:
            import hashlib
            raw_hash = hashlib.md5((raw_text or "").strip().encode("utf-8")).hexdigest() if raw_text else None
            if raw_hash and existing.text_hash == raw_hash:
                matched_by = "text_hash"
            else:
                matched_by = "company_title_location_match"
            logger.info(f"Duplicate job identified (matched via {matched_by}): {company_name} - {job_title}")

        canonical_record = JobDeduplicationRepository.get_or_create_canonical(
            job_id=temp_job_id,
            company_name=company_name,
            job_title=job_title,
            location=location,
            source_url=source_url,
            raw_text=raw_text,
        )

        return {
            "canonical_job_id": canonical_record.id,
            "is_duplicate": is_duplicate,
            "matched_by": matched_by,
            "company_name": canonical_record.company_name,
            "job_title": canonical_record.job_title,
            "location": canonical_record.location,
            "source_urls": list(canonical_record.source_urls_json or []),
            "job_ids": list(canonical_record.job_ids_json or []),
        }
