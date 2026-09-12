import pytest
from pathlib import Path
from careerpilot.graphs.job_analysis_graph import analyze_job, build_job_analysis_graph
from careerpilot.core.constants import DecisionRecommendation, RoleCategory


def test_job_analysis_graph_compilation():
    graph = build_job_analysis_graph()
    assert graph is not None


def test_eval_dataset_all_10_jobs():
    eval_dir = Path("data/jobs/evaluation")
    assert eval_dir.exists()

    job_files = sorted(list(eval_dir.glob("*.txt")))
    assert len(job_files) == 10, f"Expected 10 evaluation JDs, found {len(job_files)}"

    results = []
    for jf in job_files:
        res = analyze_job(jf)
        assert res.job_id != ""
        assert res.fit_score.total_weighted_score >= 0.0
        assert res.recommendation in (
            DecisionRecommendation.APPLY,
            DecisionRecommendation.REVIEW,
            DecisionRecommendation.SKIP,
        )
        assert len(res.role_reality.work_distribution) > 0
        results.append(res)

    # Specific asserts on key test cases
    # 01 AI Data Engineer -> High fit, APPLY
    assert results[0].recommendation == DecisionRecommendation.APPLY
    assert results[0].role_classification.primary_role == RoleCategory.AI_DATA_ENGINEER

    # 02 Data Engineer GCP -> High fit, APPLY
    assert results[1].recommendation == DecisionRecommendation.APPLY

    # 03 GenAI RAG Engineer -> High fit, APPLY
    assert results[2].recommendation == DecisionRecommendation.APPLY

    # 04 GCP Cloud Data Engineer -> High fit, APPLY
    assert results[3].recommendation == DecisionRecommendation.APPLY

    # 05 AWS Transferable -> APPLY or REVIEW
    assert results[4].recommendation in (DecisionRecommendation.APPLY, DecisionRecommendation.REVIEW)

    # 07 Pure ML Research Scientist -> SKIP
    assert results[6].recommendation == DecisionRecommendation.SKIP

    # 08 Staff Lead 10yr -> REVIEW or SKIP
    assert results[7].recommendation in (DecisionRecommendation.REVIEW, DecisionRecommendation.SKIP)
