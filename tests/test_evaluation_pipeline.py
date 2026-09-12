import pytest
from careerpilot.evaluation.job_analysis_eval import evaluate_job_analysis
from careerpilot.evaluation.rag_eval import evaluate_rag_retrieval
from careerpilot.evaluation.truth_guard_eval import evaluate_truth_guard
from careerpilot.evaluation.resume_eval import evaluate_resume_generation
from careerpilot.evaluation.interview_eval import evaluate_interview_engine
from careerpilot.evaluation.regression import run_regression_suite


def test_job_analysis_evaluation_runner():
    res = evaluate_job_analysis()
    assert res["status"] == "SUCCESS"
    assert res["total_jobs_evaluated"] == 10
    assert res["role_classification_accuracy"] >= 0.80
    assert res["must_have_extraction_avg_f1"] >= 0.30


def test_rag_retrieval_evaluation_runner():
    res = evaluate_rag_retrieval()
    assert res["status"] == "SUCCESS"
    assert "candidate_evidence_rag" in res
    assert "technical_knowledge_rag" in res
    assert res["candidate_evidence_rag"]["recall@5"] >= 0.90
    assert res["candidate_evidence_rag"]["mrr"] >= 0.80


def test_truth_guard_evaluation_runner():
    res = evaluate_truth_guard()
    assert res["status"] == "SUCCESS"
    assert res["total_cases"] == 12
    assert res["precision"] >= 0.95
    assert res["recall"] >= 0.95
    assert res["f1_score"] >= 0.95


def test_resume_generation_evaluation_runner():
    res = evaluate_resume_generation()
    assert res["status"] == "SUCCESS"
    assert res["total_resumes_evaluated"] > 0
    assert res["metric_accuracy_rate"] == 1.0


def test_interview_engine_evaluation_runner():
    res = evaluate_interview_engine()
    assert res["status"] == "SUCCESS"
    assert res["total_questions_evaluated"] == 5
    assert res["adaptive_routing_rule_verification"]["all_routing_rules_verified"] is True


def test_regression_evaluation_suite():
    res = run_regression_suite()
    assert res["status"] == "PASS"
    assert res["regressions_count"] == 0
