import pytest
from pathlib import Path
from careerpilot.parsers.jd_parser import JobDescriptionParser
from careerpilot.analysis.role_classifier import RoleClassifier
from careerpilot.analysis.evidence_matcher import EvidenceMatcher
from careerpilot.analysis.fit_scorer import CandidateJobFitScorer
from careerpilot.core.constants import MatchStatus, RequirementImportance


def test_fit_scorer_high_match():
    eval_dir = Path("data/jobs/evaluation")
    jd = JobDescriptionParser.parse_file(eval_dir / "01_ai_data_engineer.txt")
    role_class = RoleClassifier.classify(jd)
    matcher = EvidenceMatcher()

    matches = [matcher.match_requirement(req) for req in jd.requirements]
    cloud_eval = matcher.evaluate_cloud_transferability(jd)
    pref_score, _ = matcher.evaluate_preferences(jd, role_class.primary_role)

    fit = CandidateJobFitScorer.compute_fit_score(
        matches=matches,
        role_class=role_class,
        cloud_eval=cloud_eval,
        preference_score=pref_score,
        jd=jd,
    )

    assert fit.total_weighted_score >= 70.0
    assert fit.must_have_score >= 75.0
    assert fit.data_eng_score >= 80.0
    assert fit.genai_score >= 80.0
    assert "must_have" in fit.weights_used


def test_fit_scorer_must_have_penalty():
    eval_dir = Path("data/jobs/evaluation")
    jd = JobDescriptionParser.parse_file(eval_dir / "07_pure_ml_research_scientist.txt")
    role_class = RoleClassifier.classify(jd)
    matcher = EvidenceMatcher()

    matches = [matcher.match_requirement(req) for req in jd.requirements]
    cloud_eval = matcher.evaluate_cloud_transferability(jd)
    pref_score, _ = matcher.evaluate_preferences(jd, role_class.primary_role)

    fit = CandidateJobFitScorer.compute_fit_score(
        matches=matches,
        role_class=role_class,
        cloud_eval=cloud_eval,
        preference_score=pref_score,
        jd=jd,
    )

    # Pure ML research has low fit and must-have penalties
    assert fit.total_weighted_score < 60.0
    assert fit.must_have_penalty > 0
