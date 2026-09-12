import pytest
from pathlib import Path
from careerpilot.models.ats import ATSReport
from careerpilot.graphs.job_analysis_graph import analyze_job
from careerpilot.graphs.resume_graph import generate_tailored_resume
from careerpilot.ats.evaluator import ATSEvaluator


def test_ats_evaluator_ai_data_engineer():
    eval_file = Path("data/jobs/evaluation/01_ai_data_engineer.txt")
    analysis = analyze_job(eval_file)
    resume = generate_tailored_resume(analysis)

    report = ATSEvaluator.evaluate_resume(resume, analysis)

    assert report is not None
    assert isinstance(report, ATSReport)
    # Score should be strong for target matching JD (> 85.0)
    assert report.overall_score >= 85.0
    assert report.score_interpretation in ("Excellent ATS-Style Alignment", "Strong Alignment")

    # Check 7 components
    assert "keyword_coverage" in report.components
    assert "skill_taxonomy" in report.components
    assert "semantic_alignment" in report.components
    assert "experience_alignment" in report.components
    assert "structure" in report.components
    assert "formatting" in report.components
    assert "readability" in report.components

    # Check coverage ratios
    assert "10/10" in report.must_have_coverage_ratio or "9/10" in report.must_have_coverage_ratio
    assert len(report.coverage_matrix) >= 10
    assert report.interview_seed is not None
