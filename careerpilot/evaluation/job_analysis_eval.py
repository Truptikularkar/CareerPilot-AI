import json
from pathlib import Path
from typing import Dict, Any, List
from careerpilot.parsers.jd_parser import JobDescriptionParser
from careerpilot.analysis.role_classifier import RoleClassifier, RoleRealityAnalyzer
from careerpilot.core.config import settings
from careerpilot.observability.tracer import tracer


def calculate_precision_recall_f1(pred_set: set, gold_set: set) -> Dict[str, float]:
    """Helper computing precision, recall, and F1 between predicted and gold label sets."""
    if not pred_set and not gold_set:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0}
    if not pred_set or not gold_set:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

    intersection = pred_set.intersection(gold_set)
    precision = len(intersection) / len(pred_set)
    recall = len(intersection) / len(gold_set)
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def evaluate_job_analysis(golden_path: Path = Path("data/evaluation/jobs/golden_jobs.json")) -> Dict[str, Any]:
    """
    Evaluates Job Analysis engine (Role Classifier, Seniority, Requirement Extractor)
    against the ground truth golden dataset.
    """
    if not golden_path.exists():
        return {"status": "ERROR", "message": f"Dataset {golden_path} not found"}

    with open(golden_path, "r", encoding="utf-8") as f:
        golden_jobs = json.load(f)

    role_correct = 0
    seniority_correct = 0
    must_have_f1s = []
    nice_to_have_f1s = []
    tech_f1s = []
    total = len(golden_jobs)

    for g_job in golden_jobs:
        job_file = Path("data/evaluation/jobs") / g_job["filename"]
        if not job_file.exists():
            job_file = settings.EVALUATION_JOBS_DIR / g_job["filename"]
        if not job_file.exists():
            continue


        with tracer.span("EVAL_JOB_ANALYSIS", "parse_and_classify", {"job": g_job["filename"]}):
            parsed_jd = JobDescriptionParser.parse_file(job_file)
            role_class = RoleClassifier.classify(parsed_jd)
            role_reality = RoleRealityAnalyzer.analyze(parsed_jd, role_class.primary_role)
            reqs = parsed_jd.requirements

        # 1. Role Category Accuracy
        pred_role = role_class.primary_role.value if hasattr(role_class.primary_role, "value") else str(role_class.primary_role)
        if pred_role == g_job["expected_role_category"]:
            role_correct += 1

        # 2. Seniority Accuracy
        pred_sen = role_class.seniority.value if hasattr(role_class.seniority, "value") else (parsed_jd.seniority_level.value if hasattr(parsed_jd.seniority_level, "value") else str(role_class.seniority))
        if pred_sen == g_job["expected_seniority"]:
            seniority_correct += 1


        # 3. Must-Haves F1
        pred_must = {s.lower() for s in (parsed_jd.must_have_skills or [r.skill_name for r in reqs if (r.importance.value if hasattr(r.importance, "value") else str(r.importance)) == "MUST_HAVE"])}
        gold_must = {s.lower() for s in g_job["expected_must_haves"]}
        m_metrics = calculate_precision_recall_f1(pred_must, gold_must)
        must_have_f1s.append(m_metrics["f1"])

        # 4. Nice-to-Haves F1
        pred_nice = {s.lower() for s in (parsed_jd.nice_to_have_skills or [r.skill_name for r in reqs if (r.importance.value if hasattr(r.importance, "value") else str(r.importance)) == "NICE_TO_HAVE"])}
        gold_nice = {s.lower() for s in g_job["expected_nice_to_haves"]}
        n_metrics = calculate_precision_recall_f1(pred_nice, gold_nice)
        nice_to_have_f1s.append(n_metrics["f1"])

        # 5. All Technologies F1
        pred_tech = {s.lower() for s in (parsed_jd.tech_stack or [r.skill_name for r in reqs])}
        gold_tech = {s.lower() for s in g_job["expected_technologies"]}
        t_metrics = calculate_precision_recall_f1(pred_tech, gold_tech)
        tech_f1s.append(t_metrics["f1"])


    return {
        "status": "SUCCESS",
        "total_jobs_evaluated": total,
        "role_classification_accuracy": round(role_correct / total, 4) if total > 0 else 0.0,
        "seniority_detection_accuracy": round(seniority_correct / total, 4) if total > 0 else 0.0,
        "must_have_extraction_avg_f1": round(sum(must_have_f1s) / len(must_have_f1s), 4) if must_have_f1s else 0.0,
        "nice_to_have_extraction_avg_f1": round(sum(nice_to_have_f1s) / len(nice_to_have_f1s), 4) if nice_to_have_f1s else 0.0,
        "technology_extraction_avg_f1": round(sum(tech_f1s) / len(tech_f1s), 4) if tech_f1s else 0.0,
    }


if __name__ == "__main__":
    res = evaluate_job_analysis()
    print("\n" + "=" * 60)
    print("  Job Analysis Engine Evaluation Results")
    print("=" * 60)
    print(json.dumps(res, indent=2))
