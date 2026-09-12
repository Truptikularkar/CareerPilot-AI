import pytest
from pathlib import Path
from careerpilot.parsers.jd_parser import JobDescriptionParser
from careerpilot.analysis.role_classifier import RoleClassifier, RoleRealityAnalyzer, SeniorityDetector
from careerpilot.core.constants import RoleCategory, SeniorityLevel


def test_role_classifier_ai_data_engineer():
    eval_dir = Path("data/jobs/evaluation")
    jd = JobDescriptionParser.parse_file(eval_dir / "01_ai_data_engineer.txt")

    classification = RoleClassifier.classify(jd)
    assert classification.primary_role == RoleCategory.AI_DATA_ENGINEER
    assert classification.confidence >= 0.80
    assert len(classification.reasoning) > 0


def test_role_classifier_data_engineer():
    eval_dir = Path("data/jobs/evaluation")
    jd = JobDescriptionParser.parse_file(eval_dir / "02_data_engineer_gcp.txt")

    classification = RoleClassifier.classify(jd)
    assert classification.primary_role in (RoleCategory.DATA_ENGINEER, RoleCategory.GCP_DATA_ENGINEER)


def test_role_reality_work_distribution():
    eval_dir = Path("data/jobs/evaluation")
    jd = JobDescriptionParser.parse_file(eval_dir / "01_ai_data_engineer.txt")

    reality = RoleRealityAnalyzer.analyze(jd, RoleCategory.AI_DATA_ENGINEER)
    assert "Data Engineering" in reality.work_distribution
    assert "GenAI / RAG / Agents" in reality.work_distribution
    # Total sum of work distribution should be ~100%
    total = sum(reality.work_distribution.values())
    assert abs(total - 100.0) < 1.0
    assert len(reality.supporting_evidence) > 0


def test_seniority_detector():
    eval_dir = Path("data/jobs/evaluation")
    
    # 2-3 yrs mid JD
    jd_mid = JobDescriptionParser.parse_file(eval_dir / "01_ai_data_engineer.txt")
    seniority_mid = SeniorityDetector.detect(jd_mid)
    assert seniority_mid.detected_seniority in (SeniorityLevel.MID, SeniorityLevel.JUNIOR)

    # 8-10 yrs staff JD
    jd_staff = JobDescriptionParser.parse_file(eval_dir / "08_staff_lead_10yr_seniority_gap.txt")
    seniority_staff = SeniorityDetector.detect(jd_staff)
    assert seniority_staff.detected_seniority in (SeniorityLevel.LEAD, SeniorityLevel.SENIOR)
    assert seniority_staff.explicit_years_required >= 8.0
