from careerpilot.db.session import SessionLocal, init_db
from careerpilot.db.schema import CandidateProfileDB, JobDescriptionDB
from careerpilot.parsers.candidate_parser import CandidateParser
from careerpilot.parsers.jd_parser import JobDescriptionParser


def test_db_initialization_and_crud(sample_candidate, sample_ai_jd):
    init_db()
    session = SessionLocal()
    try:
        # Save candidate profile
        cand_db = CandidateProfileDB(
            id=sample_candidate.id,
            full_name=sample_candidate.full_name,
            email=sample_candidate.email,
            professional_summary=sample_candidate.professional_summary,
            skills_json=[s.model_dump() for s in sample_candidate.skills],
        )
        session.merge(cand_db)

        # Save job description
        job_db = JobDescriptionDB(
            id=sample_ai_jd.id,
            company_name=sample_ai_jd.company_name,
            job_title=sample_ai_jd.job_title,
            raw_text=sample_ai_jd.raw_text,
            extracted_role=sample_ai_jd.extracted_role.value,
            estimated_seniority=sample_ai_jd.estimated_seniority.value,
            tech_stack_json=sample_ai_jd.tech_stack,
        )
        session.merge(job_db)
        session.commit()

        # Query back
        retrieved_cand = session.query(CandidateProfileDB).filter_by(id=sample_candidate.id).first()
        assert retrieved_cand is not None
        assert retrieved_cand.full_name == sample_candidate.full_name

        retrieved_job = session.query(JobDescriptionDB).filter_by(id=sample_ai_jd.id).first()
        assert retrieved_job is not None
        assert retrieved_job.company_name == sample_ai_jd.company_name

    finally:
        session.close()
