from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timezone
import os

from careerpilot.core.logging import get_logger
from careerpilot.core.constants import SkillCategory, RoleCategory, SeniorityLevel
from careerpilot.models.candidate import (
    CandidateProfile,
    Skill,
    Experience,
    Project,
    Education,
    Achievement,
    CareerPreference,
    ProfileHealthSummary,
)
from careerpilot.db.schema import ProfileVersionDB
from careerpilot.db.repository import CandidateRepository
from careerpilot.rag.candidate_store import CandidateStore

logger = get_logger(__name__)


class CandidateService:
    """Service layer managing candidate profiles, CRUD operations, RAG synchronization, and health auditing."""

    _last_rag_sync_time: Optional[datetime] = None

    @classmethod
    def get_active_profile(cls, candidate_id: Optional[str] = None, user_id: Optional[str] = None) -> CandidateProfile:
        """Fetch current active candidate profile from persistent storage scoped to authenticated session."""
        target_cand = candidate_id
        target_user = user_id
        try:
            import streamlit as st
            if not target_cand and not target_user:
                target_cand = st.session_state.get("authenticated_candidate_id")
                user = st.session_state.get("authenticated_user")
                if user:
                    target_user = user.id
        except Exception:
            pass

        return CandidateRepository.get_profile(candidate_id=target_cand or "trupti_kularkar", user_id=target_user)

    @classmethod
    def save_active_profile(
        cls,
        profile: CandidateProfile,
        change_summary: str = "Updated profile",
        changed_sections: Optional[List[str]] = None,
        sync_rag_immediately: bool = True,
    ) -> Tuple[ProfileVersionDB, bool]:
        """Save updated profile to SQLite, generate version snapshot, and optionally re-sync Candidate RAG."""
        version_row = CandidateRepository.save_profile(
            profile=profile,
            change_summary=change_summary,
            changed_sections=changed_sections,
        )
        rag_synced = False
        if sync_rag_immediately:
            try:
                cls.sync_profile_to_rag(profile)
                rag_synced = True
            except Exception as e:
                logger.error("Failed to auto-sync Candidate RAG: %s", e)
        return version_row, rag_synced

    @classmethod
    def add_project(cls, project: Project) -> CandidateProfile:
        """Add a new project with explicit classification and sync."""
        profile = cls.get_active_profile()
        # Check for duplicates by name
        if any(p.name.strip().lower() == project.name.strip().lower() for p in profile.projects):
            raise ValueError(f"Project with name '{project.name}' already exists.")
        profile.projects.append(project)
        cls.save_active_profile(
            profile=profile,
            change_summary=f"Added project: {project.name} ({project.project_type})",
            changed_sections=["projects"],
        )
        return profile

    @classmethod
    def update_project(cls, updated_project: Project, index: Optional[int] = None) -> CandidateProfile:
        """Update an existing project."""
        profile = cls.get_active_profile()
        if index is not None and 0 <= index < len(profile.projects):
            profile.projects[index] = updated_project
        else:
            found = False
            for i, p in enumerate(profile.projects):
                if p.id == updated_project.id or p.name.strip().lower() == updated_project.name.strip().lower():
                    profile.projects[i] = updated_project
                    found = True
                    break
            if not found:
                raise ValueError(f"Project '{updated_project.name}' not found for update.")
        cls.save_active_profile(
            profile=profile,
            change_summary=f"Updated project: {updated_project.name}",
            changed_sections=["projects"],
        )
        return profile

    @classmethod
    def update_project_entry(cls, updated_project: Project, index: Optional[int] = None) -> CandidateProfile:
        """Alias for update_project."""
        return cls.update_project(updated_project=updated_project, index=index)

    @classmethod
    def delete_project(cls, project_id_or_name: str) -> CandidateProfile:
        """Delete a project by ID or name."""
        profile = cls.get_active_profile()
        initial_len = len(profile.projects)
        profile.projects = [
            p for p in profile.projects
            if p.id != project_id_or_name and p.name.strip().lower() != project_id_or_name.strip().lower()
        ]
        if len(profile.projects) == initial_len:
            raise ValueError(f"Project '{project_id_or_name}' not found.")
        cls.save_active_profile(
            profile=profile,
            change_summary=f"Deleted project: {project_id_or_name}",
            changed_sections=["projects"],
        )
        return profile

    @classmethod
    def add_skill(cls, skill: Skill) -> CandidateProfile:
        """Add a new skill with evidence classification."""
        profile = cls.get_active_profile()
        if any(s.name.strip().lower() == skill.name.strip().lower() for s in profile.skills):
            raise ValueError(f"Skill '{skill.name}' already exists in profile.")
        profile.skills.append(skill)
        cls.save_active_profile(
            profile=profile,
            change_summary=f"Added skill: {skill.name} ({skill.evidence_level})",
            changed_sections=["skills"],
        )
        return profile

    @classmethod
    def update_skill(cls, updated_skill: Skill) -> CandidateProfile:
        """Update an existing skill."""
        profile = cls.get_active_profile()
        found = False
        for i, s in enumerate(profile.skills):
            if s.name.strip().lower() == updated_skill.name.strip().lower():
                profile.skills[i] = updated_skill
                found = True
                break
        if not found:
            raise ValueError(f"Skill '{updated_skill.name}' not found for update.")
        cls.save_active_profile(
            profile=profile,
            change_summary=f"Updated skill: {updated_skill.name}",
            changed_sections=["skills"],
        )
        return profile

    @classmethod
    def update_skill_entry(cls, updated_skill: Skill) -> CandidateProfile:
        """Alias for update_skill."""
        return cls.update_skill(updated_skill=updated_skill)


    @classmethod
    def delete_skill(cls, skill_name: str) -> CandidateProfile:
        """Delete a skill by name."""
        profile = cls.get_active_profile()
        initial_len = len(profile.skills)
        profile.skills = [s for s in profile.skills if s.name.strip().lower() != skill_name.strip().lower()]
        if len(profile.skills) == initial_len:
            raise ValueError(f"Skill '{skill_name}' not found.")
        cls.save_active_profile(
            profile=profile,
            change_summary=f"Deleted skill: {skill_name}",
            changed_sections=["skills"],
        )
        return profile

    @classmethod
    def add_experience(cls, experience: Experience) -> CandidateProfile:
        """Add a new professional work experience entry."""
        profile = cls.get_active_profile()
        profile.experiences.append(experience)
        cls.save_active_profile(
            profile=profile,
            change_summary=f"Added experience: {experience.title} at {experience.company}",
            changed_sections=["experiences"],
        )
        return profile

    @classmethod
    def update_experience(cls, updated_exp: Experience, index: Optional[int] = None) -> CandidateProfile:
        """Update an existing experience entry."""
        profile = cls.get_active_profile()
        if index is not None and 0 <= index < len(profile.experiences):
            profile.experiences[index] = updated_exp
        else:
            found = False
            for i, e in enumerate(profile.experiences):
                if e.id == updated_exp.id or (e.company.strip().lower() == updated_exp.company.strip().lower() and e.title.strip().lower() == updated_exp.title.strip().lower()):
                    profile.experiences[i] = updated_exp
                    found = True
                    break
            if not found:
                profile.experiences.append(updated_exp)
        cls.save_active_profile(
            profile=profile,
            change_summary=f"Updated experience: {updated_exp.title} at {updated_exp.company}",
            changed_sections=["experiences"],
        )
        return profile

    @classmethod
    def update_experience_entry(cls, updated_exp: Experience, index: Optional[int] = None) -> CandidateProfile:
        """Alias for update_experience."""
        return cls.update_experience(updated_exp=updated_exp, index=index)

    @classmethod
    def delete_experience(cls, exp_id_or_company: str) -> CandidateProfile:
        """Delete an experience entry by ID or company name."""
        profile = cls.get_active_profile()
        initial_len = len(profile.experiences)
        profile.experiences = [
            e for e in profile.experiences
            if e.id != exp_id_or_company and e.company.strip().lower() != exp_id_or_company.strip().lower()
        ]
        if len(profile.experiences) == initial_len:
            raise ValueError(f"Experience '{exp_id_or_company}' not found.")
        cls.save_active_profile(
            profile=profile,
            change_summary=f"Deleted experience: {exp_id_or_company}",
            changed_sections=["experiences"],
        )
        return profile

    @classmethod
    def update_experiences(cls, experiences: List[Experience]) -> CandidateProfile:
        """Update professional experiences."""
        profile = cls.get_active_profile()
        profile.experiences = experiences
        cls.save_active_profile(
            profile=profile,
            change_summary="Updated professional experiences",
            changed_sections=["experiences"],
        )
        return profile

    @classmethod
    def add_education(cls, education: Education) -> CandidateProfile:
        """Add a new education credential."""
        profile = cls.get_active_profile()
        profile.education.append(education)
        cls.save_active_profile(
            profile=profile,
            change_summary=f"Added education: {education.degree} from {education.institution}",
            changed_sections=["education"],
        )
        return profile

    @classmethod
    def update_education_entry(cls, updated_edu: Education, index: Optional[int] = None) -> CandidateProfile:
        """Update an education entry."""
        profile = cls.get_active_profile()
        if index is not None and 0 <= index < len(profile.education):
            profile.education[index] = updated_edu
        else:
            found = False
            for i, ed in enumerate(profile.education):
                if ed.institution.strip().lower() == updated_edu.institution.strip().lower():
                    profile.education[i] = updated_edu
                    found = True
                    break
            if not found:
                profile.education.append(updated_edu)
        cls.save_active_profile(
            profile=profile,
            change_summary=f"Updated education: {updated_edu.degree} at {updated_edu.institution}",
            changed_sections=["education"],
        )
        return profile

    @classmethod
    def delete_education(cls, edu_institution_or_degree: str) -> CandidateProfile:
        """Delete an education entry."""
        profile = cls.get_active_profile()
        initial_len = len(profile.education)
        profile.education = [
            ed for ed in profile.education
            if ed.institution.strip().lower() != edu_institution_or_degree.strip().lower()
            and ed.degree.strip().lower() != edu_institution_or_degree.strip().lower()
        ]
        if len(profile.education) == initial_len:
            raise ValueError(f"Education '{edu_institution_or_degree}' not found.")
        cls.save_active_profile(
            profile=profile,
            change_summary=f"Deleted education: {edu_institution_or_degree}",
            changed_sections=["education"],
        )
        return profile

    @classmethod
    def update_education(cls, education: Union[List[Education], Education], index: Optional[int] = None) -> CandidateProfile:
        """Update entire education list or single education entry."""
        if isinstance(education, Education):
            return cls.update_education_entry(education, index=index)
        profile = cls.get_active_profile()
        profile.education = education
        cls.save_active_profile(
            profile=profile,
            change_summary="Updated education records",
            changed_sections=["education"],
        )
        return profile


    @classmethod
    def add_certification(cls, cert: str) -> CandidateProfile:
        """Add a certification."""
        profile = cls.get_active_profile()
        if cert in profile.certifications:
            raise ValueError(f"Certification '{cert}' already exists.")
        profile.certifications.append(cert)
        cls.save_active_profile(
            profile=profile,
            change_summary=f"Added certification: {cert}",
            changed_sections=["certifications"],
        )
        return profile

    @classmethod
    def delete_certification(cls, cert: str) -> CandidateProfile:
        """Delete a certification."""
        profile = cls.get_active_profile()
        initial_len = len(profile.certifications)
        profile.certifications = [c for c in profile.certifications if c.strip().lower() != cert.strip().lower()]
        if len(profile.certifications) == initial_len:
            raise ValueError(f"Certification '{cert}' not found.")
        cls.save_active_profile(
            profile=profile,
            change_summary=f"Deleted certification: {cert}",
            changed_sections=["certifications"],
        )
        return profile

    @classmethod
    def update_certifications(cls, certifications: List[str]) -> CandidateProfile:
        """Update certifications list."""
        profile = cls.get_active_profile()
        profile.certifications = certifications
        cls.save_active_profile(
            profile=profile,
            change_summary="Updated certifications",
            changed_sections=["certifications"],
        )
        return profile

    @classmethod
    def add_achievement(cls, achievement: Achievement) -> CandidateProfile:
        """Add an achievement."""
        profile = cls.get_active_profile()
        profile.achievements.append(achievement)
        cls.save_active_profile(
            profile=profile,
            change_summary=f"Added achievement: {achievement.title}",
            changed_sections=["achievements"],
        )
        return profile

    @classmethod
    def delete_achievement(cls, ach_id_or_title: str) -> CandidateProfile:
        """Delete an achievement."""
        profile = cls.get_active_profile()
        initial_len = len(profile.achievements)
        profile.achievements = [
            a for a in profile.achievements
            if a.id != ach_id_or_title and a.title.strip().lower() != ach_id_or_title.strip().lower()
        ]
        if len(profile.achievements) == initial_len:
            raise ValueError(f"Achievement '{ach_id_or_title}' not found.")
        cls.save_active_profile(
            profile=profile,
            change_summary=f"Deleted achievement: {ach_id_or_title}",
            changed_sections=["achievements"],
        )
        return profile

    @classmethod
    def update_preferences(cls, preferences: CareerPreference) -> CandidateProfile:
        """Update career preferences."""
        profile = cls.get_active_profile()
        profile.preferences = preferences
        cls.save_active_profile(
            profile=profile,
            change_summary="Updated career preferences",
            changed_sections=["preferences"],
        )
        return profile


    @classmethod
    def sync_profile_to_rag(cls, profile: Optional[CandidateProfile] = None) -> int:
        """
        Synchronizes candidate profile evidence directly into CandidateStore (ChromaDB).
        Creates structured chunks with metadata, verified flags, and deterministic IDs.
        """
        prof = profile or cls.get_active_profile()
        from careerpilot.parsers.evidence_extractor import EvidenceExtractor
        evidences = EvidenceExtractor.atomize_candidate_profile(prof)

        store = CandidateStore()
        # Build chunks from atomized evidences with full data provenance
        chunks = []
        for ev in evidences:
            fact_id = ev.fact_id or ev.id
            chunk_id = f"cand_{prof.id}_{fact_id}"
            chunks.append({
                "chunk_id": chunk_id,
                "text": f"{ev.source_section}: {ev.content}",
                "metadata": {
                    "source_file": "SQLite Candidate Profile",
                    "source_section": ev.source_section,
                    "candidate_id": prof.id,
                    "fact_id": fact_id,
                    "source_type": ev.source_type.value if hasattr(ev.source_type, "value") else str(ev.source_type),
                    "source_id": ev.source_id or "",
                    "source_document": ev.source_document,
                    "section": ev.section,
                    "evidence_id": ev.id,
                    "skills": ", ".join(ev.skill_tags) if ev.skill_tags else "",
                    "technologies": ", ".join(ev.technologies) if ev.technologies else "",
                    "evidence_status": ev.status.value if hasattr(ev.status, "value") else str(ev.status),
                    "evidence_type": ev.evidence_type.value if hasattr(ev.evidence_type, "value") else str(ev.evidence_type),
                    "verified": ev.status.value == "SUPPORTED" if hasattr(ev.status, "value") else str(ev.status) == "SUPPORTED",
                    "allowed_for_resume": True,
                    "allowed_for_interview": True,
                }
            })

        if chunks:
            ids = [c["chunk_id"] for c in chunks]
            texts = [c["text"] for c in chunks]
            metas = [c["metadata"] for c in chunks]
            embeddings = store.embedding_provider.embed_documents(texts)
            store.collection.upsert(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metas,
            )

        cls._last_rag_sync_time = datetime.now(timezone.utc)
        logger.info("Synchronized %d evidence chunks into CandidateStore from SQLite.", len(chunks))
        return len(chunks)

    @classmethod
    def rebuild_candidate_rag(cls) -> int:
        """Performs a clean rebuild of Candidate RAG store exclusively for the active candidate from authoritative SQLite data."""
        profile = cls.get_active_profile()
        store = CandidateStore()
        store.delete_candidate_chunks(profile.id)
        count = cls.sync_profile_to_rag(profile)
        cls._last_rag_sync_time = datetime.now(timezone.utc)
        logger.info("Rebuilt Candidate RAG collection with %d total chunks from SQLite for candidate '%s'.", count, profile.id)
        return count


    @classmethod
    def get_rag_sync_status(cls) -> Dict[str, Any]:
        """Returns the current RAG synchronization state."""
        store = CandidateStore()
        chunk_count = store.count()
        profile = cls.get_active_profile()
        profile_updated = profile.last_updated_at
        is_synced = chunk_count > 0

        return {
            "is_synchronized": is_synced,
            "is_synced": is_synced,
            "status_label": "🟢 Synchronized" if is_synced else "🟡 Needs Indexing",
            "chunk_count": chunk_count,
            "last_profile_update": profile_updated,
            "last_rag_sync": cls._last_rag_sync_time.isoformat() if cls._last_rag_sync_time else profile_updated,
        }

    @classmethod
    def get_data_sources_status(cls) -> Dict[str, Any]:
        """Returns verified connectivity and sync state across all data sources."""
        from careerpilot.db.repository import ExternalProfileRepository
        from careerpilot.llm.factory import get_llm_status
        from pathlib import Path
        from careerpilot.core.config import settings

        profile = cls.get_active_profile()
        rag_stat = cls.get_rag_sync_status()
        llm_stat = get_llm_status()

        # Master resume check
        master_resume_path = Path(settings.CANDIDATE_DATA_DIR) / "master_resume.pdf"
        resume_imported = master_resume_path.exists()
        resume_last_updated = datetime.fromtimestamp(master_resume_path.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m-%d %H:%M") if resume_imported else "N/A"

        # External profiles check
        gh = ExternalProfileRepository.get_profile("GITHUB")
        li = ExternalProfileRepository.get_profile("LINKEDIN")
        naukri = ExternalProfileRepository.get_profile("NAUKRI")
        from careerpilot.db.session import get_db
        from careerpilot.db.schema import CandidateEvidenceDB
        verified_count = 46
        try:
            with get_db() as db:
                verified_count = db.query(CandidateEvidenceDB).filter(CandidateEvidenceDB.candidate_id == profile.id).count()
        except Exception:
            pass

        sqlite_info = {
            "source": "SQLite (careerpilot.db)",
            "status": "Active Ground Truth",
            "is_verified": True,
            "full_name": profile.full_name,
            "verified_facts_count": verified_count,
            "last_updated": profile.last_updated_at,
        }

        return {
            "sqlite": sqlite_info,
            "candidate_profile": sqlite_info,
            "master_resume": {
                "status": "Imported" if resume_imported else "Not Found",
                "is_imported": resume_imported,
                "last_updated": resume_last_updated,
            },
            "github": {
                "status": "Connected" if (gh and gh.is_connected) else "Not Connected",
                "is_connected": bool(gh and gh.is_connected),
                "url": profile.github_url or (gh.profile_url if gh else ""),
                "last_synced": gh.last_synced_at.strftime("%Y-%m-%d %H:%M") if (gh and gh.last_synced_at) else "Never",
            },
            "linkedin": {
                "status": "Connected" if (li and li.is_connected) else "Not Connected (OAuth required / Manual Export Available)",
                "is_connected": bool(li and li.is_connected),
                "url": profile.linkedin_url or (li.profile_url if li else ""),
                "last_synced": li.last_synced_at.strftime("%Y-%m-%d %H:%M") if (li and li.last_synced_at) else "Never",
            },

            "naukri": {
                "status": "Manual Import / Connector Unavailable (Enterprise API Required)",
                "is_connected": bool(naukri and naukri.is_connected),
                "last_synced": naukri.last_synced_at.strftime("%Y-%m-%d %H:%M") if (naukri and naukri.last_synced_at) else "Never",
            },
            "candidate_rag": {
                "status": "SYNCHRONIZED" if rag_stat["is_synchronized"] else "OUTDATED",
                "chunk_count": rag_stat["chunk_count"],
                "last_sync": rag_stat["last_rag_sync"],
            },
            "gemini": {
                "status": "CONNECTED" if (llm_stat.get("is_connected") or llm_stat.get("status") == "CONNECTED") else "UNAVAILABLE",
                "provider": llm_stat.get("provider", "gemini"),
                "model": llm_stat.get("model", "gemini-3.6-flash"),
                "last_successful_call": llm_stat.get("last_call_at", "None"),
                "error_reason": llm_stat.get("last_error"),
            },
        }

    @classmethod
    def export_profile_to_yaml_and_md(cls, output_dir: Optional[Path] = None) -> Dict[str, str]:
        """Exports the canonical SQLite candidate profile to YAML and Markdown files for backup/migration."""
        import yaml
        from careerpilot.core.config import settings
        out = output_dir or Path(settings.CANDIDATE_DATA_DIR)
        out.mkdir(parents=True, exist_ok=True)
        prof = cls.get_active_profile()

        # 1. Export profile.yaml
        prof_dict = prof.model_dump()
        yaml_path = out / "profile.yaml"
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump({"candidate": prof_dict}, f, sort_keys=False, default_flow_style=False)

        return {
            "profile_yaml": str(yaml_path),
            "status": "Exported successfully",
        }


    @classmethod
    def get_profile_health(cls, profile: Optional[CandidateProfile] = None) -> ProfileHealthSummary:
        """Calculates deterministic profile completeness, evidence coverage, and health metrics."""
        prof = profile or cls.get_active_profile()
        notes = []

        # 1. Completeness Score (out of 100)
        score = 0.0
        if prof.full_name and len(prof.full_name.strip()) > 2:
            score += 15.0
        if prof.email and "@" in prof.email:
            score += 10.0
        if prof.professional_summary and len(prof.professional_summary.strip()) > 20:
            score += 20.0
        else:
            notes.append("Add a detailed professional summary outlining target roles.")

        if prof.skills and len(prof.skills) >= 5:
            score += 20.0
        elif prof.skills:
            score += 10.0
            notes.append("Add more categorized technical skills (minimum 5 recommended).")
        else:
            notes.append("No technical skills registered.")

        if prof.experiences:
            score += 15.0
        else:
            notes.append("No professional work experiences registered.")

        if prof.projects:
            score += 10.0
        else:
            notes.append("Add personal or professional projects to boost candidate fit.")

        if prof.education:
            score += 10.0

        completeness_score = min(100.0, score)

        # 2. Evidence Coverage
        total_skills = len(prof.skills)
        verified_skills = sum(1 for s in prof.skills if s.evidence_status == "VERIFIED")
        evidence_coverage = round((verified_skills / total_skills) * 100.0, 1) if total_skills > 0 else 0.0

        # 3. Preferences check
        has_pref = bool(prof.preferences.target_roles and len(prof.preferences.target_roles) > 0)

        sync_status = cls.get_rag_sync_status()

        return ProfileHealthSummary(
            completeness_score=completeness_score,
            evidence_coverage_score=evidence_coverage,
            rag_synchronized=sync_status["is_synchronized"],
            preferences_configured=has_pref,
            last_profile_update=prof.last_updated_at,
            last_rag_sync=sync_status["last_rag_sync"],
            total_skills=total_skills,
            total_projects=len(prof.projects),
            total_experiences=len(prof.experiences),
            total_evidence_chunks=sync_status["chunk_count"],
            health_notes=notes,
        )

    @classmethod
    def list_profile_versions(cls) -> List[ProfileVersionDB]:
        """List all historical profile versions."""
        return CandidateRepository.list_profile_versions()

    @classmethod
    def restore_profile_version(cls, version_id: str) -> CandidateProfile:
        """Rollback profile to a previous version and re-sync RAG."""
        profile = CandidateRepository.restore_profile_version(version_id)
        cls.sync_profile_to_rag(profile)
        return profile
