import pytest
from pathlib import Path
from careerpilot.graphs.job_analysis_graph import analyze_job
from careerpilot.graphs.resume_graph import generate_tailored_resume
from careerpilot.ats.evaluator import ATSEvaluator
from careerpilot.models.ats import InterviewReadinessSeed


def test_interview_readiness_seed_generation():
    eval_file = Path("data/jobs/evaluation/01_ai_data_engineer.txt")
    analysis = analyze_job(eval_file)
    resume = generate_tailored_resume(analysis)

    report = ATSEvaluator.evaluate_resume(resume, analysis)
    seed = report.interview_seed

    assert seed is not None
    assert isinstance(seed, InterviewReadinessSeed)
    assert seed.job_id == analysis.job_id
    assert "AI Data Engineer" in seed.target_role

    # Verify seed lists
    assert len(seed.high_priority_skills) > 0
    assert len(seed.candidate_strengths) > 0
    assert len(seed.likely_interview_topics) >= 3
    assert len(seed.challenged_claims) >= 2
    assert len(seed.scenario_topics) >= 2
    assert len(seed.system_design_topics) >= 1
    assert len(seed.behavioral_themes) >= 2

    # Check specific topics
    assert any("BigQuery" in t for t in seed.likely_interview_topics)
    assert any("Airflow" in t for t in seed.likely_interview_topics)
