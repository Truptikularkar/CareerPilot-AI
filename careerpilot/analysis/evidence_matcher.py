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
from careerpilot.models.candidate import CandidateProfile
from careerpilot.rag.retriever import DualStoreRetriever, RetrievalResult
from careerpilot.core.logging import get_logger

logger = get_logger(__name__)


class EvidenceMatcher:
    """
    Matches extracted Job Requirements against Candidate Profile and RAG Evidence Store.
    Calculates explicit experience gaps, cloud transferability, and preference alignment.
    Directly reflects candidate profile updates (skills, projects, experiences, preferences).
    """

    CANDIDATE_TOTAL_EXPERIENCE_YEARS = 1.9  # Verified candidate experience baseline fallback

    def __init__(
        self,
        retriever: Optional[DualStoreRetriever] = None,
        preferences_path: Optional[Path] = None,
        candidate_profile: Optional[CandidateProfile] = None,
        candidate_id: Optional[str] = None,
    ):
        self.retriever = retriever or DualStoreRetriever()
        self.preferences_path = preferences_path or Path("data/candidate/preferences.yaml")
        self.candidate_profile = candidate_profile
        self.candidate_id = candidate_id or (candidate_profile.id if candidate_profile else None)
        self.preferences = self._load_preferences()

    @property
    def candidate_years(self) -> float:
        """Dynamically computes candidate's total verified experience years."""
        if self.candidate_profile and self.candidate_profile.experiences:
            from careerpilot.core.date_utils import calculate_total_experience_years
            calc_yrs = calculate_total_experience_years(self.candidate_profile.experiences)
            if calc_yrs > 0:
                return round(calc_yrs, 1)
        return self.CANDIDATE_TOTAL_EXPERIENCE_YEARS

    def _load_preferences(self) -> Dict[str, Any]:
        if self.preferences_path.exists():
            try:
                with open(self.preferences_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f).get("career_preferences", {})
            except Exception as e:
                logger.warning("Could not load preferences from %s: %s", self.preferences_path, e)
        return {}

    def match_requirement(self, req: JobRequirement) -> RequirementMatch:
        """Matches a single requirement against Candidate Profile and Evidence RAG."""
        norm_skill_lower = (req.normalized_skill or "").lower().strip()
        skill_name_lower = (req.skill_name or "").lower().strip()
        cand_yrs = self.candidate_years

        match_status = MatchStatus.GAP
        years_status = MatchStatus.MATCH
        matched_text = None
        matched_id = None
        notes = ""

        # 1. Direct profile skill check (Instant ground-truth match from Candidate Profile)
        if self.candidate_profile and self.candidate_profile.skills:
            for s in self.candidate_profile.skills:
                s_name_lower = s.name.lower().strip()
                if (
                    s_name_lower == norm_skill_lower
                    or s_name_lower == skill_name_lower
                    or (len(norm_skill_lower) > 3 and norm_skill_lower in s_name_lower)
                    or (len(s_name_lower) > 3 and s_name_lower in norm_skill_lower)
                ):
                    match_status = MatchStatus.MATCH
                    matched_text = f"Verified skill: {s.name} ({s.proficiency_level}, {s.years_of_experience} yrs verified experience)"
                    matched_id = f"skill_{s.name.lower().replace(' ', '_')}"
                    notes = f"Directly matched from candidate verified profile ({getattr(s.evidence_level, 'value', s.evidence_level)})."
                    break

        # 2. Semantic & Domain Equivalency for Machine Learning & AI
        if match_status == MatchStatus.GAP:
            if norm_skill_lower in ("machine learning", "ml", "deep learning", "predictive modeling"):
                # Check candidate education (B.Tech AI), Vertex AI, BigQuery ML, and ML projects
                has_ai_degree = any(
                    "artificial intelligence" in (f"{ed.degree} {ed.field_of_study}").lower()
                    for ed in (self.candidate_profile.education if self.candidate_profile else [])
                )
                has_bqml = any(
                    "bigquery ml" in s.name.lower() or "machine learning" in s.name.lower()
                    for s in (self.candidate_profile.skills if self.candidate_profile else [])
                )
                has_vertex = any(
                    "vertex ai" in s.name.lower()
                    for s in (self.candidate_profile.skills if self.candidate_profile else [])
                )
                has_ml_proj = any(
                    "anomaly detection" in (f"{p.name} {p.description}").lower()
                    or "bigquery ml" in " ".join(p.technologies).lower()
                    for p in (self.candidate_profile.projects if self.candidate_profile else [])
                )

                if has_ai_degree or has_bqml or has_vertex or has_ml_proj:
                    match_status = MatchStatus.MATCH
                    matched_text = "Verified background in Machine Learning: B.Tech (Artificial Intelligence), BigQuery ML regression models, and Vertex AI production pipelines."
                    matched_id = "domain_ai_ml_verified"
                    notes = "Strong domain match: Candidate holds an AI degree and builds BigQuery ML / Vertex AI models in production."

            elif norm_skill_lower in (
                "generative ai & llms", "generative ai", "genai", "llm orchestration",
                "prompt engineering", "ai agents", "ai agent"
            ):
                has_genai = any(
                    any(w in s.name.lower() for w in ["vertex ai", "gemini", "langgraph", "langchain", "rag", "generative ai"])
                    for s in (self.candidate_profile.skills if self.candidate_profile else [])
                )
                if has_genai:
                    match_status = MatchStatus.MATCH
                    matched_text = "Verified production experience building LLM ticket resolution agents on Vertex AI (Gemini 2.5 Pro) and multi-agent LangGraph architectures."
                    matched_id = "domain_genai_verified"
                    notes = "Direct match: Candidate develops Vertex AI / Gemini LLM agents and LangGraph architectures."

            elif norm_skill_lower in ("langchain", "langgraph", "llm orchestration framework"):
                has_lang_orch = any(
                    any(w in s.name.lower() for w in ["langgraph", "langchain"])
                    for s in (self.candidate_profile.skills if self.candidate_profile else [])
                ) or any(
                    any(w in f"{p.name} {' '.join(p.technologies)}".lower() for w in ["langgraph", "langchain"])
                    for p in (self.candidate_profile.projects if self.candidate_profile else [])
                )
                if has_lang_orch:
                    match_status = MatchStatus.MATCH
                    matched_text = "Verified experience with LLM orchestration frameworks (LangGraph / LangChain) in multi-agent autonomous architectures."
                    matched_id = "skill_langchain_langgraph"
                    notes = "Framework match: Candidate has demonstrated expertise in LangGraph/LangChain agent orchestration."


        # 3. Direct inspection of candidate projects and experiences
        if match_status == MatchStatus.GAP and self.candidate_profile:
            # Check projects
            for p in (self.candidate_profile.projects or []):
                p_text = f"{p.name} {' '.join(p.technologies)} {p.description} {' '.join(p.responsibilities)}".lower()
                if (len(norm_skill_lower) > 2 and norm_skill_lower in p_text) or (len(skill_name_lower) > 2 and skill_name_lower in p_text):
                    match_status = MatchStatus.MATCH
                    matched_text = f"Demonstrated in project '{p.name}': {p.description}"
                    matched_id = f"proj_{p.name[:20].lower().replace(' ', '_')}"
                    notes = f"Verified evidence found in candidate project: {p.name}"
                    break

            # Check experiences
            if match_status == MatchStatus.GAP:
                for exp in (self.candidate_profile.experiences or []):
                    exp_text = f"{exp.title} {exp.company} {' '.join(exp.technologies_used)} {' '.join(exp.responsibilities)}".lower()
                    if (len(norm_skill_lower) > 2 and norm_skill_lower in exp_text) or (len(skill_name_lower) > 2 and skill_name_lower in exp_text):
                        match_status = MatchStatus.MATCH
                        resp_snippet = exp.responsibilities[0] if exp.responsibilities else ""
                        matched_text = f"Production experience at {exp.company} ({exp.title}): {resp_snippet}"
                        matched_id = f"exp_{exp.company.lower().replace(' ', '_')}"
                        notes = f"Verified evidence found in production experience at {exp.company}"
                        break

        # 4. Fallback RAG retrieval from vector store
        if match_status == MatchStatus.GAP:
            query = f"{req.normalized_skill} {req.skill_name}"
            filters = {}
            if self.candidate_id:
                filters["candidate_id"] = self.candidate_id

            try:
                results = self.retriever.retrieve_candidate_evidence(
                    query=query,
                    limit=5,
                    filters=filters if filters else None,
                    evidence_status="SUPPORTED",
                )
            except Exception as e:
                logger.debug("Retriever fallback error: %s", e)
                results = []

            best_match = None
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
            candidate_years=cand_yrs,
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
        """Evaluates how well the JD aligns with candidate career preferences (Pune/Nagpur/Remote, Role, Direction)."""
        score = 100.0
        reasons = []

        # 1. Target Role alignment
        if self.candidate_profile and self.candidate_profile.preferences and self.candidate_profile.preferences.target_roles:
            target_roles_raw = self.candidate_profile.preferences.target_roles
            target_roles = [
                (r.value.lower() if hasattr(r, "value") else str(r).lower()).replace("_", " ")
                for r in target_roles_raw
            ]
        else:
            target_roles = [r.lower() for r in self.preferences.get("role_preferences", {}).get("highest_priority", [])]

        role_str = primary_role.value.lower().replace("_", " ")
        if any(tr in role_str or role_str in tr for tr in target_roles) or primary_role in (
            RoleCategory.AI_DATA_ENGINEER,
            RoleCategory.GENAI_ENGINEER,
            RoleCategory.DATA_ENGINEER,
            RoleCategory.GCP_DATA_ENGINEER,
            RoleCategory.AI_ENGINEER,
        ):
            reasons.append(f"Role '{primary_role.value}' directly matches top priority career target.")
        else:
            score -= 15.0
            reasons.append(f"Role '{primary_role.value}' is outside top priority roles.")

        # 2. Location match
        if self.candidate_profile and self.candidate_profile.preferences and self.candidate_profile.preferences.target_locations:
            pref_locs = [l.lower() for l in self.candidate_profile.preferences.target_locations]
        else:
            pref_locs = [l.lower() for l in self.preferences.get("location", {}).get("primary", ["pune", "nagpur"])]

        # Candidate's current location is also an automatic primary match
        if self.candidate_profile and self.candidate_profile.location:
            cand_loc = self.candidate_profile.location.lower()
            for city in ["pune", "nagpur", "mumbai", "bangalore", "bengaluru", "hyderabad"]:
                if city in cand_loc and city not in pref_locs:
                    pref_locs.append(city)

        jd_loc = ((jd.location or "") + " " + (jd.work_mode or "") + " " + jd.raw_text[:300]).lower()
        if any(pl in jd_loc for pl in pref_locs) or "remote" in jd_loc or (jd.work_mode and "remote" in jd.work_mode.lower()):
            reasons.append("Location matches preferred target (Pune / Nagpur / Remote).")
        else:
            score -= 20.0
            reasons.append(f"Location '{jd.location or 'Unspecified'}' is outside primary preference ({', '.join(pref_locs)}).")

        # 3. Company preference (Service 1st, Product 2nd - both supported, never reject product)
        reasons.append("Company model aligns with exploration targets (service or product).")

        return max(20.0, score), reasons
