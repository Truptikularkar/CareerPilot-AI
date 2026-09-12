import json
from pathlib import Path
from typing import Dict, Any, List
from careerpilot.truth_guard.validator import TruthValidator
from careerpilot.models.resume import (
    TailoredResume,
    ResumeStrategy,
    ResumeSummary,
    ResumeExperienceEntry,
    ResumeProjectEntry,
    ResumeStrategyType,
)
from careerpilot.observability.tracer import tracer


def evaluate_truth_guard(golden_path: Path = Path("data/evaluation/truth_guard/golden_truth_cases.json")) -> Dict[str, Any]:
    """
    Evaluates Truth Guard engine against golden test cases containing supported claims,
    unsupported technologies, inflated metrics, and boundary violations.
    """
    if not golden_path.exists():
        return {"status": "ERROR", "message": f"Dataset {golden_path} not found"}

    with open(golden_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    tp = 0  # Hallucination correctly BLOCKED
    fp = 0  # Valid claim incorrectly BLOCKED
    tn = 0  # Valid claim correctly PASSED
    fn = 0  # Hallucination incorrectly PASSED

    results = []

    for item in cases:
        claim_text = item["claim_text"]
        is_hallucination = item["is_hallucination"]
        expected_verdict = item["expected_verdict"]

        # Build schema-compliant TailoredResume
        is_proj = "PROJECT" in item["claim_type"] and not is_hallucination
        test_resume = TailoredResume(
            id=f"eval_res_{item['case_id']}",
            job_id="job_eval_01",
            candidate_id="alex_rivera_demo",
            strategy=ResumeStrategy(
                strategy_type=ResumeStrategyType.DATA_ENGINEER,
                target_role="Data Engineer",
            ),
            summary=ResumeSummary(
                text=claim_text if "SENIORITY" in item["claim_type"] else "Experienced engineer.",
                target_title="Data Engineer",
            ),
            experiences=[
                ResumeExperienceEntry(
                    company="Apex Cloud Solutions",
                    title="Data Engineer",
                    bullets=[claim_text] if not is_proj else ["Developed BigQuery pipelines."]
                )
            ],
            projects=[
                ResumeProjectEntry(
                    name="Hybrid RAG Sandbox",
                    bullets=[claim_text] if is_proj else ["Built local vector search sandbox."]
                )
            ]
        )

        with tracer.span("EVAL_TRUTH_GUARD", "audit_claim", {"case_id": item["case_id"]}):
            report = TruthValidator.validate_tailored_resume(test_resume)

        actual_verdict = report.status.value  # "PASS" or "BLOCK"
        
        # Classification evaluation
        blocked = (actual_verdict == "BLOCK" or len(report.blocked_claims) > 0)
        
        if is_hallucination and blocked:
            tp += 1
            outcome = "TP (Correctly Blocked)"
        elif not is_hallucination and not blocked:
            tn += 1
            outcome = "TN (Correctly Passed)"
        elif not is_hallucination and blocked:
            fp += 1
            outcome = "FP (False Alarm)"
        else:  # is_hallucination and not blocked
            fn += 1
            outcome = "FN (Missed Hallucination)"

        results.append({
            "case_id": item["case_id"],
            "description": item["description"],
            "expected_verdict": expected_verdict,
            "actual_verdict": "BLOCK" if blocked else "PASS",
            "outcome": outcome,
            "blocked_reasons": [c.violation_reason for c in report.blocked_claims],
        })

    total = len(cases)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / total if total > 0 else 0.0

    return {
        "status": "SUCCESS",
        "total_cases": total,
        "confusion_matrix": {
            "true_positives": tp,
            "true_negatives": tn,
            "false_positives": fp,
            "false_negatives": fn,
        },
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "accuracy": round(accuracy, 4),
        "case_breakdown": results,
    }


if __name__ == "__main__":
    res = evaluate_truth_guard()
    print("\n" + "=" * 60)
    print("  Truth Guard Engine Evaluation Results")
    print("=" * 60)
    print(json.dumps(res, indent=2))
