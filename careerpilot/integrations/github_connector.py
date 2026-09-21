"""
CareerPilot AI — Official GitHub Integration
Interacts with the public GitHub REST API to ingest candidate repositories,
classify them as PERSONAL_PROJECT, and support human-in-the-loop review and approval.
"""
import json
import ssl
import urllib.request
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from careerpilot.core.constants import ProvenanceSourceType
from careerpilot.core.logging import get_logger
from careerpilot.db.repository import ExternalProfileRepository, CandidateRepository
from careerpilot.db.schema import CandidateEvidenceDB
from careerpilot.db.session import get_db

logger = get_logger("careerpilot.integrations.github")


class GitHubConnector:
    """Official GitHub REST API connector with secure SSL verification and candidate ownership."""

    BASE_API_URL = "https://api.github.com"

    @classmethod
    def _create_ssl_context(cls) -> ssl.SSLContext:
        """Creates secure TLS context validated with official CA certificates."""
        import certifi
        return ssl.create_default_context(cafile=certifi.where())

    @classmethod
    def resolve_username(
        cls,
        candidate_id: Optional[str] = None,
        username: Optional[str] = None,
        explicit_username: Optional[str] = None,
        candidate_profile: Optional[Any] = None,
    ) -> str:
        """Resolves candidate's GitHub username from explicit argument, profile object, or database."""
        u = explicit_username or username
        raw_user = ""
        if u and u.strip():
            raw_user = u.strip()
        else:
            prof = candidate_profile
            if not prof and candidate_id:
                prof = CandidateRepository.get_profile(candidate_id=candidate_id)
            if prof and getattr(prof, "github_url", None):
                raw_user = prof.github_url
            elif prof and getattr(prof, "full_name", None):
                raw_user = prof.full_name.replace(" ", "")

        if raw_user:
            cleaned = raw_user.rstrip("/").split("/")[-1].strip()
            if cleaned.lower() in ("trupti-kularkar", "truptikularkar"):
                return "Truptikularkar"
            return cleaned

        cid = candidate_id or settings.active_candidate_id
        if cid in ("trupti_kularkar", "cand_verified"):
            return "Truptikularkar"
        return ""



    @classmethod
    def fetch_user_repositories(
        cls,
        username: Optional[str] = None,
        token: Optional[str] = None,
        candidate_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetches public repositories for the candidate via official GitHub REST API.
        Classifies all fetched repositories as PERSONAL_PROJECT.
        """
        target_user = cls.resolve_username(candidate_id=candidate_id, username=username)
        url = f"{cls.BASE_API_URL}/users/{target_user}/repos?per_page=100&sort=updated"
        headers = {
            "User-Agent": "CareerPilot-AI-Agent",
            "Accept": "application/vnd.github.v3+json",
        }
        if token:
            headers["Authorization"] = f"token {token}"

        req = urllib.request.Request(url, headers=headers)
        ctx = cls._create_ssl_context()

        try:
            with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
                raw_repos = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            logger.error(f"GitHub API request failed for '{target_user}': {e}")
            raise e

        parsed_repos = []
        for r in raw_repos:
            if not isinstance(r, dict):
                continue
            name = r.get("name", "Untitled")
            parsed_repos.append({
                "name": name,
                "description": r.get("description") or "",
                "html_url": r.get("html_url", f"https://github.com/{target_user}/{name}"),
                "language": r.get("language") or "Python",
                "topics": r.get("topics") or [],
                "stars": r.get("stargazers_count", 0),
                "forks": r.get("forks_count", 0),
                "updated_at": r.get("updated_at", ""),
                "classification": "PERSONAL_PROJECT",
                "is_approved": False,
                "provenance": {
                    "source_type": ProvenanceSourceType.GITHUB.value,
                    "source_id": name,
                    "source_document": r.get("html_url", ""),
                    "section": "projects",
                    "evidence_status": "PROPOSED",
                }
            })

        logger.info(f"Successfully fetched {len(parsed_repos)} repositories for GitHub user '{target_user}'.")
        return parsed_repos

    @classmethod
    def sync_github_profile(
        cls,
        username: Optional[str] = None,
        candidate_id: str = "trupti_kularkar",
        token: Optional[str] = None,
        github_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Connects and synchronizes candidate GitHub repositories.
        Persists connection state in SQLite external profiles table.
        """
        tok = github_token or token
        target_user = cls.resolve_username(candidate_id=candidate_id, username=username)
        try:
            repos = cls.fetch_user_repositories(username=target_user, token=tok)

            ExternalProfileRepository.save_profile(
                platform="GITHUB",
                candidate_id=candidate_id,
                username=target_user,
                profile_url=f"https://github.com/{target_user}",
                is_connected=True,
                sync_status="SYNCED",
                raw_data={"repos_count": len(repos), "last_sync": datetime.now(timezone.utc).isoformat()},
            )
            return {
                "status": "SUCCESS",
                "platform": "GITHUB",
                "username": target_user,
                "profile_url": f"https://github.com/{target_user}",
                "repos_count": len(repos),
                "repos": repos,
            }
        except Exception as e:
            logger.error(f"GitHub sync failed: {e}")
            ExternalProfileRepository.save_profile(
                platform="GITHUB",
                candidate_id=candidate_id,
                username=target_user,
                profile_url=f"https://github.com/{target_user}",
                is_connected=False,
                sync_status=f"ERROR: {e}",
            )
            return {
                "status": "ERROR",
                "platform": "GITHUB",
                "username": target_user,
                "profile_url": f"https://github.com/{target_user}",
                "error": str(e),
                "repos_count": 0,
                "repos": [],
            }


    @classmethod
    def approve_and_import_project(
        cls,
        repo_data: Dict[str, Any],
        candidate_id: str = "trupti_kularkar",
    ) -> bool:
        """
        Imports a reviewed and approved GitHub repository as verified candidate evidence.
        """
        with get_db() as db:
            fact_id = f"gh_{repo_data['name'].lower()}"
            existing = db.query(CandidateEvidenceDB).filter(
                CandidateEvidenceDB.candidate_id == candidate_id,
                CandidateEvidenceDB.fact_id == fact_id,
            ).first()

            desc = repo_data.get("description") or f"Personal project {repo_data['name']}"
            if repo_data.get("language"):
                desc += f" (Built with {repo_data['language']})"

            target_user = cls.resolve_username(candidate_id=candidate_id)
            if existing:
                existing.content = desc
                existing.status = "VERIFIED"
                existing.updated_at = datetime.now(timezone.utc)
            else:
                new_ev = CandidateEvidenceDB(
                    id=f"ev_{fact_id}",
                    candidate_id=candidate_id,
                    fact_id=fact_id,
                    section="projects",
                    source_section="projects",
                    evidence_type="PROJECT",
                    content=desc,
                    source_type=ProvenanceSourceType.GITHUB.value,
                    source_id=repo_data["name"],
                    source_document=repo_data.get("html_url", f"https://github.com/{target_user}"),
                    status="VERIFIED",
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                db.add(new_ev)

            db.commit()
            logger.info(f"Approved and imported GitHub project '{repo_data['name']}' into CandidateEvidenceDB.")

            # Also add to active CandidateProfile and trigger RAG synchronization
            try:
                from careerpilot.services.candidate_service import CandidateService
                from careerpilot.models.candidate import Project, Skill
                from careerpilot.core.constants import SkillCategory

                profile = CandidateService.get_active_profile(candidate_id=candidate_id)
                repo_name = repo_data["name"]
                proj_name = repo_name.replace("-", " ").replace("_", " ").title()
                techs = [repo_data["language"]] if repo_data.get("language") else ["Python"]
                if repo_data.get("topics"):
                    techs.extend([t.replace("-", " ").title() for t in repo_data["topics"][:4]])

                existing_proj = next((p for p in profile.projects if p.name.lower() in (proj_name.lower(), repo_name.lower())), None)
                if not existing_proj:
                    new_proj = Project(
                        name=proj_name,
                        project_type="PERSONAL_PROJECT",
                        description=desc,
                        technologies=techs,
                        responsibilities=[
                            f"Developed and maintained open-source repository {repo_name} on GitHub ({repo_data.get('html_url')}).",
                            desc,
                        ],
                        highlights=[f"Public GitHub project with {repo_data.get('stars', 0)} stars."],
                        metrics=[f"GitHub Repo: {repo_name}"],
                    )
                    profile.projects.append(new_proj)

                # Register language as skill if not present
                if repo_data.get("language"):
                    lang = repo_data["language"]
                    if not any(s.name.lower() == lang.lower() for s in profile.skills):
                        profile.skills.append(
                            Skill(
                                name=lang,
                                category=SkillCategory.PROGRAMMING,
                                evidence_level="PERSONAL_PROJECT",
                                evidence_status="VERIFIED",
                                proficiency_level="Proficient",
                                years_of_experience=1.0,
                            )
                        )

                CandidateService.save_active_profile(
                    profile=profile,
                    change_summary=f"Imported GitHub repository project: {proj_name}",
                    changed_sections=["projects", "skills"],
                    sync_rag_immediately=True,
                )
                logger.info("Successfully added GitHub project '%s' to active CandidateProfile and re-indexed Candidate RAG.", proj_name)
            except Exception as ex:
                logger.warning("Could not sync GitHub project to CandidateProfile: %s", ex)

            return True
