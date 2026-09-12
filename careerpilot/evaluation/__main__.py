import sys
import json
from careerpilot.evaluation.job_analysis_eval import evaluate_job_analysis
from careerpilot.evaluation.rag_eval import evaluate_rag_retrieval
from careerpilot.evaluation.truth_guard_eval import evaluate_truth_guard
from careerpilot.evaluation.resume_eval import evaluate_resume_generation
from careerpilot.evaluation.interview_eval import evaluate_interview_engine
from careerpilot.evaluation.regression import run_regression_suite
from careerpilot.observability.tracer import tracer


def run_all_evaluations():
    """Runs full benchmark suite across all evaluation modules and outputs summary."""
    print("=" * 70)
    print("  CareerPilot AI — Comprehensive AI & RAG Evaluation Suite")
    print("=" * 70)

    print("\n[1/6] Running Job Analysis Evaluation...")
    job_res = evaluate_job_analysis()
    print(f"      - Role Classification Accuracy: {job_res.get('role_classification_accuracy', 0.0) * 100:.1f}%")
    print(f"      - Must-Have Extraction Avg F1:  {job_res.get('must_have_extraction_avg_f1', 0.0) * 100:.1f}%")

    print("\n[2/6] Running RAG Retrieval Evaluation...")
    rag_res = evaluate_rag_retrieval()
    cand_rag = rag_res.get("candidate_evidence_rag", {})
    know_rag = rag_res.get("technical_knowledge_rag", {})
    print(f"      - Candidate Store Recall@5:      {cand_rag.get('recall@5', 0.0) * 100:.1f}% (MRR: {cand_rag.get('mrr', 0.0):.3f})")
    print(f"      - Knowledge Store Recall@5:      {know_rag.get('recall@5', 0.0) * 100:.1f}% (MRR: {know_rag.get('mrr', 0.0):.3f})")

    print("\n[3/6] Running Truth Guard Benchmark...")
    tg_res = evaluate_truth_guard()
    print(f"      - Truth Guard Precision:         {tg_res.get('precision', 0.0) * 100:.1f}%")
    print(f"      - Truth Guard Recall:            {tg_res.get('recall', 0.0) * 100:.1f}%")
    print(f"      - Truth Guard F1 Score:          {tg_res.get('f1_score', 0.0) * 100:.1f}%")

    print("\n[4/6] Running Resume Generation Evaluation...")
    res_res = evaluate_resume_generation()
    print(f"      - Evidence Grounding Rate:       {res_res.get('average_evidence_grounding_rate', 0.0) * 100:.1f}%")
    print(f"      - Metric Accuracy Rate:          {res_res.get('metric_accuracy_rate', 0.0) * 100:.1f}%")

    print("\n[5/6] Running Interview Engine Evaluation...")
    int_res = evaluate_interview_engine()
    print(f"      - Question Relevance Rate:       {int_res.get('question_relevance_rate', 0.0) * 100:.1f}%")
    print(f"      - Adaptive Routing Verified:     {int_res.get('adaptive_routing_rule_verification', {}).get('all_routing_rules_verified', False)}")

    print("\n[6/6] Running Regression Baseline Check...")
    reg_res = run_regression_suite()
    print(f"      - Regression Status:             {reg_res.get('status', 'UNKNOWN')}")

    latency_summary = tracer.get_latency_summary()
    print("\n" + "=" * 70)
    print("  Measured Execution Latencies (ms)")
    print("=" * 70)
    for op, stats in latency_summary.items():
        print(f"  {op:<30} | Avg: {stats['avg_ms']:>6.1f}ms | Median: {stats['median_ms']:>6.1f}ms | P95: {stats['p95_ms']:>6.1f}ms")

    print("\n" + "=" * 70)
    print("  Evaluation Completed Successfully!")
    print("=" * 70 + "\n")

    return {
        "job_analysis": job_res,
        "rag_retrieval": rag_res,
        "truth_guard": tg_res,
        "resume_generation": res_res,
        "interview_engine": int_res,
        "regression": reg_res,
        "latencies": latency_summary,
    }


if __name__ == "__main__":
    arg = sys.argv[1].lower() if len(sys.argv) > 1 else "all"

    if arg in ("job_analysis", "job", "jobs"):
        print(json.dumps(evaluate_job_analysis(), indent=2))
    elif arg in ("rag", "retrieval"):
        print(json.dumps(evaluate_rag_retrieval(), indent=2))
    elif arg in ("truth_guard", "truth"):
        print(json.dumps(evaluate_truth_guard(), indent=2))
    elif arg in ("resume", "resumes"):
        print(json.dumps(evaluate_resume_generation(), indent=2))
    elif arg in ("interview", "interviews"):
        print(json.dumps(evaluate_interview_engine(), indent=2))
    elif arg in ("regression", "reg"):
        print(json.dumps(run_regression_suite(), indent=2))
    else:
        run_all_evaluations()
