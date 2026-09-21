from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from careerpilot.core.config import settings
from careerpilot.db.schema import Base
from careerpilot.core.logging import get_logger

logger = get_logger(__name__)

if settings.DATABASE_URL:
    db_url = settings.DATABASE_URL.strip()
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    if "neon.tech" in db_url and "sslmode" not in db_url:
        delim = "&" if "?" in db_url else "?"
        db_url = f"{db_url}{delim}sslmode=require"
    SQLALCHEMY_DATABASE_URL = db_url
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
    )
else:
    # Ensure sqlite database parent directory exists
    db_path = Path(settings.SQLITE_DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{settings.SQLITE_DB_PATH}"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},  # Required for SQLite multi-threading
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Initialize database tables and seed candidate if missing."""
    from careerpilot.db.schema import CandidateProfileDB
    logger.info("Initializing database tables...")
    
    # Check if existing applications or resume_versions tables are missing new columns (SQLite only)
    if "sqlite" in str(engine.url):
        with engine.connect() as conn:
            from sqlalchemy import text
            try:
                res = conn.execute(text("PRAGMA table_info(applications)")).fetchall()
                col_names = [r[1] for r in res]
                if col_names and "job_location" not in col_names:
                    logger.info("Migrating applications table to new schema...")
                    conn.execute(text("DROP TABLE IF EXISTS applications"))
                    conn.commit()

                res_rv = conn.execute(text("PRAGMA table_info(resume_versions)")).fetchall()
                col_rv = [r[1] for r in res_rv]
                if col_rv and "pdf_file_path" not in col_rv:
                    logger.info("Migrating resume_versions table to add pdf_file_path...")
                    try:
                        conn.execute(text("ALTER TABLE resume_versions ADD COLUMN pdf_file_path VARCHAR"))
                        conn.commit()
                    except Exception:
                        conn.execute(text("DROP TABLE IF EXISTS resume_versions"))
                        conn.commit()

                res_ce = conn.execute(text("PRAGMA table_info(candidate_evidences)")).fetchall()
                col_ce = [r[1] for r in res_ce]
                if col_ce:
                    for col, c_type in [
                        ("fact_id", "VARCHAR"),
                        ("source_type", "VARCHAR"),
                        ("source_id", "VARCHAR"),
                        ("source_document", "VARCHAR"),
                        ("section", "VARCHAR"),
                        ("evidence_status", "VARCHAR"),
                        ("updated_at", "DATETIME"),
                    ]:
                        if col not in col_ce:
                            try:
                                conn.execute(text(f"ALTER TABLE candidate_evidences ADD COLUMN {col} {c_type}"))
                                conn.commit()
                            except Exception:
                                pass
                    # Backfill if fact_id was null
                    conn.execute(text("UPDATE candidate_evidences SET fact_id = id WHERE fact_id IS NULL"))
                    conn.execute(text("UPDATE candidate_evidences SET section = source_section WHERE section IS NULL"))
                    conn.execute(text("UPDATE candidate_evidences SET source_type = 'PROFESSIONAL_EXPERIENCE' WHERE source_type IS NULL"))
                    conn.commit()

                res_app = conn.execute(text("PRAGMA table_info(applications)")).fetchall()
                col_app = [r[1] for r in res_app]
                if col_app:
                    for col, c_type in [
                        ("canonical_job_id", "VARCHAR"),
                        ("source", "VARCHAR"),
                        ("resume_version", "VARCHAR"),
                        ("recruiter", "VARCHAR"),
                        ("final_outcome", "VARCHAR"),
                        ("status_history_json", "JSON"),
                    ]:
                        if col not in col_app:
                            try:
                                conn.execute(text(f"ALTER TABLE applications ADD COLUMN {col} {c_type}"))
                                conn.commit()
                            except Exception:
                                pass
                res_cp = conn.execute(text("PRAGMA table_info(candidate_profiles)")).fetchall()
                col_cp = [r[1] for r in res_cp]
                if col_cp and "user_id" not in col_cp:
                    try:
                        conn.execute(text("ALTER TABLE candidate_profiles ADD COLUMN user_id VARCHAR"))
                        conn.commit()
                    except Exception:
                        pass
            except Exception as e:
                logger.warning(f"Migration error: {e}")




    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        from careerpilot.parsers.candidate_parser import CandidateParser
        from careerpilot.parsers.evidence_extractor import EvidenceExtractor
        from careerpilot.db.schema import CandidateEvidenceDB, ProfileVersionDB

        cand_verified = db.query(CandidateProfileDB).filter(CandidateProfileDB.id == "trupti_kularkar").first()
        parsed_p = CandidateParser.parse_all()

        if not cand_verified:
            cand_verified = CandidateProfileDB(
                id="trupti_kularkar",
                full_name=parsed_p.full_name,
                email=parsed_p.email,
                phone=parsed_p.phone,
                linkedin_url=parsed_p.linkedin_url,
                github_url=parsed_p.github_url,
                professional_summary=parsed_p.professional_summary,
                skills_json=[s.model_dump() for s in parsed_p.skills],
                experiences_json=[e.model_dump() for e in parsed_p.experiences],
                projects_json=[p.model_dump() for p in parsed_p.projects],
                education_json=[ed.model_dump() for ed in parsed_p.education],
                certifications_json=list(parsed_p.certifications),
                achievements_json=[a.model_dump() for a in parsed_p.achievements],
                preferences_json=parsed_p.preferences.model_dump(),
            )
            db.add(cand_verified)
            db.commit()
            db.refresh(cand_verified)
        elif not cand_verified.experiences_json or not cand_verified.skills_json:
            cand_verified.skills_json = [s.model_dump() for s in parsed_p.skills]
            cand_verified.experiences_json = [e.model_dump() for e in parsed_p.experiences]
            cand_verified.projects_json = [p.model_dump() for p in parsed_p.projects]
            cand_verified.education_json = [ed.model_dump() for ed in parsed_p.education]
            cand_verified.certifications_json = list(parsed_p.certifications)
            cand_verified.achievements_json = [a.model_dump() for a in parsed_p.achievements]
            cand_verified.preferences_json = parsed_p.preferences.model_dump()
            db.commit()
        else:
            # Synchronize canonical education, projects, skills and experiences
            if any("Savitribai" in str(ed) for ed in (cand_verified.education_json or [])) or any("70%" in str(p) for p in (cand_verified.projects_json or [])) or len(cand_verified.experiences_json or []) < 2:
                cand_verified.education_json = [ed.model_dump() for ed in parsed_p.education]
                cand_verified.experiences_json = [e.model_dump() for e in parsed_p.experiences]
                cand_verified.projects_json = [p.model_dump() for p in parsed_p.projects]
                cand_verified.skills_json = [s.model_dump() for s in parsed_p.skills]
                db.commit()



        # Ensure initial version snapshot exists
        init_ver = db.query(ProfileVersionDB).filter(ProfileVersionDB.candidate_id == "trupti_kularkar").first()
        if not init_ver:
            db.add(
                ProfileVersionDB(
                    id="pver_init_v1",
                    candidate_id="trupti_kularkar",
                    version_tag="v1.0",
                    profile_json=parsed_p.model_dump(),
                    change_summary="Initial master profile baseline",
                    changed_sections_json=["all"],
                )
            )
            db.commit()
        else:
            init_ver.profile_json = parsed_p.model_dump()
            db.commit()

        # Ensure default UserDB exists and is linked to candidate profile
        from careerpilot.db.schema import UserDB
        from argon2 import PasswordHasher
        ph = PasswordHasher()

        target_email = "kularkartrupti123@gmail.com"
        target_password = ph.hash("9834055766@Liza")

        trupti_user = db.query(UserDB).filter(
            (UserDB.email == target_email) | (UserDB.email == "kularkartrupti@gmail.com")
        ).first()
        if not trupti_user:
            trupti_user = UserDB(
                id="usr_trupti_kularkar",
                email=target_email,
                password_hash=target_password,
                full_name="Trupti Kularkar",
                is_active=True,
            )
            db.add(trupti_user)
            db.commit()
            db.refresh(trupti_user)
        else:
            trupti_user.email = target_email
            trupti_user.password_hash = target_password
            db.commit()

        if cand_verified and not cand_verified.user_id:
            cand_verified.user_id = trupti_user.id
            db.commit()


    logger.info("Database tables initialized successfully.")





from contextlib import contextmanager


@contextmanager
def get_db():
    """Context manager / generator for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


get_db_session = get_db


