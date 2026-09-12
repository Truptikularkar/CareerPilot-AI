import re
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from careerpilot.core.constants import (
    MatchStatus,
    CloudTransferabilityStatus,
    RequirementImportance,
    TaxonomyCategory,
    RoleCategory,
)
from careerpilot.models.job import (
    JobDescription,
    JobRequirement,
    RequirementMatch,
    CloudTransferability,
)
from careerpilot.rag.retriever import DualStoreRetriever, RetrievalResult
from careerpilot.core.logging import get_logger

logger = get_logger(__name__)


class EvidenceMatcher:
    """
    Matches extracted Job Requirements against Candidate RAG Evidence Store.
    Calculates explicit experience gaps, cloud transferability, and preference alignment.
    """

    CANDIDATE_TOTAL_EXPERIENCE_YEARS = 1.9  # Verified candidate experience baseline

    def __init__(self, retriever: Optional[DualStoreRetriever] = None, preferences_path: Optional[Path] = None):
        self.retriever = retriever or DualStoreRetriever()
        self.preferences_path = preferences_path or Path("data/candidate/preferences.yaml")
        self.preferences = self._load_preferences()

    def _load_preferences(self) -> Dict[str, Any]:
        if self.preferences_path.exists():
            try:
                with open(self.preferences_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f).get("career_preferences", {})
            except Exception as e:
                logger.warning("Could not load preferences from %s: %s", self.preferences_path, e)
        return {}

    def match_requirement(self, req: JobRequirement) -> RequirementMatch:
        """Matches a single requirement against Candidate Evidence RAG."""
        # Query candidate store specifically with concise skill keywords
        query = f"{req.normalized_skill} {req.skill_name}"
        results = self.retriever.retrieve_candidate_evidence(
            query=query,
            limit=5,
            evidence_status="SUPPORTED",
        )

        match_status = MatchStatus.GAP
        years_status = MatchStatus.MATCH
        matched_text = None
        matched_id = None
        notes = ""

        # Check for direct or partial evidence in retrieved chunks
        best_match = None
        norm_skill_lower = req.normalized_skill.lower()
        stop_words = {
            "and", "the", "for", "with", "experience", "or", "in", "of", "to", "a", "an",
            "is", "as", "at", "by", "from", "on", "using", "track", "record", "strong",
            "deep", "extensive", "equivalent", "hands", "proven", "proficient", "proficiency",
            "knowledge", "skills", "skill", "background", "solid", "understanding",
            "years", "production", "development", "familiarity", "ability", "work",
            "preferred", "required", "qualifications", "minimum", "basic",
        }
        req_words = [w for w in re.findall(r"[a-zA-Z0-9\+\#]+", norm_skill_lower) if len(w) > 1 and w not in stop_words]

        for r in results:
            text_lower = r.text.lower()
            skills_lower = r.skills.lower()

            # Exact or token match in skills or content
            if req_words and any(w in skills_lower or w in text_lower for w in req_words):
                best_match = r
                match_status = MatchStatus.MATCH
                break



        if best_match:
            matched_text = best_match.text
            matched_id = best_match.chunk_id
            notes = f"Verified evidence found in {best_match.source}"
        else:
            # Check if it's a transferable cloud or adjacent skill
            if req.category == TaxonomyCategory.CLOUD and "aws" in norm_skill_lower:
                match_status = MatchStatus.PARTIAL
                notes = "Transferable from verified GCP cloud production experience."
            elif req.category == TaxonomyCategory.SOFT_SKILL:
                match_status = MatchStatus.MATCH
                notes = "General professional capability verified through team leadership & collaboration."
            else:
                match_status = MatchStatus.GAP
                notes = f"No verified candidate evidence for {req.normalized_skill}."

        # Evaluate explicit experience years comparison
        if req.years_required:
            req_yrs = req.years_required
            cand_yrs = self.CANDIDATE_TOTAL_EXPERIENCE_YEARS
            if req_yrs <= 2.0:
                years_status = MatchStatus.MATCH
            elif 2.0 < req_yrs <= 3.5:
                years_status = MatchStatus.PARTIAL
                notes += f" Experience difference: Candidate has {cand_yrs} yrs, JD asks for {req_yrs} yrs."
            else:
                years_status = MatchStatus.GAP
                notes += f" Seniority/Years gap: JD requests {req_yrs}+ yrs, candidate has {cand_yrs} yrs."

        return RequirementMatch(
            requirement=req,
            candidate_evidence_text=matched_text,
            candidate_evidence_id=matched_id,
            match_status=match_status,
            years_match=years_status,
            candidate_years=self.CANDIDATE_TOTAL_EXPERIENCE_YEARS,
            required_years=req.years_required,
            notes=notes.strip(),
        )

    def evaluate_cloud_transferability(self, jd: JobDescription) -> CloudTransferability:
        """Evaluates whether cloud requirements (GCP vs AWS vs Azure) are met or transferable."""
        text_lower = jd.raw_text.lower()
        has_gcp = "gcp" in text_lower or "google cloud" in text_lower or "bigquery" in text_lower
        has_aws = "aws" in text_lower or "amazon web services" in text_lower or "redshift" in text_lower or "glue" in text_lower
        has_azure = "azure" in text_lower or "synapse" in text_lower

        # Identify if AWS is MUST_HAVE or NICE_TO_HAVE
        aws_must_have = any("aws" in r.normalized_skill.lower() and r.importance == RequirementImportance.MUST_HAVE for r in jd.requirements)
        aws_nice_to_have = any("aws" in r.normalized_skill.lower() and r.importance == RequirementImportance.NICE_TO_HAVE for r in jd.requirements)

        if has_gcp and not has_aws:
            return CloudTransferability(
                cloud_requested="Google Cloud Platform (GCP)",
                is_must_have=True,
                is_nice_to_have=False,
                centrality="Core",
                candidate_cloud="GCP",
                transferability_status=CloudTransferabilityStatus.MATCH,
                transferability_reasoning="Direct verified production match. Candidate has deep production experience across BigQuery, Airflow, Vertex AI, and GCP Cloud Storage.",
            )

        if has_gcp and has_aws:
            return CloudTransferability(
                cloud_requested="GCP & AWS Multi-Cloud",
                is_must_have=aws_must_have,
                is_nice_to_have=aws_nice_to_have,
                centrality="Core",
                candidate_cloud="GCP",
                transferability_status=CloudTransferabilityStatus.TRANSFERABLE,
                transferability_reasoning="GCP is verified in production. AWS data architecture patterns (Redshift, Glue, S3) are transferable from BigQuery and GCS.",
            )

        if has_aws and not has_gcp:
            # Check if heavy AWS proprietary architecture is mandatory
            is_heavy_aws = any(w in text_lower for w in ["emr", "glue", "kinesis", "aws certified", "redshift optimization"])
            if aws_must_have and is_heavy_aws:
                return CloudTransferability(
                    cloud_requested="Amazon Web Services (AWS)",
                    is_must_have=True,
                    is_nice_to_have=False,
                    centrality="Core",
                    candidate_cloud="GCP",
                    transferability_status=CloudTransferabilityStatus.SIGNIFICANT_GAP,
                    transferability_reasoning="JD heavily mandates deep AWS-specific proprietary services (Glue/EMR/Redshift) and AWS certifications, which are unevidenced in candidate production history.",
                )
            else:
                return CloudTransferability(
                    cloud_requested="Amazon Web Services (AWS)",
                    is_must_have=aws_must_have,
                    is_nice_to_have=aws_nice_to_have or not aws_must_have,
                    centrality="Secondary" if aws_nice_to_have else "Core",
                    candidate_cloud="GCP",
                    transferability_status=CloudTransferabilityStatus.TRANSFERABLE,
                    transferability_reasoning="Candidate has verified production experience in GCP data engineering (BigQuery, Airflow, SQL, Python). General cloud ETL patterns transfer smoothly to AWS.",
                )

        return CloudTransferability(
            cloud_requested="Cloud Agnostic / Other",
            is_must_have=False,
            is_nice_to_have=False,
            centrality="Secondary",
            candidate_cloud="GCP",
            transferability_status=CloudTransferabilityStatus.NOT_APPLICABLE,
            transferability_reasoning="No strong cloud-specific constraint in JD.",
        )

    def evaluate_preferences(self, jd: JobDescription, primary_role: RoleCategory) -> Tuple[float, List[str]]:
        """Evaluates how well the JD aligns with candidate career preferences (Pune/Nagpur, Role, Direction)."""
        score = 100.0
        reasons = []

        # 1. Target Role alignment
        target_roles = [r.lower() for r in self.preferences.get("role_preferences", {}).get("highest_priority", [])]
        role_str = primary_role.value.lower().replace("_", " ")
        if any(tr in role_str for tr in target_roles):
            reasons.append(f"Role '{primary_role.value}' directly matches top priority career target.")
        else:
            score -= 15.0
            reasons.append(f"Role '{primary_role.value}' is outside top priority roles.")

        # 2. Location match
        pref_locs = [l.lower() for l in self.preferences.get("location", {}).get("primary", ["pune", "nagpur"])]
        jd_loc = (jd.location or jd.raw_text[:200]).lower()
        if any(pl in jd_loc for pl in pref_locs) or "remote" in jd_loc:
            reasons.append("Location matches preferred target (Pune / Nagpur / Remote).")
        else:
            score -= 20.0
            reasons.append(f"Location '{jd.location or 'Unspecified'}' is outside primary Pune/Nagpur preference.")

        # 3. Company preference (Service 1st, Product 2nd - both supported, never reject product)
        reasons.append("Company model aligns with exploration targets (service or product).")

        return max(20.0, score), reasons
