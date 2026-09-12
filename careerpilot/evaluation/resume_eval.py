import json
from pathlib import Path
from typing import Dict, Any, List
from careerpilot.graphs.resume_graph import generate_tailored_resume
from careerpilot.truth_guard.validator import TruthValidator
from careerpilot.models.resume import ResumeStrategyType
from careerpilot.core.config import settings
from careerpilot.observability.tracer import tracer


def evaluate_resume_generation(golden_path: Path = Path("data/evaluation/resume/golden_resumes.json")) -> Dict[str, Any]:
    """
    Evaluates Resume Generation Engine for evidence grounding, metric accuracy,
    and structural integrity against golden evaluation jobs.
    """
    if not golden_path.exists():
        return {"status": "ERROR", "message": f"Dataset {golden_path} not found"}

    with open(golden_path, "r", encoding="utf-8") as f:
        golden_resumes = json.load(f)

    results = []
    grounding_scores = []
    metric_accuracies = []

    for g_res in golden_resumes:
        eval_job_file = settings.EVALUATION_JOBS_DIR / "01_ai_data_engineer.txt"
        if not eval_job_file.exists():
            continue

        with tracer.span("EVAL_RESUME", "generate_and_audit", {"strategy": g_res["strategy"]}):
            strat = ResumeStrategyType(g_res["strategy"])
            resume = generate_tailored_resume(
                job_input=eval_job_file,
                override_strategy=strat,
            )
            truth_rep = TruthValidator.validate_tailored_resume(resume)

        # 1. Section Completeness Check
        has_summary = bool(resume.summary and resume.summary.text)
        has_exp = bool(resume.experiences and len(resume.experiences) > 0)
        has_proj = bool(resume.projects and len(resume.projects) > 0)
        has_skills = bool(resume.skills_categories and len(resume.skills_categories) > 0)
        has_edu = bool(resume.education and len(resume.education) > 0)
        all_expected_present = has_summary and has_exp and has_proj and has_skills and has_edu

        # 2. Grounding Rate
        total_bullets = sum(len(e.bullets) for e in resume.experiences) + sum(len(p.bullets) for p in resume.projects)
        verified_count = truth_rep.verified_claims_count
        grounding_rate = min(1.0, verified_count / max(1, total_bullets))
        grounding_scores.append(grounding_rate)

        # 3. Metric Accuracy
        metric_acc = 1.0 if len(truth_rep.blocked_claims) == 0 else 0.0
        metric_accuracies.append(metric_acc)

        results.append({
            "case_id": g_res["case_id"],
            "strategy": g_res["strategy"],
            "all_sections_present": all_expected_present,
            "total_bullets_generated": total_bullets,
            "truth_status": truth_rep.status.value,
            "blocked_claims_count": len(truth_rep.blocked_claims),
            "grounding_rate": round(grounding_rate, 4),
        })

    return {
        "status": "SUCCESS",
        "total_resumes_evaluated": len(results),
        "average_evidence_grounding_rate": round(sum(grounding_scores) / len(grounding_scores), 4) if grounding_scores else 0.0,
        "metric_accuracy_rate": round(sum(metric_accuracies) / len(metric_accuracies), 4) if metric_accuracies else 0.0,
        "resume_evaluations": results,
    }


if __name__ == "__main__":
    res = evaluate_resume_generation()
    print("\n" + "=" * 60)
    print("  Resume Generation Engine Evaluation Results")
    print("=" * 60)
    print(json.dumps(res, indent=2))
