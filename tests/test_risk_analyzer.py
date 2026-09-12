import pytest
from pathlib import Path
from careerpilot.parsers.jd_parser import JobDescriptionParser
from careerpilot.analysis.role_classifier import RoleClassifier
from careerpilot.analysis.evidence_matcher import EvidenceMatcher
from careerpilot.analysis.risk_analyzer import RiskAnalyzer
from careerpilot.core.constants import RiskType, RiskSeverity


def test_risk_analyzer_aws_heavy():
    eval_dir = Path("data/jobs/evaluation")
    jd = JobDescriptionParser.parse_file(eval_dir / "06_aws_heavy_glue_redshift_gap.txt")
    role_class = RoleClassifier.classify(jd)
    matcher = EvidenceMatcher()

    matches = [matcher.match_requirement(req) for req in jd.requirements]
    cloud_eval = matcher.evaluate_cloud_transferability(jd)

    risks = RiskAnalyzer.analyze_risks(matches, role_class, cloud_eval, jd)
    assert len(risks) > 0
    # Should flag cloud mismatch risk
    assert any(r.risk_type == RiskType.CLOUD_MISMATCH for r in risks)


def test_risk_analyzer_seniority_shortfall():
    eval_dir = Path("data/jobs/evaluation")
    jd = JobDescriptionParser.parse_file(eval_dir / "08_staff_lead_10yr_seniority_gap.txt")
    role_class = RoleClassifier.classify(jd)
    matcher = EvidenceMatcher()

    matches = [matcher.match_requirement(req) for req in jd.requirements]
    cloud_eval = matcher.evaluate_cloud_transferability(jd)

    risks = RiskAnalyzer.analyze_risks(matches, role_class, cloud_eval, jd)
    assert any(r.risk_type in (RiskType.EXPERIENCE_SHORTFALL, RiskType.SENIORITY_MISMATCH) for r in risks)
