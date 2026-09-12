import re
from pathlib import Path
from typing import Union, List, Dict, Any, Optional
import pymupdf

from careerpilot.core.constants import (
    SeniorityLevel,
    RoleCategory,
    RequirementImportance,
    TaxonomyCategory,
)
from careerpilot.models.job import JobDescription, JobRequirement
from careerpilot.core.exceptions import ParserError
from careerpilot.core.logging import get_logger

logger = get_logger(__name__)


class JobDescriptionParser:
    """
    Parses unstructured Job Description inputs (text, TXT file, PDF file) into structured JobDescription models.
    Preserves requirement nuance, normalizes whitespace, and extracts explicit years and categories.
    """

    # Comprehensive normalized skill dictionary mapping aliases to standardized names and taxonomy categories
    SKILL_TAXONOMY_MAP: Dict[str, Dict[str, Any]] = {
        "python": {"name": "Python", "category": TaxonomyCategory.PROGRAMMING},
        "sql": {"name": "SQL", "category": TaxonomyCategory.DATABASE},
        "bigquery": {"name": "BigQuery", "category": TaxonomyCategory.DATABASE},
        "postgresql": {"name": "PostgreSQL", "category": TaxonomyCategory.DATABASE},
        "postgres": {"name": "PostgreSQL", "category": TaxonomyCategory.DATABASE},
        "mysql": {"name": "MySQL", "category": TaxonomyCategory.DATABASE},
        "redshift": {"name": "Amazon Redshift", "category": TaxonomyCategory.DATABASE},
        "snowflake": {"name": "Snowflake", "category": TaxonomyCategory.DATABASE},
        "gcp": {"name": "Google Cloud Platform (GCP)", "category": TaxonomyCategory.CLOUD},
        "google cloud": {"name": "Google Cloud Platform (GCP)", "category": TaxonomyCategory.CLOUD},
        "aws": {"name": "Amazon Web Services (AWS)", "category": TaxonomyCategory.CLOUD},
        "azure": {"name": "Microsoft Azure", "category": TaxonomyCategory.CLOUD},
        "vertex ai": {"name": "Vertex AI", "category": TaxonomyCategory.GENAI},
        "gemini": {"name": "Gemini API", "category": TaxonomyCategory.GENAI},
        "rag": {"name": "RAG (Retrieval-Augmented Generation)", "category": TaxonomyCategory.GENAI},
        "retrieval-augmented generation": {"name": "RAG (Retrieval-Augmented Generation)", "category": TaxonomyCategory.GENAI},
        "hybrid retrieval": {"name": "Hybrid Retrieval (Dense + Sparse)", "category": TaxonomyCategory.GENAI},
        "langchain": {"name": "LangChain", "category": TaxonomyCategory.GENAI},
        "langgraph": {"name": "LangGraph", "category": TaxonomyCategory.GENAI},
        "faiss": {"name": "FAISS", "category": TaxonomyCategory.GENAI},
        "bm25": {"name": "BM25", "category": TaxonomyCategory.GENAI},
        "reciprocal rank fusion": {"name": "Reciprocal Rank Fusion (RRF)", "category": TaxonomyCategory.GENAI},
        "rrf": {"name": "Reciprocal Rank Fusion (RRF)", "category": TaxonomyCategory.GENAI},
        "llm": {"name": "LLM Orchestration", "category": TaxonomyCategory.GENAI},
        "llms": {"name": "LLM Orchestration", "category": TaxonomyCategory.GENAI},
        "agentic": {"name": "AI Agents", "category": TaxonomyCategory.GENAI},
        "ai agent": {"name": "AI Agents", "category": TaxonomyCategory.GENAI},
        "airflow": {"name": "Apache Airflow", "category": TaxonomyCategory.ORCHESTRATION},
        "apache airflow": {"name": "Apache Airflow", "category": TaxonomyCategory.ORCHESTRATION},
        "etl": {"name": "ETL / ELT Pipelines", "category": TaxonomyCategory.DATA_ENGINEERING},
        "elt": {"name": "ETL / ELT Pipelines", "category": TaxonomyCategory.DATA_ENGINEERING},
        "data engineering": {"name": "Data Engineering", "category": TaxonomyCategory.DATA_ENGINEERING},
        "data pipeline": {"name": "Data Pipelines", "category": TaxonomyCategory.DATA_ENGINEERING},
        "data quality": {"name": "Data Quality Frameworks", "category": TaxonomyCategory.DATA_QUALITY},
        "data validation": {"name": "Data Validation", "category": TaxonomyCategory.DATA_QUALITY},
        "anomaly detection": {"name": "Anomaly Detection", "category": TaxonomyCategory.DATA_QUALITY},
        "spark": {"name": "Apache Spark", "category": TaxonomyCategory.DATA_ENGINEERING},
        "pyspark": {"name": "Apache Spark", "category": TaxonomyCategory.DATA_ENGINEERING},
        "apache spark": {"name": "Apache Spark", "category": TaxonomyCategory.DATA_ENGINEERING},
        "glue": {"name": "AWS Glue", "category": TaxonomyCategory.DATA_ENGINEERING},
        "emr": {"name": "AWS EMR", "category": TaxonomyCategory.DATA_ENGINEERING},
        "lambda": {"name": "AWS Lambda", "category": TaxonomyCategory.CLOUD},
        "cloud functions": {"name": "Google Cloud Functions", "category": TaxonomyCategory.CLOUD},
        "cloud run": {"name": "Google Cloud Run", "category": TaxonomyCategory.CLOUD},
        "pub/sub": {"name": "Google Cloud Pub/Sub", "category": TaxonomyCategory.CLOUD},
        "pubsub": {"name": "Google Cloud Pub/Sub", "category": TaxonomyCategory.CLOUD},
        "cloud storage": {"name": "Google Cloud Storage (GCS)", "category": TaxonomyCategory.CLOUD},
        "gcs": {"name": "Google Cloud Storage (GCS)", "category": TaxonomyCategory.CLOUD},
        "s3": {"name": "Amazon S3", "category": TaxonomyCategory.CLOUD},
        "docker": {"name": "Docker", "category": TaxonomyCategory.DEVOPS},
        "kubernetes": {"name": "Kubernetes", "category": TaxonomyCategory.DEVOPS},
        "k8s": {"name": "Kubernetes", "category": TaxonomyCategory.DEVOPS},
        "fastapi": {"name": "FastAPI", "category": TaxonomyCategory.PROGRAMMING},
        "machine learning": {"name": "Machine Learning", "category": TaxonomyCategory.MACHINE_LEARNING},
        "system design": {"name": "System Design & Architecture", "category": TaxonomyCategory.SYSTEM_DESIGN},
    }

    YEARS_PATTERN = re.compile(
        r"(\b(?:\d+(?:\.\d+)?|\d+\+)\s*(?:-|to)?\s*(?:\d+(?:\.\d+)?|\d+\+)?\s*(?:years?|yrs?)(?:\s+of\s+experience)?\b)",
        re.IGNORECASE,
    )

    @classmethod
    def extract_text_from_pdf(cls, pdf_path: Union[str, Path]) -> str:
        """Extracts plain text from PDF using PyMuPDF."""
        path = Path(pdf_path)
        if not path.exists():
            raise ParserError(f"PDF file not found: {pdf_path}")
        try:
            doc = pymupdf.open(str(path))
            text = "\n".join(page.get_text() for page in doc)
            doc.close()
            return text
        except Exception as e:
            raise ParserError(f"Failed to extract text from PDF '{pdf_path}': {e}") from e

    @classmethod
    def normalize_text(cls, text: str) -> str:
        """Cleans excessive whitespace while preserving semantic newlines and bullet points."""
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        lines = [line.strip() for line in text.split("\n")]
        # Keep non-empty lines
        return "\n".join(line for line in lines if line)

    @classmethod
    def extract_years_required(cls, text: str) -> Optional[float]:
        """Extracts the minimum numeric years of experience required from a string."""
        match = cls.YEARS_PATTERN.search(text)
        if match:
            # Extract first numeric value
            nums = re.findall(r"\d+(?:\.\d+)?", match.group(0))
            if nums:
                return float(nums[0])
        return None

    @classmethod
    def parse_sections(cls, text: str) -> Dict[str, List[str]]:
        """Segregates text into responsibilities, must-haves, nice-to-haves, and general sections."""
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        sections: Dict[str, List[str]] = {
            "summary": [],
            "responsibilities": [],
            "must_have": [],
            "nice_to_have": [],
        }

        current_sec = "summary"
        for line in lines:
            line_lower = line.lower()
            if any(h in line_lower for h in ["responsibilities", "what you'll do", "key responsibilities", "duties", "what you will do", "role overview"]):
                current_sec = "responsibilities"
                continue
            elif any(h in line_lower for h in ["preferred", "nice to have", "bonus", "desirable", "good to have", "plus"]):
                current_sec = "nice_to_have"
                continue
            elif any(h in line_lower for h in ["required skills", "requirements", "must have", "qualifications", "minimum qualifications", "what we look for", "basic qualifications"]):
                current_sec = "must_have"
                continue


            # Strip standard bullet characters
            clean_line = re.sub(r"^[\*\-\•\d\.\)]+\s*", "", line).strip()
            if clean_line and len(clean_line) > 3:
                sections[current_sec].append(clean_line)

        return sections

    @classmethod
    def extract_structured_requirements(
        cls,
        must_have_lines: List[str],
        nice_to_have_lines: List[str],
        full_text: str,
    ) -> List[JobRequirement]:
        """Extracts categorized, normalized JobRequirement instances."""
        requirements: List[JobRequirement] = []
        seen_skills = set()

        def process_line(line: str, importance: RequirementImportance):
            line_lower = line.lower()
            years = cls.extract_years_required(line)
            found_tech = False

            for alias, info in cls.SKILL_TAXONOMY_MAP.items():
                pattern = rf"\b{re.escape(alias)}\b"
                if re.search(pattern, line_lower):
                    found_tech = True
                    norm_name = info["name"]
                    category = info["category"]
                    req_key = f"{norm_name}_{importance.value}"
                    if req_key not in seen_skills:
                        seen_skills.add(req_key)
                        requirements.append(
                            JobRequirement(
                                skill_name=alias.title(),
                                normalized_skill=norm_name,
                                category=category,
                                importance=importance,
                                years_required=years,
                                source_text=line,
                                evidence_expected=f"Verified experience in {norm_name}",
                            )
                        )

            # If no specific tech was matched but it is an explicit qualification line
            if not found_tech and len(line) > 10:
                cat = TaxonomyCategory.SOFT_SKILL if any(w in line_lower for w in ["communication", "collaboration", "team", "agile", "leadership"]) else TaxonomyCategory.OTHER
                requirements.append(
                    JobRequirement(
                        skill_name=line[:40],
                        normalized_skill=line[:50],
                        category=cat,
                        importance=importance,
                        years_required=years,
                        source_text=line,
                    )
                )

        for line in must_have_lines:
            process_line(line, RequirementImportance.MUST_HAVE)

        for line in nice_to_have_lines:
            process_line(line, RequirementImportance.NICE_TO_HAVE)

        # If no requirements were explicitly split by headers, scan full text
        if not requirements:
            for line in full_text.splitlines():
                if len(line.strip()) > 5:
                    process_line(line.strip(), RequirementImportance.MUST_HAVE)

        return requirements

    @classmethod
    def parse_raw_text(
        cls,
        text: str,
        company_name: Optional[str] = None,
        job_title: Optional[str] = None,
    ) -> JobDescription:
        """Parses normalized text into structured JobDescription."""
        if not text or not text.strip():
            raise ParserError("Cannot parse empty job description.")

        clean_text = cls.normalize_text(text)
        lines = clean_text.splitlines()

        # Extract title if not provided
        if not job_title:
            for line in lines[:6]:
                if "job title:" in line.lower() or "title:" in line.lower() or "role:" in line.lower():
                    job_title = re.sub(r"(?i)(job title|title|role):\s*", "", line).strip()
                    break
            if not job_title and lines:
                job_title = lines[0]

        # Extract company if not provided
        if not company_name:
            for line in lines[:6]:
                if "company:" in line.lower() or "organization:" in line.lower():
                    company_name = re.sub(r"(?i)(company|organization):\s*", "", line).strip()
                    break
            if not company_name:
                company_name = "Target Company"

        sections = cls.parse_sections(clean_text)
        requirements = cls.extract_structured_requirements(
            sections.get("must_have", []),
            sections.get("nice_to_have", []),
            clean_text,
        )

        must_have_skills = [r.normalized_skill for r in requirements if r.importance == RequirementImportance.MUST_HAVE]
        nice_to_have_skills = [r.normalized_skill for r in requirements if r.importance == RequirementImportance.NICE_TO_HAVE]
        all_tech = list(dict.fromkeys(r.normalized_skill for r in requirements))

        # Quick role inference
        extracted_role = RoleCategory.OTHER
        title_lower = (job_title or "").lower()
        if "ai data engineer" in title_lower:
            extracted_role = RoleCategory.AI_DATA_ENGINEER
        elif "genai" in title_lower or "gen ai" in title_lower:
            extracted_role = RoleCategory.GENAI_ENGINEER
        elif "ai engineer" in title_lower or "ai / genai" in title_lower:
            extracted_role = RoleCategory.AI_ENGINEER
        elif "gcp" in title_lower and "data" in title_lower:
            extracted_role = RoleCategory.GCP_DATA_ENGINEER
        elif "data engineer" in title_lower:
            extracted_role = RoleCategory.DATA_ENGINEER
        elif "data scientist" in title_lower:
            extracted_role = RoleCategory.DATA_SCIENTIST
        elif "ml" in title_lower or "machine learning" in title_lower:
            extracted_role = RoleCategory.ML_ENGINEER

        # Quick seniority inference
        if any(w in title_lower for w in ["lead", "principal", "staff"]):
            estimated_seniority = SeniorityLevel.LEAD
        elif any(w in title_lower for w in ["senior", "sr.", "sr "]):
            estimated_seniority = SeniorityLevel.SENIOR
        elif any(w in title_lower for w in ["junior", "associate", "entry"]):
            estimated_seniority = SeniorityLevel.JUNIOR
        else:
            estimated_seniority = SeniorityLevel.MID

        return JobDescription(
            raw_text=clean_text,
            company_name=company_name,
            job_title=job_title or "Target Role",
            extracted_role=extracted_role,
            estimated_seniority=estimated_seniority,
            summary=" ".join(sections.get("summary", [])) or clean_text[:300],
            responsibilities=sections.get("responsibilities", []),
            must_have_skills=must_have_skills,
            nice_to_have_skills=nice_to_have_skills,
            tech_stack=all_tech,
            requirements=requirements,
        )


    @classmethod
    def parse_file(cls, file_path: Union[str, Path]) -> JobDescription:
        """Parses a job description from a file (.txt, .md, .pdf)."""
        path = Path(file_path)
        if not path.exists():
            raise ParserError(f"Job description file not found: {file_path}")

        if path.suffix.lower() == ".pdf":
            raw_text = cls.extract_text_from_pdf(path)
        else:
            with open(path, "r", encoding="utf-8") as f:
                raw_text = f.read()

        return cls.parse_raw_text(raw_text)
