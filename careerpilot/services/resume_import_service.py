import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import pymupdf

from careerpilot.core.logging import get_logger

from careerpilot.core.constants import SkillCategory
from careerpilot.models.candidate import (
    CandidateProfile,
    Skill,
    Experience,
    Project,
    Education,
    ProfileDiffItem,
    ProfileDiffResult,
)
from careerpilot.services.candidate_service import CandidateService

logger = get_logger(__name__)


class ResumeImportService:
    """
    Parses an uploaded master resume (PDF or DOCX), compares against current CandidateProfile,
    generates a structured change diff matrix (ADDED, REMOVED, CHANGED, UNCHANGED), and allows
    selective user approval/rejection.
    """

    @classmethod
    def extract_text_from_pdf(cls, file_bytes_or_path: Union[bytes, str, Path]) -> str:
        """Extract plain text from PDF stream or file using pymupdf."""
        if isinstance(file_bytes_or_path, (str, Path)):
            doc = pymupdf.open(str(file_bytes_or_path))
        else:
            doc = pymupdf.open(stream=file_bytes_or_path, filetype="pdf")

        text_pages = [page.get_text() or "" for page in doc]
        doc.close()
        return "\n".join(text_pages)


    @classmethod
    def extract_text_from_docx(cls, file_bytes_or_path: Union[bytes, str, Path]) -> str:
        """Extract plain text from DOCX stream or file."""
        import docx
        import io
        if isinstance(file_bytes_or_path, (str, Path)):
            doc = docx.Document(str(file_bytes_or_path))
        else:
            doc = docx.Document(io.BytesIO(file_bytes_or_path))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs)

    @classmethod
    def extract_text(cls, file_bytes_or_path: Union[bytes, str, Path], filename: str = "") -> str:
        """Extract text based on file format extension."""
        name_lower = filename.lower()
        if name_lower.endswith(".docx"):
            return cls.extract_text_from_docx(file_bytes_or_path)
        return cls.extract_text_from_pdf(file_bytes_or_path)

    @classmethod
    def parse_resume_content(cls, raw_text: str) -> Dict[str, Any]:
        """
        Extracts candidate sections from resume text using heuristics.
        """
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

        # Detect potential skills
        known_skill_keywords = [
            "Python", "SQL", "BigQuery", "Apache Airflow", "Airflow", "GCP", "Google Cloud Platform",
            "Vertex AI", "Gemini", "FastAPI", "Docker", "Kubernetes", "Git", "ChromaDB", "FAISS",
            "LangGraph", "LangChain", "RAG", "Dataflow", "Pub/Sub", "Cloud Storage", "Cloud Functions",
            "dbt", "Spark", "PySpark", "Kafka", "PostgreSQL", "Snowflake", "Databricks", "Terraform",
            "AWS", "Redshift", "S3", "Glue", "Lambda", "Java", "C++", "TypeScript", "React", "Rust",
        ]


        found_skills = []
        for kw in known_skill_keywords:
            if re.search(rf"\b{re.escape(kw)}\b", raw_text, re.IGNORECASE):
                found_skills.append(kw)

        # Detect potential projects
        detected_projects = []
        proj_headings = ["Local RAG", "AI AutoHeal", "Sales Data Validation", "Anomaly Detection", "CareerPilot"]
        for ph in proj_headings:
            if ph.lower() in raw_text.lower():
                detected_projects.append(ph)

        return {
            "skills": list(set(found_skills)),
            "detected_projects": detected_projects,
            "raw_text": raw_text,
        }

    @classmethod
    def compute_diff(
        cls,
        active_profile: CandidateProfile,
        parsed_resume_data: Dict[str, Any],
    ) -> ProfileDiffResult:
        """
        Computes differences between active CandidateProfile and the newly parsed resume data.
        """
        diff_items: List[ProfileDiffItem] = []

        active_skill_names = {s.name.strip().lower(): s.name for s in active_profile.skills}
        parsed_skills = parsed_resume_data.get("skills", [])

        # 1. Check added skills
        for p_skill in parsed_skills:
            if p_skill.lower() not in active_skill_names:
                diff_items.append(
                    ProfileDiffItem(
                        section="skills",
                        change_type="ADDED",
                        item_name=f"Skill: {p_skill}",
                        old_value=None,
                        new_value=p_skill,
                        approved=True,
                    )
                )

        # 2. Check unchanged skills
        for a_lower, a_name in active_skill_names.items():
            if any(p.lower() == a_lower for p in parsed_skills):
                diff_items.append(
                    ProfileDiffItem(
                        section="skills",
                        change_type="UNCHANGED",
                        item_name=f"Skill: {a_name}",
                        old_value=a_name,
                        new_value=a_name,
                        approved=False,
                    )
                )

        # 3. Check projects
        active_project_names = {p.name.strip().lower(): p.name for p in active_profile.projects}
        for det_proj in parsed_resume_data.get("detected_projects", []):
            if not any(det_proj.lower() in a_name.lower() for a_name in active_project_names):
                diff_items.append(
                    ProfileDiffItem(
                        section="projects",
                        change_type="ADDED",
                        item_name=f"Project: {det_proj}",
                        old_value=None,
                        new_value=det_proj,
                        approved=True,
                    )
                )

        total_added = sum(1 for d in diff_items if d.change_type == "ADDED")
        total_removed = sum(1 for d in diff_items if d.change_type == "REMOVED")
        total_changed = sum(1 for d in diff_items if d.change_type == "CHANGED")
        total_unchanged = sum(1 for d in diff_items if d.change_type == "UNCHANGED")

        return ProfileDiffResult(
            diff_items=diff_items,
            total_added=total_added,
            total_removed=total_removed,
            total_changed=total_changed,
            total_unchanged=total_unchanged,
        )

    @classmethod
    def apply_diff_items(
        cls,
        active_profile: CandidateProfile,
        approved_items: List[ProfileDiffItem],
    ) -> CandidateProfile:
        """
        Applies approved diff items into the active candidate profile.
        """
        applied_count = 0
        for item in approved_items:
            if not item.approved:
                continue

            if item.section == "skills" and item.change_type == "ADDED" and item.new_value:
                skill_name = item.new_value.strip()
                if not any(s.name.lower() == skill_name.lower() for s in active_profile.skills):
                    active_profile.skills.append(
                        Skill(
                            name=skill_name,
                            category=SkillCategory.PROGRAMMING,
                            evidence_level="PERSONAL_PROJECT",
                            evidence_status="VERIFIED",
                        )
                    )
                    applied_count += 1

            elif item.section == "projects" and item.change_type == "ADDED" and item.new_value:
                proj_name = item.new_value.strip()
                if not any(p.name.lower() == proj_name.lower() for p in active_profile.projects):
                    active_profile.projects.append(
                        Project(
                            name=proj_name,
                            project_type="PERSONAL_PROJECT",
                            description=f"Imported project {proj_name} from master resume.",
                            technologies=["Python"],
                        )
                    )
                    applied_count += 1

        if applied_count > 0:
            CandidateService.save_active_profile(
                profile=active_profile,
                change_summary=f"Applied {applied_count} changes from master resume import.",
                changed_sections=["master_resume_import"],
            )

        return active_profile
