import json
import re
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection

from careerpilot.core.config import settings
from careerpilot.core.logging import get_logger
from careerpilot.rag.embeddings import BaseEmbeddingProvider, get_embedding_provider
from careerpilot.rag.vector_store import LocalVectorClient, LocalVectorCollection

logger = get_logger(__name__)


class CandidateStore:
    """
    Manages the persistent vector collection for verified Candidate Evidence chunks.
    Ensures semantically meaningful chunking, rich metadata preservation,
    deterministic IDs to prevent duplicate indexing, and complete isolation
    from generic technical knowledge.
    """

    COLLECTION_NAME = "candidate_evidence"

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
        client: Optional[Any] = None,
    ):
        self.persist_directory = persist_directory or settings.CHROMA_PERSIST_DIRECTORY
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        
        self.client = client or LocalVectorClient(path=self.persist_directory)
        self.embedding_provider = embedding_provider or get_embedding_provider()
        self.collection: LocalVectorCollection = self._get_or_create_collection()

    def _get_or_create_collection(self) -> LocalVectorCollection:
        return self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"description": "Verified Candidate Evidence Store for CareerPilot AI"},
        )


    def clear(self) -> None:
        """Deletes and recreates the candidate evidence collection."""
        try:
            self.client.delete_collection(self.COLLECTION_NAME)
            logger.info("Deleted collection '%s'", self.COLLECTION_NAME)
        except Exception as e:
            logger.debug("Collection deletion exception (normal if non-existent): %s", e)
        self.collection = self._get_or_create_collection()

    def parse_candidate_directory(self, candidate_dir: Path) -> List[Dict[str, Any]]:
        """
        Parses candidate source files into semantically structured chunks with metadata.
        Does NOT modify any source files.
        """
        chunks: List[Dict[str, Any]] = []

        # 1. Parse profile.yaml
        profile_file = candidate_dir / "profile.yaml"
        if profile_file.exists():
            with open(profile_file, "r", encoding="utf-8") as f:
                prof_data = yaml.safe_load(f).get("candidate", {})

            name = prof_data.get("name", "Candidate")
            exp_years = prof_data.get("current_experience_years", "1.9+")
            role = prof_data.get("current_role", "")
            company = prof_data.get("current_company", "")
            summary = (
                f"{name} is a {role} at {company} with {exp_years} years of experience. "
                f"Primary career direction: {prof_data.get('primary_career_direction', '').strip()} "
                f"Target roles: {', '.join(prof_data.get('target_roles', []))}."
            )
            chunks.append({
                "chunk_id": "cand_profile_summary",
                "text": summary,
                "metadata": {
                    "source_file": "profile.yaml",
                    "source_section": "Candidate Profile Summary",
                    "evidence_id": "PROF_001",
                    "experience_or_project": company or "Profile",
                    "skills": "AI Data Engineer, Data Engineer, GCP Data Engineer, GenAI Engineer",
                    "technologies": "Python, SQL, GCP, BigQuery, Airflow, Vertex AI",
                    "evidence_status": "SUPPORTED",
                    "evidence_type": "professional",
                    "verified": True,
                    "allowed_for_resume": True,
                    "allowed_for_interview": True,
                }
            })

            edu = prof_data.get("education", {})
            if edu:
                edu_text = f"Education: {edu.get('degree')} from {edu.get('institution')} (Graduated {edu.get('graduation_year')}, CGPA: {edu.get('cgpa')})."
                chunks.append({
                    "chunk_id": "cand_education_01",
                    "text": edu_text,
                    "metadata": {
                        "source_file": "profile.yaml",
                        "source_section": "Education",
                        "evidence_id": "EDU_001",
                        "experience_or_project": edu.get("institution", "Education"),
                        "skills": "Artificial Intelligence, Computer Science",
                        "technologies": "AI, Statistics",
                        "evidence_status": "SUPPORTED",
                        "evidence_type": "education",
                        "verified": True,
                        "allowed_for_resume": True,
                        "allowed_for_interview": True,
                    }
                })

            for idx, cert in enumerate(prof_data.get("certifications", [])):
                chunks.append({
                    "chunk_id": f"cand_cert_{idx+1}",
                    "text": f"Certification: {cert}",
                    "metadata": {
                        "source_file": "profile.yaml",
                        "source_section": "Certifications",
                        "evidence_id": f"CERT_{idx+1}",
                        "experience_or_project": "Certifications",
                        "skills": cert,
                        "technologies": "GCP, Data Analysis, Microsoft" if "Microsoft" in cert else "GCP, Cloud",
                        "evidence_status": "SUPPORTED",
                        "evidence_type": "certification",
                        "verified": True,
                        "allowed_for_resume": True,
                        "allowed_for_interview": True,
                    }
                })

        # 2. Parse experience.md
        exp_file = candidate_dir / "experience.md"
        if exp_file.exists():
            with open(exp_file, "r", encoding="utf-8") as f:
                exp_text = f.read()

            # Extract distinct company sections
            roles = re.split(r"##\s+", exp_text)
            for role_block in roles:
                if not role_block.strip() or "Professional Experience" in role_block:
                    continue
                header = role_block.splitlines()[0].strip()
                company = "Cognizant Technology Solutions" if "Cognizant" in header else header
                
                # Extract numbered points
                items = re.findall(r"(\d+\.\s+[\s\S]*?)(?=\n\d+\.|\n##|\Z)", role_block)
                for idx, item in enumerate(items):
                    clean_item = " ".join(line.strip() for line in item.splitlines() if line.strip())
                    clean_item = re.sub(r"^\d+\.\s*", "", clean_item)
                    
                    # Detect skills in bullet
                    detected_skills = []
                    for s in ["Python", "SQL", "BigQuery", "Airflow", "Vertex AI", "Gemini 2.5 Pro", "Cloud Storage", "Pub/Sub", "Cloud Functions", "ETL", "Data Quality", "GCP"]:
                        if s.lower() in clean_item.lower():
                            detected_skills.append(s)

                    chunk_id = f"cand_exp_{company[:4].lower()}_{idx+1}_{clean_item[:15].lower().replace(' ', '_')}"
                    chunk_id = re.sub(r"[^a-zA-Z0-9_]", "", chunk_id)

                    chunks.append({
                        "chunk_id": chunk_id,
                        "text": f"{header}: {clean_item}",
                        "metadata": {
                            "source_file": "experience.md",
                            "source_section": f"Experience: {header}",
                            "evidence_id": f"EXP_{idx+1}",
                            "experience_or_project": company,
                            "skills": ", ".join(detected_skills) or "Data Engineering, GCP",
                            "technologies": ", ".join(detected_skills) or "Python, SQL, GCP",
                            "evidence_status": "SUPPORTED",
                            "evidence_type": "professional",
                            "verified": True,
                            "allowed_for_resume": True,
                            "allowed_for_interview": True,
                        }
                    })

        # 3. Parse projects.md
        proj_file = candidate_dir / "projects.md"
        if proj_file.exists():
            with open(proj_file, "r", encoding="utf-8") as f:
                proj_text = f.read()

            projects = re.split(r"##\s+\d+\.\s+", proj_text)
            for p_block in projects:
                if not p_block.strip() or "Projects — Source of Truth" in p_block:
                    continue
                lines = [l.strip() for l in p_block.splitlines() if l.strip()]
                proj_title = lines[0].strip()
                tech_line = lines[1] if len(lines) > 1 and "Technologies:" in lines[1] else ""
                techs = tech_line.replace("**Technologies:**", "").strip()

                is_personal = "Local RAG" in proj_title or "personal" in p_block.lower()
                evidence_type = "personal_project" if is_personal else "professional"

                # Extract verified evidence bullets
                body = "\n".join(lines[2:])
                bullets = [b.strip().lstrip("-*• ") for b in body.splitlines() if b.strip().startswith(("-", "*", "•"))]
                
                # Full project overview chunk
                chunks.append({
                    "chunk_id": f"cand_proj_{proj_title[:10].lower().replace(' ', '_')}_overview",
                    "text": f"Project: {proj_title}. Technologies: {techs}. Details: {' '.join(bullets)}",
                    "metadata": {
                        "source_file": "projects.md",
                        "source_section": f"Project: {proj_title}",
                        "evidence_id": f"PROJ_{proj_title[:6].upper()}",
                        "experience_or_project": proj_title,
                        "skills": techs,
                        "technologies": techs,
                        "evidence_status": "SUPPORTED",
                        "evidence_type": evidence_type,
                        "verified": True,
                        "allowed_for_resume": True,
                        "allowed_for_interview": True,
                    }
                })

                # Individual highlight bullet chunks
                for b_idx, bullet in enumerate(bullets):
                    chunks.append({
                        "chunk_id": f"cand_proj_{proj_title[:6].lower().replace(' ', '_')}_b{b_idx+1}",
                        "text": f"{proj_title} achievement: {bullet}",
                        "metadata": {
                            "source_file": "projects.md",
                            "source_section": f"Project: {proj_title}",
                            "evidence_id": f"PROJ_{proj_title[:4].upper()}_{b_idx+1}",
                            "experience_or_project": proj_title,
                            "skills": techs,
                            "technologies": techs,
                            "evidence_status": "SUPPORTED",
                            "evidence_type": evidence_type,
                            "verified": True,
                            "allowed_for_resume": True,
                            "allowed_for_interview": True,
                        }
                    })

        # 4. Parse skills.md
        skills_file = candidate_dir / "skills.md"
        if skills_file.exists():
            with open(skills_file, "r", encoding="utf-8") as f:
                skills_text = f.read()

            skill_sections = re.split(r"##\s+", skills_text)
            for s_block in skill_sections:
                if not s_block.strip() or "Candidate Skill Inventory" in s_block:
                    continue
                lines = [l.strip() for l in s_block.splitlines() if l.strip()]
                skill_name = lines[0]
                body = " ".join(lines[1:])
                
                # Check status
                status = "SUPPORTED"
                allowed_resume = True
                ev_type = "skill"
                if "NOT_SUPPORTED" in body or "not established" in body.lower() or "do not claim" in body.lower():
                    status = "NOT_SUPPORTED"
                    allowed_resume = False
                elif "transferable" in body.lower():
                    status = "PARTIALLY_SUPPORTED"
                    allowed_resume = False

                chunks.append({
                    "chunk_id": f"cand_skill_{skill_name.lower().replace(' ', '_').replace('/', '_')}",
                    "text": f"Skill: {skill_name}. Details: {body}",
                    "metadata": {
                        "source_file": "skills.md",
                        "source_section": f"Skill: {skill_name}",
                        "evidence_id": f"SKILL_{skill_name[:4].upper()}",
                        "experience_or_project": "Candidate Skill Inventory",
                        "skills": skill_name,
                        "technologies": skill_name,
                        "evidence_status": status,
                        "evidence_type": ev_type,
                        "verified": status == "SUPPORTED",
                        "allowed_for_resume": allowed_resume,
                        "allowed_for_interview": True,
                    }
                })

        # 5. Parse achievements.md
        ach_file = candidate_dir / "achievements.md"
        if ach_file.exists():
            with open(ach_file, "r", encoding="utf-8") as f:
                ach_text = f.read()

            ach_bullets = [b.strip().lstrip("-*• ") for b in ach_text.splitlines() if b.strip().startswith(("-", "*", "•"))]
            for a_idx, ach in enumerate(ach_bullets):
                detected_skills = []
                for s in ["BigQuery", "Airflow", "LLM", "Vertex AI", "Gemini", "SQL", "ETL", "Cloud Storage", "Pub/Sub", "Cloud Functions"]:
                    if s.lower() in ach.lower():
                        detected_skills.append(s)

                chunks.append({
                    "chunk_id": f"cand_achieve_{a_idx+1}",
                    "text": f"Verified metric achievement: {ach}",
                    "metadata": {
                        "source_file": "achievements.md",
                        "source_section": "Verified Achievements",
                        "evidence_id": f"ACH_{a_idx+1}",
                        "experience_or_project": "Cognizant / Verified Projects",
                        "skills": ", ".join(detected_skills) or "Data Engineering",
                        "technologies": ", ".join(detected_skills) or "Python, SQL, GCP",
                        "evidence_status": "SUPPORTED",
                        "evidence_type": "achievement",
                        "verified": True,
                        "allowed_for_resume": True,
                        "allowed_for_interview": True,
                    }
                })

        # 6. Parse evidence.json
        ev_json_file = candidate_dir / "evidence.json"
        if ev_json_file.exists():
            with open(ev_json_file, "r", encoding="utf-8") as f:
                loaded_raw = json.load(f)
                ev_data = loaded_raw if isinstance(loaded_raw, list) else loaded_raw.get("evidence", [])


            for item in ev_data:
                e_id = item.get("id", "E000")
                claim = item.get("claim", "")
                status = item.get("status", "SUPPORTED")
                src = item.get("source", "evidence.json")
                ev_type = item.get("evidence_type", "professional" if status == "SUPPORTED" else "unsupported")
                allowed_resume = item.get("allowed_for_resume", False)

                chunks.append({
                    "chunk_id": f"cand_evidence_{e_id.lower()}",
                    "text": f"Evidence Claim [{e_id}]: {claim}. Status: {status}.",
                    "metadata": {
                        "source_file": src,
                        "source_section": f"Evidence Matrix: {e_id}",
                        "evidence_id": e_id,
                        "experience_or_project": "Evidence Ledger",
                        "skills": claim,
                        "technologies": claim,
                        "evidence_status": status,
                        "evidence_type": ev_type,
                        "verified": status == "SUPPORTED",
                        "allowed_for_resume": allowed_resume,
                        "allowed_for_interview": status != "NOT_SUPPORTED",
                    }
                })

        logger.info("Parsed %d candidate evidence chunks from '%s'.", len(chunks), candidate_dir)
        return chunks

    def index_candidate_data(self, candidate_dir: Optional[Path] = None, clear_existing: bool = True) -> int:
        """
        Indexes all candidate data into ChromaDB.
        Safe against duplicates via deterministic chunk IDs and upsert.
        """
        cand_dir = candidate_dir or Path("data/candidate")
        if not cand_dir.exists():
            logger.error("Candidate directory '%s' does not exist.", cand_dir)
            return 0

        if clear_existing:
            self.clear()

        chunks = self.parse_candidate_directory(cand_dir)
        if not chunks:
            logger.warning("No candidate chunks parsed from '%s'.", cand_dir)
            return 0

        ids = [c["chunk_id"] for c in chunks]
        texts = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]

        # Generate embeddings
        embeddings = self.embedding_provider.embed_documents(texts)

        # Upsert into collection (safe against duplicates)
        self.collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        logger.info("Successfully indexed %d candidate chunks in '%s'.", len(ids), self.COLLECTION_NAME)
        return len(ids)

    def count(self) -> int:
        """Return total number of chunks indexed in candidate store."""
        return self.collection.count()
