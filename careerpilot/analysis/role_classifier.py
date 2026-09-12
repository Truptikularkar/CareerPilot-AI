import re
from typing import Dict, List, Any, Optional
from careerpilot.core.constants import SeniorityLevel, RoleCategory
from careerpilot.models.job import JobDescription, RoleClassification, RoleReality, SeniorityDetection
from careerpilot.core.logging import get_logger

logger = get_logger(__name__)


class RoleClassifier:
    """
    Classifies the actual role category, secondary role, and role family
    by analyzing responsibilities and technical stack rather than relying purely on the title.
    """

    ROLE_SIGNALS = {
        RoleCategory.AI_DATA_ENGINEER: {
            "keywords": ["ai data engineer", "llm pipeline", "rag architecture", "agentic data", "ai autoheal"],
            "weight": 1.5,
        },
        RoleCategory.GENAI_ENGINEER: {
            "keywords": ["genai", "generative ai", "llm", "llms", "prompt engineering", "langchain", "langgraph", "rag", "agents", "vector db", "vertex ai"],
            "weight": 1.3,
        },
        RoleCategory.GCP_DATA_ENGINEER: {
            "keywords": ["gcp data engineer", "google cloud data", "gcp", "google cloud", "bigquery", "dataproc", "dataflow", "cloud composer", "pub/sub", "cloud storage"],
            "weight": 1.4,
        },
        RoleCategory.DATA_ENGINEER: {
            "keywords": ["data engineer", "etl", "elt", "data pipeline", "data engineering", "bigquery", "airflow", "spark", "sql", "data warehouse", "data modeling", "dbt", "data quality"],
            "weight": 1.3,
        },
        RoleCategory.CLOUD_DATA_ENGINEER: {
            "keywords": ["cloud data engineer", "aws", "azure", "glue", "emr", "redshift", "synapse", "data lake"],
            "weight": 1.2,
        },
        RoleCategory.AI_ENGINEER: {
            "keywords": ["ai engineer", "artificial intelligence", "applied ai", "deep learning", "neural network", "nlp"],
            "weight": 1.2,
        },
        RoleCategory.DATA_SCIENTIST: {
            "keywords": ["data scientist", "research scientist", "ai research", "statistical analysis", "hypothesis testing", "predictive modeling", "calculus", "linear algebra"],
            "weight": 1.3,
        },
        RoleCategory.ML_ENGINEER: {
            "keywords": ["machine learning engineer", "mlops", "model deployment", "triton", "tensorflow", "pytorch", "cuda"],
            "weight": 1.2,
        },
        RoleCategory.ANALYTICS_ENGINEER: {
            "keywords": ["analytics engineer", "bi developer", "tableau", "looker", "power bi", "dashboard", "reporting", "data mart"],
            "weight": 1.3,
        },
    }

    @classmethod
    def classify(cls, jd: JobDescription) -> RoleClassification:
        """Classifies the actual job role family and seniority based on full JD text."""
        title_lower = jd.job_title.lower()
        resp_text = " ".join(jd.responsibilities).lower()
        must_have_text = " ".join(jd.must_have_skills).lower()
        combined_text = f"{jd.job_title}\n{jd.summary}\n{resp_text}\n{must_have_text}\n{' '.join(jd.tech_stack)}".lower()

        scores: Dict[RoleCategory, float] = {}

        for role, config in cls.ROLE_SIGNALS.items():
            score = 0.0
            kw_list = config["keywords"]
            matches = sum(1 for kw in kw_list if kw in combined_text)
            score += matches * config.get("weight", 1.0)

            # Substantial bonus if title explicitly matches the role
            role_str = role.value.lower().replace("_", " ")
            if role_str in title_lower:
                score += 15.0
            elif "gcp" in title_lower and "data" in title_lower and role == RoleCategory.GCP_DATA_ENGINEER:
                score += 16.0
            elif "data engineer" in title_lower and role == RoleCategory.DATA_ENGINEER and not ("ai" in title_lower or "genai" in title_lower):
                score += 14.0
            elif "genai" in title_lower and role == RoleCategory.GENAI_ENGINEER:
                score += 15.0
            elif "research scientist" in title_lower or "ai research" in title_lower:
                if role in (RoleCategory.DATA_SCIENTIST, RoleCategory.ML_ENGINEER):
                    score += 15.0

            # Special check for AI Data Engineer (needs explicit AI in title OR substantial AI in core responsibilities)
            if role == RoleCategory.AI_DATA_ENGINEER:
                has_ai_core = any(kw in f"{title_lower} {resp_text} {must_have_text}" for kw in ["rag", "llm", "agent", "genai", "vertex ai"])
                has_de_core = any(kw in f"{title_lower} {resp_text} {must_have_text}" for kw in ["etl", "pipeline", "bigquery", "airflow", "sql"])
                if "ai data engineer" in title_lower:
                    score += 20.0
                elif has_ai_core and has_de_core and any(w in title_lower for w in ["ai", "genai", "intelligent", "rag"]):
                    score += 10.0
                elif not (has_ai_core and has_de_core):
                    score = 0.0

            scores[role] = score

        # Sort candidate roles by score
        ranked_roles = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        primary_role = ranked_roles[0][0] if ranked_roles and ranked_roles[0][1] > 0 else RoleCategory.OTHER
        secondary_role = ranked_roles[1][0] if len(ranked_roles) > 1 and ranked_roles[1][1] > 2.0 else None

        seniority_info = SeniorityDetector.detect(jd)



        # Build explainable reasoning
        reasoning = (
            f"Analyzed {len(jd.responsibilities)} responsibilities and {len(jd.tech_stack)} technical items. "
            f"Primary role classified as '{primary_role.value}' based on core engineering duties "
            f"(Score: {scores.get(primary_role, 0.0):.1f}). "
            f"{'Secondary focus: ' + secondary_role.value if secondary_role else 'No strong secondary divergence'}."
        )

        return RoleClassification(
            primary_role=primary_role,
            secondary_role=secondary_role,
            role_family="Data & AI Engineering",
            seniority=seniority_info.detected_seniority,
            confidence=0.90 if scores.get(primary_role, 0) > 4.0 else 0.75,
            reasoning=reasoning,
        )


class RoleRealityAnalyzer:
    """
    Computes the practical day-to-day work distribution ("What will I ACTUALLY be doing?").
    """

    @classmethod
    def analyze(cls, jd: JobDescription, primary_role: RoleCategory) -> RoleReality:
        combined_text = f"{' '.join(jd.responsibilities)}\n{' '.join(jd.tech_stack)}".lower()

        # Count keyword occurrences for distribution estimation
        de_signals = sum(1 for w in ["etl", "pipeline", "bigquery", "airflow", "sql", "data quality", "spark", "warehouse", "schema"] if w in combined_text)
        genai_signals = sum(1 for w in ["rag", "llm", "agent", "genai", "prompt", "vector", "langchain", "vertex ai", "embeddings"] if w in combined_text)
        cloud_signals = sum(1 for w in ["gcp", "aws", "cloud storage", "pub/sub", "lambda", "functions", "s3", "docker", "kubernetes"] if w in combined_text)
        ml_signals = sum(1 for w in ["machine learning", "pytorch", "model training", "evaluation", "scikit-learn", "statistics"] if w in combined_text)
        analytics_signals = sum(1 for w in ["reporting", "dashboard", "tableau", "power bi", "analytics", "business stakeholders"] if w in combined_text)

        total_signals = de_signals + genai_signals + cloud_signals + ml_signals + analytics_signals
        if total_signals == 0:
            distribution = {"Data Engineering": 50.0, "GenAI / LLMs": 30.0, "Cloud & DevOps": 20.0}
        else:
            raw_de = (de_signals / total_signals) * 100
            raw_genai = (genai_signals / total_signals) * 100
            raw_cloud = (cloud_signals / total_signals) * 100
            raw_ml = (ml_signals / total_signals) * 100
            raw_analytics = (analytics_signals / total_signals) * 100

            # Normalize to 100%
            distribution = {
                "Data Engineering": round(max(5.0, raw_de), 1),
                "GenAI / RAG / Agents": round(max(5.0, raw_genai), 1),
                "Cloud & Backend Infrastructure": round(max(5.0, raw_cloud), 1),
            }
            if raw_ml > 5.0:
                distribution["ML & Analytics"] = round(raw_ml, 1)
            if raw_analytics > 5.0:
                distribution["BI & Reporting"] = round(raw_analytics, 1)

            # Re-scale to exactly 100%
            total = sum(distribution.values())
            distribution = {k: round((v / total) * 100, 1) for k, v in distribution.items()}

        sorted_types = sorted(distribution.items(), key=lambda x: x[1], reverse=True)
        primary_work = sorted_types[0][0]
        secondary_works = [x[0] for x in sorted_types[1:]]

        supporting_evidence = jd.responsibilities[:3] if jd.responsibilities else ["General engineering responsibilities"]

        return RoleReality(
            detected_role=primary_role,
            work_distribution=distribution,
            primary_work_type=primary_work,
            secondary_work_types=secondary_works,
            confidence=0.88,
            supporting_evidence=supporting_evidence,
            disclaimer="AI-derived interpretation based on responsibilities and technical requirements.",
        )


class SeniorityDetector:
    """
    Detects required seniority level based on explicit years, title, and leadership/architecture signals.
    """

    @classmethod
    def detect(cls, jd: JobDescription) -> SeniorityDetection:
        text = f"{jd.job_title}\n{jd.raw_text}".lower()

        # 1. Search for explicit numeric years in text
        years_match = re.search(r"(\b\d+(?:\.\d+)?|\d+\+)\s*(?:-|to)?\s*(?:\d+(?:\.\d+)?|\d+\+)?\s*(?:years?|yrs?)(?:\s+of\s+experience)?\b", text)
        explicit_years = None
        if years_match:
            nums = re.findall(r"\d+(?:\.\d+)?", years_match.group(0))
            if nums:
                explicit_years = float(nums[0])

        # 2. Check title and keywords
        title_lower = jd.job_title.lower()
        if any(w in title_lower for w in ["lead", "principal", "staff", "architect", "director"]):
            seniority = SeniorityLevel.LEAD
            reason = f"Title indicates leadership / architectural role ('{jd.job_title}')."
        elif any(w in title_lower for w in ["senior", "sr.", "sr "]) or (explicit_years and explicit_years >= 5.0):
            seniority = SeniorityLevel.SENIOR
            reason = f"Requires senior experience ({explicit_years or '5+'} years specified)."
        elif any(w in title_lower for w in ["junior", "associate", "entry", "0-2 years"]) or (explicit_years and explicit_years <= 2.0):
            seniority = SeniorityLevel.JUNIOR if (explicit_years and explicit_years > 0.5) else SeniorityLevel.ENTRY
            reason = f"Entry/Junior scope ({explicit_years or '0-2'} years required)."
        elif any(w in title_lower for w in ["intern", "internship"]):
            seniority = SeniorityLevel.INTERN
            reason = "Internship position."
        elif explicit_years and 2.0 <= explicit_years < 5.0:
            seniority = SeniorityLevel.MID
            reason = f"Mid-level scope ({explicit_years} years required)."
        else:
            seniority = SeniorityLevel.MID
            reason = "Standard mid-level engineering role requirements."

        return SeniorityDetection(
            detected_seniority=seniority,
            explicit_years_required=explicit_years,
            reasoning=reason,
            confidence=0.92 if explicit_years else 0.80,
        )
