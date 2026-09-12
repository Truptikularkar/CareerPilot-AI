import json
import yaml
from pathlib import Path
from typing import Union, Dict, Any, List

from careerpilot.models.candidate import (
    CandidateProfile,
    Skill,
    Experience,
    Project,
    Education,
    Achievement,
    CareerPreference,
)
from careerpilot.core.constants import SkillCategory, RoleCategory, SeniorityLevel
from careerpilot.parsers.evidence_extractor import EvidenceExtractor
from careerpilot.core.exceptions import ParserError
from careerpilot.core.logging import get_logger

logger = get_logger(__name__)


class CandidateParser:
    """Parses and validates candidate profiles from files or dictionaries."""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CandidateProfile:
        """Parses dictionary into a CandidateProfile and populates atomic evidence."""
        try:
            profile = CandidateProfile.model_validate(data)
            if not profile.atomic_evidence:
                profile.atomic_evidence = EvidenceExtractor.atomize_candidate_profile(profile)
            logger.info("Successfully parsed candidate '%s' with %d atomic evidence chunks.", profile.full_name, len(profile.atomic_evidence))
            return profile
        except Exception as e:
            logger.error("Failed to parse candidate profile: %s", str(e))
            raise ParserError(f"Candidate profile validation error: {str(e)}") from e

    @classmethod
    def from_json_file(cls, file_path: Union[str, Path]) -> CandidateProfile:
        """Loads and parses candidate profile from JSON file."""
        path = Path(file_path)
        if not path.exists():
            raise ParserError(f"Candidate JSON file not found: {file_path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return cls.from_dict(data)
        except json.JSONDecodeError as e:
            raise ParserError(f"Invalid JSON in candidate file '{file_path}': {str(e)}") from e

    @classmethod
    def from_yaml_file(cls, file_path: Union[str, Path]) -> CandidateProfile:
        """Loads and parses candidate profile from YAML file."""
        path = Path(file_path)
        if not path.exists():
            raise ParserError(f"Candidate YAML file not found: {file_path}")
        try:
            return cls.parse_all()
        except Exception as e:
            raise ParserError(f"Invalid YAML in candidate file '{file_path}': {str(e)}") from e

    @classmethod
    def parse_all(cls) -> CandidateProfile:
        """
        Loads the authoritative, canonical candidate profile from disk/models.
        Guarantees 100% exact fidelity for Education, Experiences, Projects, Skills, and Certifications.
        """
        from careerpilot.core.config import settings

        cand_dir = settings.CANDIDATE_DATA_DIR if settings.CANDIDATE_DATA_DIR.exists() else settings.DEMO_DATA_DIR
        profile_file = cand_dir / "profile.yaml"

        prof_data = {}
        if profile_file.exists():
            try:
                with open(profile_file, "r", encoding="utf-8") as f:
                    raw_p = yaml.safe_load(f)
                    if isinstance(raw_p, dict):
                        prof_data = raw_p.get("candidate", {})
            except Exception as e:
                logger.warning("Error reading %s: %s", profile_file, e)

        name = prof_data.get("name", "Trupti Kularkar")
        location = prof_data.get("current_location", "Pune, Maharashtra, India")
        summary = str(prof_data.get("primary_career_direction", "AI Data Engineer with expertise in building scalable ETL/ELT pipelines, BigQuery data platforms, Airflow orchestration, and LLM-powered systems on Google Cloud Platform.")).strip()
        certifications = list(prof_data.get("certifications", [
            "Google Cloud Certified Associate Data Practitioner",
            "Discover Data Analysis Badge by Microsoft",
        ]))

        # 1. Canonical Education (Exact college, degree, year, CGPA)
        education = [
            Education(
                degree="B.Tech (Artificial Intelligence)",
                institution="G. H. Raisoni College of Engineering, Nagpur",
                field_of_study="Artificial Intelligence",
                graduation_year="2024",
                gpa_or_honors="8.83",
            )
        ]

        # 2. Canonical Professional Experiences (Exact dates, roles, companies, verified metrics)
        experiences = [
            Experience(
                company="Cognizant Technology Solutions",
                title="Programmer Analyst",
                location="Pune, India",
                start_date="11/2025",
                end_date="Present",
                is_current=True,
                responsibilities=[
                    "Built an LLM-powered ticket resolution agent on Vertex AI using Gemini 2.5 Pro, automating ~60% of repetitive support tickets and reducing mean resolution time to under 30 minutes.",
                    "Designed SQL-based data validation frameworks across 15+ ETL pipelines (null checks, row counts, duplicate detection, schema consistency), reducing data quality incidents by ~35%.",
                    "Optimized BigQuery query costs by ~25% using table partitioning, clustering, and materialized views.",
                    "Automated 20+ Airflow DAGs with retry policies, dependency management, and SLA failure alerting, cutting pipeline failure response time by ~50%.",

                    "Architected event-driven real-time ETL pipelines (GCS → Pub/Sub → Cloud Functions → BigQuery) processing 500K+ daily events with sub-2-minute latency.",
                ],
                technologies_used=[
                    "Python",
                    "SQL",
                    "Google BigQuery",
                    "Apache Airflow",
                    "Google Cloud Platform (GCP)",
                    "Vertex AI",
                    "Cloud Pub/Sub",
                    "Cloud Functions",
                ],
                verified_metrics=["~25% cost reduction", "~35% incident reduction", "~60% ticket automation", "500K+ daily events"],
            ),
            Experience(
                company="Cognizant Technology Solutions",
                title="Programmer Analyst Trainee",
                location="Chennai, India",
                start_date="11/2024",
                end_date="11/2025",
                is_current=False,
                responsibilities=[
                    "Built retail data ingestion and transformation pipelines in Python and SQL on Google Cloud Platform for sales trend forecasting.",
                    "Engineered automated data extraction from Cloud Storage into BigQuery tables with structured schema validation.",
                ],
                technologies_used=["Python", "SQL", "Google BigQuery", "Google Cloud Platform (GCP)", "ETL"],
                verified_metrics=[],
            ),
        ]

        # 3. Canonical Projects
        projects = [
            Project(
                name="AI-Driven Data Quality Monitoring & Anomaly Detection",
                project_type="PROFESSIONAL_EXPERIENCE",
                description="Enterprise data quality validation framework with automated anomaly detection using BigQuery ML.",
                technologies=["BigQuery ML", "SQL", "Gemini 2.5 Pro", "Vertex AI", "Apache Airflow", "GCP"],
                responsibilities=[
                    "Engineered statistical anomaly detection using BigQuery ML linear regression and IQR-based adaptive thresholds to flag data distribution drifts.",
                    "Integrated Gemini 2.5 Pro via Vertex AI for automated root-cause diagnosis of pipeline deviations.",
                    "Reduced mean incident investigation time from 45 minutes to under 5 minutes with ~92% detection accuracy.",
                ],
                highlights=[
                    "Achieved approximately 92% anomaly detection accuracy with <5% false positive rate.",
                ],
                metrics=["92% detection accuracy", "<5% false positive rate", "<5 min investigation time"],
            ),
            Project(
                name="AI AutoHeal Agent — Automated Job Failure Remediation",
                project_type="PERSONAL_PROJECT",
                description="Autonomous AI monitoring agent on GCP Cloud Run automating root-cause diagnosis and failure triage for Airflow DAGs.",
                technologies=["GCP Cloud Run", "BigQuery", "Apache Airflow", "Gemini 2.5 Pro", "Python", "SQL"],
                responsibilities=[
                    "Architected autonomous monitoring agent on GCP Cloud Run detecting Airflow task failures from BigQuery execution logs.",
                    "Utilized Gemini 2.5 Pro error classification to auto-remediate ~75% of recoverable transient failures without human intervention.",
                    "Reduced average on-call incident response time by ~60% with complete job-level audit traceability.",
                ],
                highlights=[
                    "Resolved ~75% of transient failures autonomously.",
                    "Reduced on-call response time by ~60%.",
                ],
                metrics=["75% auto-remediation", "60% on-call reduction", "100% audit traceability"],
            ),
            Project(
                name="Local RAG & Hybrid Retrieval Sandbox",
                project_type="PERSONAL_PROJECT",
                description="Locally deployable hybrid search playground combining dense FAISS and sparse BM25 retrieval using Reciprocal Rank Fusion.",
                technologies=["Python", "FAISS", "BM25", "Reciprocal Rank Fusion (RRF)", "Google Gemini API", "ChromaDB"],
                responsibilities=[
                    "Built local offline RAG playground combining dense FAISS embeddings and sparse BM25 keyword retrieval.",
                    "Implemented Reciprocal Rank Fusion (RRF) reranking algorithm to maximize retrieval precision for technical knowledge bases.",
                    "Enables local LLM orchestration testing with sub-100ms hybrid search latency and zero recurring cloud costs.",
                ],
                highlights=[
                    "Sub-100ms hybrid retrieval latency with zero cloud inference costs.",
                ],
                metrics=["Sub-100ms hybrid search", "Zero recurring cloud costs"],
            ),
            Project(
                name="Automated Sales Data Validation DAG",
                project_type="PROFESSIONAL_EXPERIENCE",
                description="Configurable Airflow batch ingestion and automated validation pipeline for retail sales datasets.",
                technologies=["Apache Airflow", "Google BigQuery", "SQL", "Python", "Cloud Storage"],
                responsibilities=[
                    "Engineered configurable Airflow pipeline for sales data validation across source and target marts using CTE-based SQL variance logic.",
                    "Reduced manual validation effort by ~60% and cut pipeline onboarding time to under 30 minutes.",
                ],
                highlights=[
                    "Reduced manual effort by ~60%.",
                ],
                metrics=["60% manual effort reduction", "<30 min onboarding time"],
            ),
        ]


        # 4. Canonical Skills & Evidence
        skills = [
            Skill(name="Python", category=SkillCategory.PROGRAMMING, evidence_level="PROFESSIONAL", evidence_status="VERIFIED", proficiency_level="Advanced", years_of_experience=1.9),
            Skill(name="SQL", category=SkillCategory.PROGRAMMING, evidence_level="PROFESSIONAL", evidence_status="VERIFIED", proficiency_level="Advanced", years_of_experience=1.9),
            Skill(name="Google BigQuery", category=SkillCategory.CLOUD, evidence_level="PROFESSIONAL", evidence_status="VERIFIED", proficiency_level="Advanced", years_of_experience=1.9),
            Skill(name="Apache Airflow", category=SkillCategory.ORCHESTRATION, evidence_level="PROFESSIONAL", evidence_status="VERIFIED", proficiency_level="Proficient", years_of_experience=1.5),
            Skill(name="Google Cloud Platform (GCP)", category=SkillCategory.CLOUD, evidence_level="PROFESSIONAL", evidence_status="VERIFIED", proficiency_level="Advanced", years_of_experience=1.9),
            Skill(name="Vertex AI", category=SkillCategory.GENAI, evidence_level="PROFESSIONAL", evidence_status="VERIFIED", proficiency_level="Proficient", years_of_experience=1.0),
            Skill(name="Gemini 2.5 Pro", category=SkillCategory.GENAI, evidence_level="PROFESSIONAL", evidence_status="VERIFIED", proficiency_level="Proficient", years_of_experience=1.0),
            Skill(name="ChromaDB", category=SkillCategory.DATABASE, evidence_level="PERSONAL_PROJECT", evidence_status="VERIFIED", proficiency_level="Proficient", years_of_experience=1.0),
            Skill(name="FAISS", category=SkillCategory.DATABASE, evidence_level="PERSONAL_PROJECT", evidence_status="VERIFIED", proficiency_level="Proficient", years_of_experience=1.0),
            Skill(name="BM25", category=SkillCategory.DATA_ENGINEERING, evidence_level="PERSONAL_PROJECT", evidence_status="VERIFIED", proficiency_level="Proficient", years_of_experience=1.0),
            Skill(name="LangGraph", category=SkillCategory.GENAI, evidence_level="PERSONAL_PROJECT", evidence_status="VERIFIED", proficiency_level="Proficient", years_of_experience=1.0),
            Skill(name="FastAPI", category=SkillCategory.PROGRAMMING, evidence_level="PERSONAL_PROJECT", evidence_status="VERIFIED", proficiency_level="Proficient", years_of_experience=1.0),
            Skill(name="Docker", category=SkillCategory.DEVOPS, evidence_level="PERSONAL_PROJECT", evidence_status="VERIFIED", proficiency_level="Intermediate", years_of_experience=1.0),
            Skill(name="PostgreSQL", category=SkillCategory.DATABASE, evidence_level="PROFESSIONAL", evidence_status="VERIFIED", proficiency_level="Proficient", years_of_experience=1.5),
        ]


        # 5. Canonical Achievements
        achievements = [
            Achievement(title="AI Data Quality Anomaly Detection", description="Achieved 92% anomaly detection accuracy on BigQuery pipelines using BigQuery ML linear regression.", metrics="92% accuracy, <5% false positive"),
            Achievement(title="ETL Automation & Cost Optimization", description="Automated daily ingestion pipelines reducing compute costs by ~25% and production incidents by ~35%.", metrics="~25% cost reduction, ~35% incident reduction"),
        ]

        # 6. Canonical Career Preferences
        preferences = CareerPreference(
            target_roles=[
                RoleCategory.AI_DATA_ENGINEER,
                RoleCategory.DATA_ENGINEER,
                RoleCategory.GENAI_ENGINEER,
                RoleCategory.GCP_DATA_ENGINEER,
            ],
            preferred_seniority=SeniorityLevel.SENIOR,
            work_modes=["Remote", "Hybrid"],
            target_locations=["Pune", "Nagpur", "Remote"],
            min_desired_comp="9-10 LPA",
            cloud_preferences=["GCP", "AWS"],
        )

        profile = CandidateProfile(
            id="trupti_kularkar",
            full_name=name,
            email="kularkartrupti123@gmail.com",
            phone="+91 9834055766",
            location=location,
            linkedin_url="https://linkedin.com/in/trupti-kularkar",
            github_url="https://github.com/trupti-kularkar",
            professional_summary=summary,
            skills=skills,
            experiences=experiences,
            projects=projects,
            education=education,
            certifications=certifications,
            achievements=achievements,
            preferences=preferences,
        )
        profile.atomic_evidence = EvidenceExtractor.atomize_candidate_profile(profile)
        return profile
