import pytest
from pathlib import Path
from careerpilot.graphs.job_analysis_graph import analyze_job
from careerpilot.core.constants import DecisionRecommendation


def test_decision_engine_apply():
    eval_dir = Path("data/jobs/evaluation")
    res = analyze_job(eval_dir / "01_ai_data_engineer.txt")
    assert res.recommendation == DecisionRecommendation.APPLY
    assert res.fit_score.total_weighted_score >= 75.0
    assert len(res.key_strengths) > 0
    assert len(res.explainable_reasoning) > 0


def test_decision_engine_transferable_aws():
    eval_dir = Path("data/jobs/evaluation")
    res = analyze_job(eval_dir / "05_aws_data_engineer_transferable.txt")
    # Transferable AWS should be either APPLY or REVIEW, never automatic SKIP
    assert res.recommendation in (DecisionRecommendation.APPLY, DecisionRecommendation.REVIEW)


def test_decision_engine_skip():
    eval_dir = Path("data/jobs/evaluation")
    res = analyze_job(eval_dir / "07_pure_ml_research_scientist.txt")
    assert res.recommendation == DecisionRecommendation.SKIP
