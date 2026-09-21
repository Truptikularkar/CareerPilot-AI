import re
from pathlib import Path
from typing import Union, List, Dict, Any, Optional, Tuple
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
    Preserves requirement nuance, normalizes whitespace, extracts location and work mode, and excludes boilerplate.
    """

    # Comprehensive normalized skill dictionary mapping aliases to standardized names and taxonomy categories
    SKILL_TAXONOMY_MAP: Dict[str, Dict[str, Any]] = {
        # Programming & Frameworks
        "python": {"name": "Python", "category": TaxonomyCategory.PROGRAMMING},
        "sql": {"name": "SQL", "category": TaxonomyCategory.DATABASE},
        "fastapi": {"name": "FastAPI", "category": TaxonomyCategory.PROGRAMMING},
        "rest api": {"name": "RESTful APIs", "category": TaxonomyCategory.PROGRAMMING},
        "rest apis": {"name": "RESTful APIs", "category": TaxonomyCategory.PROGRAMMING},
        "restful api": {"name": "RESTful APIs", "category": TaxonomyCategory.PROGRAMMING},
        "api": {"name": "RESTful APIs", "category": TaxonomyCategory.PROGRAMMING},
        "apis": {"name": "RESTful APIs", "category": TaxonomyCategory.PROGRAMMING},

        # Databases & Warehouses
        "bigquery": {"name": "BigQuery", "category": TaxonomyCategory.DATABASE},
        "postgresql": {"name": "PostgreSQL", "category": TaxonomyCategory.DATABASE},
        "postgres": {"name": "PostgreSQL", "category": TaxonomyCategory.DATABASE},
        "mysql": {"name": "MySQL", "category": TaxonomyCategory.DATABASE},
        "redshift": {"name": "Amazon Redshift", "category": TaxonomyCategory.DATABASE},
        "snowflake": {"name": "Snowflake", "category": TaxonomyCategory.DATABASE},
        "sql optimization": {"name": "SQL Query Optimization", "category": TaxonomyCategory.DATABASE},
        "sql tuning": {"name": "SQL Query Optimization", "category": TaxonomyCategory.DATABASE},

        # Cloud Platforms & Services
        "gcp": {"name": "Google Cloud Platform (GCP)", "category": TaxonomyCategory.CLOUD},
        "google cloud": {"name": "Google Cloud Platform (GCP)", "category": TaxonomyCategory.CLOUD},
        "aws": {"name": "Amazon Web Services (AWS)", "category": TaxonomyCategory.CLOUD},
        "azure": {"name": "Microsoft Azure", "category": TaxonomyCategory.CLOUD},
        "cloud": {"name": "Cloud Computing", "category": TaxonomyCategory.CLOUD},
        "lambda": {"name": "AWS Lambda", "category": TaxonomyCategory.CLOUD},
        "cloud functions": {"name": "Google Cloud Functions", "category": TaxonomyCategory.CLOUD},
        "cloud run": {"name": "Google Cloud Run", "category": TaxonomyCategory.CLOUD},
        "pub/sub": {"name": "Google Cloud Pub/Sub", "category": TaxonomyCategory.CLOUD},
        "pubsub": {"name": "Google Cloud Pub/Sub", "category": TaxonomyCategory.CLOUD},
        "cloud storage": {"name": "Google Cloud Storage (GCS)", "category": TaxonomyCategory.CLOUD},
        "gcs": {"name": "Google Cloud Storage (GCS)", "category": TaxonomyCategory.CLOUD},
        "s3": {"name": "Amazon S3", "category": TaxonomyCategory.CLOUD},

        # GenAI & LLMs
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
        "generative ai": {"name": "Generative AI & LLMs", "category": TaxonomyCategory.GENAI},
        "genai": {"name": "Generative AI & LLMs", "category": TaxonomyCategory.GENAI},
        "gen ai": {"name": "Generative AI & LLMs", "category": TaxonomyCategory.GENAI},
        "prompt engineering": {"name": "Prompt Engineering", "category": TaxonomyCategory.GENAI},
        "agentic": {"name": "AI Agents", "category": TaxonomyCategory.GENAI},
        "ai agent": {"name": "AI Agents", "category": TaxonomyCategory.GENAI},
        "ai agents": {"name": "AI Agents", "category": TaxonomyCategory.GENAI},
        "vector database": {"name": "Vector Databases", "category": TaxonomyCategory.GENAI},
        "vector databases": {"name": "Vector Databases", "category": TaxonomyCategory.GENAI},
        "chromadb": {"name": "ChromaDB", "category": TaxonomyCategory.GENAI},
        "chroma": {"name": "ChromaDB", "category": TaxonomyCategory.GENAI},
        "pinecone": {"name": "Pinecone", "category": TaxonomyCategory.GENAI},
        "hugging face": {"name": "Hugging Face", "category": TaxonomyCategory.GENAI},
        "huggingface": {"name": "Hugging Face", "category": TaxonomyCategory.GENAI},
        "transformers": {"name": "Transformers", "category": TaxonomyCategory.GENAI},
        "nlp": {"name": "Natural Language Processing (NLP)", "category": TaxonomyCategory.GENAI},
        "natural language processing": {"name": "Natural Language Processing (NLP)", "category": TaxonomyCategory.GENAI},

        # Machine Learning & Deep Learning
        "machine learning": {"name": "Machine Learning", "category": TaxonomyCategory.MACHINE_LEARNING},
        "ml": {"name": "Machine Learning", "category": TaxonomyCategory.MACHINE_LEARNING},
        "deep learning": {"name": "Deep Learning", "category": TaxonomyCategory.MACHINE_LEARNING},
        "scikit-learn": {"name": "Scikit-Learn", "category": TaxonomyCategory.MACHINE_LEARNING},
        "sklearn": {"name": "Scikit-Learn", "category": TaxonomyCategory.MACHINE_LEARNING},
        "pytorch": {"name": "PyTorch", "category": TaxonomyCategory.MACHINE_LEARNING},
        "tensorflow": {"name": "TensorFlow", "category": TaxonomyCategory.MACHINE_LEARNING},
        "keras": {"name": "Keras", "category": TaxonomyCategory.MACHINE_LEARNING},
        "bigquery ml": {"name": "BigQuery ML", "category": TaxonomyCategory.MACHINE_LEARNING},
        "bqml": {"name": "BigQuery ML", "category": TaxonomyCategory.MACHINE_LEARNING},

        # Data Engineering & Orchestration
        "airflow": {"name": "Apache Airflow", "category": TaxonomyCategory.ORCHESTRATION},
        "apache airflow": {"name": "Apache Airflow", "category": TaxonomyCategory.ORCHESTRATION},
        "etl": {"name": "ETL / ELT Pipelines", "category": TaxonomyCategory.DATA_ENGINEERING},
        "elt": {"name": "ETL / ELT Pipelines", "category": TaxonomyCategory.DATA_ENGINEERING},
        "data engineering": {"name": "Data Engineering", "category": TaxonomyCategory.DATA_ENGINEERING},
        "data pipeline": {"name": "Data Pipelines", "category": TaxonomyCategory.DATA_ENGINEERING},
        "data pipelines": {"name": "Data Pipelines", "category": TaxonomyCategory.DATA_ENGINEERING},
        "data modeling": {"name": "Data Modeling", "category": TaxonomyCategory.DATA_ENGINEERING},
        "data quality": {"name": "Data Quality Frameworks", "category": TaxonomyCategory.DATA_QUALITY},
        "data validation": {"name": "Data Validation", "category": TaxonomyCategory.DATA_QUALITY},
        "anomaly detection": {"name": "Anomaly Detection", "category": TaxonomyCategory.DATA_QUALITY},
        "spark": {"name": "Apache Spark", "category": TaxonomyCategory.DATA_ENGINEERING},
        "pyspark": {"name": "Apache Spark", "category": TaxonomyCategory.DATA_ENGINEERING},
        "apache spark": {"name": "Apache Spark", "category": TaxonomyCategory.DATA_ENGINEERING},
        "glue": {"name": "AWS Glue", "category": TaxonomyCategory.DATA_ENGINEERING},
        "emr": {"name": "AWS EMR", "category": TaxonomyCategory.DATA_ENGINEERING},
        "pandas": {"name": "Pandas", "category": TaxonomyCategory.DATA_ENGINEERING},
        "numpy": {"name": "NumPy", "category": TaxonomyCategory.DATA_ENGINEERING},
        "dbt": {"name": "dbt", "category": TaxonomyCategory.DATA_ENGINEERING},

        # DevOps & System Design
        "docker": {"name": "Docker", "category": TaxonomyCategory.DEVOPS},
        "kubernetes": {"name": "Kubernetes", "category": TaxonomyCategory.DEVOPS},
        "k8s": {"name": "Kubernetes", "category": TaxonomyCategory.DEVOPS},
        "git": {"name": "Git", "category": TaxonomyCategory.DEVOPS},
        "github": {"name": "GitHub", "category": TaxonomyCategory.DEVOPS},
        "ci/cd": {"name": "CI/CD", "category": TaxonomyCategory.DEVOPS},
        "system design": {"name": "System Design & Architecture", "category": TaxonomyCategory.SYSTEM_DESIGN},
    }

    YEARS_PATTERN = re.compile(
        r"(\b(?:\d+(?:\.\d+)?|\d+\+)\s*(?:-|to)?\s*(?:\d+(?:\.\d+)?|\d+\+)?\s*(?:years?|yrs?)(?:\s+of\s+experience)?\b)",
        re.IGNORECASE,
    )

    LOCATION_LINE_PATTERN = re.compile(
        r"(?i)^\s*(?:job\s+)?(?:location|work\s+location|base\s+location|office\s+location)\s*[:\-–]\s*(.+)$",
    )
    WORK_MODE_PATTERN = re.compile(
        r"(?i)^\s*(?:work\s+mode|job\s+type|workplace\s+type|employment\s+type)\s*[:\-–]\s*(.+)$",
    )

    @classmethod
    def is_location_line(cls, line: str) -> bool:
        """Determines if a line describes location or work mode metadata instead of a skill."""
        line_clean = line.strip().lower()
        if not line_clean:
            return False
        if cls.LOCATION_LINE_PATTERN.match(line) or cls.WORK_MODE_PATTERN.match(line):
            return True
        if line_clean.startswith(("location:", "location -", "work location:", "location;")):
            return True
        # Standalone city/mode lines (e.g., 'Pune, India', 'Remote', 'Pune, Maharashtra')
        common_locations = {
            "pune", "pune, india", "pune, maharashtra", "pune, maharashtra, india",
            "nagpur", "bangalore", "bengaluru", "hyderabad", "chennai", "mumbai",
            "delhi", "gurgaon", "gurugram", "noida", "remote", "hybrid", "on-site",
            "onsite", "work from home", "remote / flexible",
        }
        if line_clean in common_locations:
            return True
        return False

    @classmethod
    def is_boilerplate_or_marketing_line(cls, line: str) -> bool:
        """
        Determines whether a line is marketing copy, an HR slogan, equal opportunity notice,
        benefits blurb, or conversational question rather than an actual technical qualification.
        """
        line_clean = line.strip().lower()
        if not line_clean or len(line_clean) < 3:
            return True

        # Questions or conversational prompts
        if line_clean.endswith("?") or line_clean.startswith((
            "why ", "how ", "what if", "want to ", "are you ", "do you want ", "tell us ", "let us ", "looking for a "
        )):
            return True

        # Marketing slogans, company blurbs, and HR filler
        marketing_keywords = [
            "want to change the world",
            "tell us about",
            "let us know",
            "join our team",
            "join us",
            "about us",
            "who we are",
            "what we do",
            "our mission",
            "our vision",
            "equal opportunity",
            "we are an equal",
            "affirmative action",
            "race, color",
            "religion, sex",
            "sexual orientation",
            "disability",
            "veteran status",
            "all qualified applicants",
            "diversity and inclusion",
            "diversity, equity",
            "benefits and perks",
            "what we offer",
            "we offer:",
            "perks:",
            "how to apply",
            "click here",
            "apply now",
            "please submit",
            "send your resume",
            "competitive salary",
            "health insurance",
            "401(k)",
            "paid time off",
            "work-life balance",
            "terms of employment",
            "disclaimer",
            "privacy policy",
            "about the company",
            "about the role",
            "role summary",
        ]
        if any(kw in line_clean for kw in marketing_keywords):
            return True

        return False

    @classmethod
    def extract_location_and_mode(cls, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Extracts location and work mode from job description text."""
        location = None
        work_mode = None

        for line in text.splitlines():
            line_str = line.strip()
            loc_match = cls.LOCATION_LINE_PATTERN.match(line_str)
            if loc_match and not location:
                loc_val = loc_match.group(1).strip()
                if "hybrid" in loc_val.lower():
                    work_mode = "Hybrid"
                    cleaned_loc = re.sub(r"(?i)\(hybrid\)|hybrid", "", loc_val).strip(" ,-–")
                    loc_val = cleaned_loc if cleaned_loc else "Hybrid"
                elif "remote" in loc_val.lower():
                    work_mode = "Remote"
                    cleaned_loc = re.sub(r"(?i)\(remote\)|remote", "", loc_val).strip(" ,-–")
                    loc_val = cleaned_loc if cleaned_loc else "Remote"
                elif "onsite" in loc_val.lower() or "on-site" in loc_val.lower():
                    work_mode = "Onsite"
                    cleaned_loc = re.sub(r"(?i)\(onsite\)|onsite|\(on-site\)|on-site", "", loc_val).strip(" ,-–")
                    loc_val = cleaned_loc if cleaned_loc else "Onsite"
                location = loc_val

            mode_match = cls.WORK_MODE_PATTERN.match(line_str)
            if mode_match and not work_mode:
                work_mode = mode_match.group(1).strip()

        # Fallback check across full text for common cities if not found in explicit header
        if not location:
            text_lower = text.lower()
            for city in ["pune", "nagpur", "bangalore", "bengaluru", "hyderabad", "chennai", "mumbai", "delhi", "gurgaon", "gurugram", "noida"]:
                if re.search(rf"\b{city}\b", text_lower):
                    location = city.title()
                    break

        if not work_mode:
            text_lower = text.lower()
            if "hybrid" in text_lower:
                work_mode = "Hybrid"
            elif "remote" in text_lower:
                work_mode = "Remote"
            elif "onsite" in text_lower or "on-site" in text_lower:
                work_mode = "Onsite"

        return location, work_mode

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

            # Skip location metadata and marketing boilerplate from requirement sections
            if cls.is_location_line(line) or cls.is_boilerplate_or_marketing_line(line):
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
            if cls.is_location_line(line) or cls.is_boilerplate_or_marketing_line(line):
                return
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

            # If no specific tech was matched, check if it's a soft skill or valid non-tech qualification
            if not found_tech and len(line) > 10:
                is_soft_skill = any(w in line_lower for w in ["communication", "collaboration", "team", "agile", "leadership", "problem-solving", "analytical"])
                # NEVER assign MUST_HAVE to arbitrary unparsed text that might be company blurb!
                # Only recognized soft skills become NICE_TO_HAVE, preserving candidate score integrity.
                if is_soft_skill:
                    norm_label = line[:40].strip()
                    req_key = f"{norm_label}_{RequirementImportance.NICE_TO_HAVE.value}"
                    if req_key not in seen_skills:
                        seen_skills.add(req_key)
                        requirements.append(
                            JobRequirement(
                                skill_name=norm_label,
                                normalized_skill=norm_label,
                                category=TaxonomyCategory.SOFT_SKILL,
                                importance=RequirementImportance.NICE_TO_HAVE,
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
        location: Optional[str] = None,
        work_mode: Optional[str] = None,
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

        # Extract location and work mode if not explicitly provided
        extracted_location, extracted_work_mode = cls.extract_location_and_mode(clean_text)
        final_location = location or extracted_location
        final_work_mode = work_mode or extracted_work_mode

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
            location=final_location,
            work_mode=final_work_mode,
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
    def parse_file(
        cls,
        file_path: Union[str, Path],
        company_name: Optional[str] = None,
        job_title: Optional[str] = None,
        location: Optional[str] = None,
        work_mode: Optional[str] = None,
    ) -> JobDescription:
        """Parses a job description from a file (.txt, .md, .pdf)."""
        path = Path(file_path)
        if not path.exists():
            raise ParserError(f"Job description file not found: {file_path}")

        if path.suffix.lower() == ".pdf":
            raw_text = cls.extract_text_from_pdf(path)
        else:
            with open(path, "r", encoding="utf-8") as f:
                raw_text = f.read()

        return cls.parse_raw_text(
            raw_text,
            company_name=company_name,
            job_title=job_title,
            location=location,
            work_mode=work_mode,
        )
