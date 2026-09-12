import json
from pathlib import Path
from typing import Dict, Any
from careerpilot.evaluation.job_analysis_eval import evaluate_job_analysis
from careerpilot.evaluation.rag_eval import evaluate_rag_retrieval
from careerpilot.evaluation.truth_guard_eval import evaluate_truth_guard
from careerpilot.observability.tracer import tracer


def run_regression_suite(golden_path: Path = Path("data/evaluation/regression/golden_regression.json")) -> Dict[str, Any]:
    """
    Executes full regression evaluation comparing current outputs against baseline benchmarks.
    Detects any regressions in RAG recall, Truth Guard F1, or Job Analysis precision.
    """
    if not golden_path.exists():
        return {"status": "ERROR", "message": f"Regression baseline {golden_path} not found"}

    with open(golden_path, "r", encoding="utf-8") as f:
        baseline = json.load(f)

    # 1. Run Evaluators
    job_res = evaluate_job_analysis()
    rag_res = evaluate_rag_retrieval()
    tg_res = evaluate_truth_guard()

    # 2. Check for Regressions
    regressions = []

    # Check RAG Recall@5
    cand_recall_5 = rag_res["candidate_evidence_rag"].get("recall@5", 0.0)
    if cand_recall_5 < baseline["expected_min_rag_recall"]:
        regressions.append(f"RAG Recall@5 dropped to {cand_recall_5} (expected >= {baseline['expected_min_rag_recall']})")

    # Check Truth Guard F1
    tg_f1 = tg_res.get("f1_score", 0.0)
    if tg_f1 < baseline["expected_min_truth_guard_f1"]:
        regressions.append(f"Truth Guard F1 dropped to {tg_f1} (expected >= {baseline['expected_min_truth_guard_f1']})")

    # Check Job Analysis Role Accuracy
    job_acc = job_res.get("role_classification_accuracy", 0.0)
    if job_acc < baseline["expected_min_job_analysis_f1"]:
        regressions.append(f"Job Analysis Accuracy dropped to {job_acc} (expected >= {baseline['expected_min_job_analysis_f1']})")

    passed = len(regressions) == 0

    return {
        "status": "PASS" if passed else "REGRESSION_DETECTED",
        "regressions_count": len(regressions),
        "regressions": regressions,
        "current_metrics": {
            "rag_recall@5": cand_recall_5,
            "truth_guard_f1": tg_f1,
            "job_analysis_accuracy": job_acc,
        },
        "baseline_targets": baseline,
    }


if __name__ == "__main__":
    res = run_regression_suite()
    print("\n" + "=" * 60)
    print("  Regression Evaluation Suite Results")
    print("=" * 60)
    print(json.dumps(res, indent=2))
