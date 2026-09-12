"""
CareerPilot AI — Clean Test Mock Data Script
Cleans out test runner mock data and keeps the real candidate profile (Trupti Kularkar).
"""
import shutil
from pathlib import Path
from sqlalchemy import text
from careerpilot.db.session import engine, init_db

def clean_database():
    db_path = Path("data/careerpilot.db")
    bak_path = Path("data/careerpilot.db.bak")
    
    if db_path.exists() and not bak_path.exists():
        shutil.copy(db_path, bak_path)
        print(f"Backed up {db_path} to {bak_path}")

    init_db()

    with engine.begin() as conn:
        # Keep trupti_kularkar candidate profile and cand_verified
        conn.execute(text("DELETE FROM applications"))
        conn.execute(text("DELETE FROM job_descriptions"))
        conn.execute(text("DELETE FROM job_analyses"))
        conn.execute(text("DELETE FROM resume_versions"))
        conn.execute(text("DELETE FROM interview_preparations"))
        conn.execute(text("DELETE FROM mock_sessions"))
        conn.execute(text("DELETE FROM skill_gaps"))
        conn.execute(text("DELETE FROM canonical_jobs"))
        conn.execute(text("DELETE FROM user_sessions"))

        # Clean users except usr_trupti_kularkar
        conn.execute(text("DELETE FROM users WHERE id != 'usr_trupti_kularkar'"))

        # Clean candidate profiles except trupti_kularkar and cand_verified
        conn.execute(text("DELETE FROM candidate_profiles WHERE id NOT IN ('trupti_kularkar', 'cand_verified')"))

        # Clean candidate evidences not belonging to trupti_kularkar
        conn.execute(text("DELETE FROM candidate_evidences WHERE candidate_id NOT IN ('trupti_kularkar', 'cand_verified')"))

        # Vacuum SQLite database to reclaim disk space
        print("Test mock data cleaned from SQLite database.")

    with engine.connect() as conn:
        conn.execute(text("VACUUM"))
        user_count = conn.execute(text("SELECT count(*) FROM users")).scalar()
        cand_count = conn.execute(text("SELECT count(*) FROM candidate_profiles")).scalar()
        app_count = conn.execute(text("SELECT count(*) FROM applications")).scalar()
        ev_count = conn.execute(text("SELECT count(*) FROM candidate_evidences")).scalar()
        print(f"Post-clean status: Users={user_count}, Candidates={cand_count}, Evidences={ev_count}, Applications={app_count}")

if __name__ == "__main__":
    clean_database()
