import pytest
from careerpilot.models.ats import ATSReport, ATSScoreComponent
from careerpilot.core.constants import TruthValidationStatus
from careerpilot.models.job import JobAnalysisResult
from careerpilot.parsers.jd_parser import JobDescriptionParser
from careerpilot.graphs.job_analysis_graph import analyze_job
from careerpilot.graphs.resume_graph import generate_tailored_resume
from careerpilot.ats.evaluator import ATSEvaluator
from careerpilot.core.config import settings


def test_ats_report_component_properties():
    """Verify that ATSReport exposes all 7 component properties and aliases cleanly."""
    c1 = ATSScoreComponent(
        name="Keyword & Requirement Coverage",
        score=95.5,
        weight=0.25,
        weighted_score=23.88,
        explanation="High keyword match",
    )
    c3 = ATSScoreComponent(
        name="Semantic Role Alignment",
        score=90.0,
        weight=0.15,
        weighted_score=13.5,
        explanation="Semantic match",
    )
    c4 = ATSScoreComponent(
        name="Experience & Seniority Alignment",
        score=100.0,
        weight=0.15,
        weighted_score=15.0,
        explanation="Junior match",
    )
    c6 = ATSScoreComponent(
        name="Formatting & Layout Compatibility",
        score=98.0,
        weight=0.10,
        weighted_score=9.8,
        explanation="Clean formatting",
    )

    report = ATSReport(
        resume_id="res_test_123",
        job_id="job_test_123",
        job_title="Data Engineer",
        target_strategy="DATA_ENGINEER",
        overall_score=96.7,
        score_interpretation="Excellent ATS-Style Alignment",
        components={
            "keyword_coverage": c1,
            "semantic_alignment": c3,
            "experience_alignment": c4,
            "formatting": c6,
        },
        truth_status=TruthValidationStatus.PASS,
    )

    # 1. Test direct score and property access
    assert report.overall_score == 96.7
    assert report.score == 96.7
    
    # 2. Test keyword alignment and coverage properties
    assert report.keyword_coverage is not None
    assert report.keyword_coverage.score == 95.5
    assert report.keyword_alignment is not None
    assert report.keyword_alignment.score == 95.5
    assert report.keyword_alignment.keyword_score == 95.5

    # 3. Test semantic alignment property
    assert report.semantic_alignment is not None
    assert report.semantic_alignment.score == 90.0

    # 4. Test experience alignment property
    assert report.experience_alignment is not None
    assert report.experience_alignment.score == 100.0

    # 5. Test formatting property
    assert report.formatting is not None
    assert report.formatting.score == 98.0

    # 6. Test missing optional component returns None without raising AttributeError
    assert report.skill_taxonomy is None
    assert report.structure is None
    assert report.readability is None


def test_resume_builder_ats_integration():
    """Verify that end-to-end resume generation produces an ATSReport that Resume Builder can read without errors."""
    eval_job_file = settings.EVALUATION_JOBS_DIR / "01_ai_data_engineer.txt"
    analysis = analyze_job(eval_job_file)
    resume = generate_tailored_resume(analysis)
    ats_report = ATSEvaluator.evaluate_resume(resume, analysis)

    assert isinstance(ats_report, ATSReport)
    assert ats_report.overall_score > 0.0

    # Test all metrics read by Resume Builder (pages/4_Resume_Builder.py)
    score_str = f"{ats_report.overall_score:.1f}%"
    kw_str = f"{ats_report.keyword_alignment.score:.1f}%" if ats_report.keyword_alignment else "N/A"
    sem_str = f"{ats_report.semantic_alignment.score:.1f}%" if ats_report.semantic_alignment else "N/A"
    exp_str = f"{ats_report.experience_alignment.score:.1f}%" if ats_report.experience_alignment else "N/A"
    fmt_str = f"{ats_report.formatting.score:.1f}%" if ats_report.formatting else "N/A"
    truth_str = ats_report.truth_status.value if hasattr(ats_report.truth_status, "value") else str(ats_report.truth_status)

    assert "%" in score_str
    assert "%" in kw_str
    assert "%" in sem_str
    assert "%" in exp_str
    assert "%" in fmt_str
    assert truth_str in ("PASS", "BLOCK", "TruthValidationStatus.PASS", "TruthValidationStatus.BLOCK")
