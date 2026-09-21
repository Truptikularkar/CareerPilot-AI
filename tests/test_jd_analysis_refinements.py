import pytest
from careerpilot.parsers.jd_parser import JobDescriptionParser
from careerpilot.graphs.job_analysis_graph import analyze_job
from careerpilot.services.careerpilot_service import CareerPilotService
from careerpilot.core.constants import DecisionRecommendation, MatchStatus, RequirementImportance
from careerpilot.models.candidate import Skill, CandidateProfile
from careerpilot.core.constants import SkillCategory, RoleCategory, SeniorityLevel


def test_user_genai_pune_jd_accurate_matching():
    """
    Tests the exact scenario reported by the user:
    - Role: Genai Engineer at Acro, Pune
    - Requirements: Python, Machine Learning, HR slogan, Vertex AI, GCP
    - Expected:
      * Slogan and Location must NOT be treated as skill requirements
      * Location: Pune must score 100% (candidate is in Pune)
      * Machine Learning must match candidate's AI background
      * Fit score must be >= 75% and recommendation must be APPLY or REVIEW (NOT SKIP)
    """
    jd_text = """Job Title: Genai Engineer
Company: Acro
Location: Pune
Requirements:
- Python
- Machine Learning
- Want to change the world? Let us know. Tell us about your journey.
- Experience with Vertex AI and Google Cloud Platform (GCP)
"""
    # 1. Test parsing directly
    jd = JobDescriptionParser.parse_raw_text(jd_text)
    assert jd.location == "Pune"
    assert "Machine Learning" in jd.must_have_skills
    assert "Python" in jd.must_have_skills

    req_skills = [r.normalized_skill for r in jd.requirements]
    assert "Location: Pune" not in req_skills
    assert not any("change the world" in s.lower() for s in req_skills)

    # 2. Test end-to-end analysis via CareerPilotService
    analysis, app = CareerPilotService.analyze_job(input_source=jd_text)

    # Location score must be 100% for Pune
    assert analysis.fit_score.location_preference_score == 100.0

    # Fit score must be high, not collapsed to 45%
    assert analysis.fit_score.total_weighted_score >= 75.0

    # Must NOT be SKIP
    assert analysis.recommendation in (DecisionRecommendation.APPLY, DecisionRecommendation.REVIEW)

    # Missing required skills must NOT include Location or marketing text
    req_names_missing = [m.requirement.normalized_skill for m in analysis.matches if m.match_status == MatchStatus.GAP]
    assert not any("pune" in s.lower() for s in req_names_missing)
    assert not any("world" in s.lower() for s in req_names_missing)

    # Machine Learning must be matched
    ml_matches = [m for m in analysis.matches if "machine learning" in m.requirement.normalized_skill.lower()]
    assert len(ml_matches) > 0
    assert ml_matches[0].match_status == MatchStatus.MATCH


def test_boilerplate_and_slogan_filtering():
    """Verifies that HR filler, questions, and equal opportunity text are excluded from requirements."""
    jd_text = """Job Title: Data Engineer
Company: TestCorp
Location: Remote
What we look for:
- 3+ years of experience in SQL and Python
- Why join us? We are transforming the future of data.
- Are you ready to take your career to the next level?
- Equal Opportunity Employer: We celebrate diversity and are committed to creating an inclusive environment.
- Competitive salary, health insurance, 401(k), and paid time off.
"""
    jd = JobDescriptionParser.parse_raw_text(jd_text)
    req_skills = [r.normalized_skill for r in jd.requirements]

    assert "Python" in req_skills
    assert "SQL" in req_skills
    assert not any("equal opportunity" in s.lower() for s in req_skills)
    assert not any("why join" in s.lower() for s in req_skills)
    assert not any("are you ready" in s.lower() for s in req_skills)
    assert not any("health insurance" in s.lower() for s in req_skills)


def test_location_and_work_mode_extraction():
    """Verifies regex extraction of location and work mode."""
    cases = [
        ("Job Title: AI Engineer\nLocation: Pune (Hybrid)\nRequirements:\n- Python", "Pune", "Hybrid"),
        ("Job Title: AI Engineer\nWork Location: Remote\nRequirements:\n- Python", "Remote", "Remote"),
        ("Job Title: AI Engineer\nLocation: Bengaluru\nWork Mode: Onsite\nRequirements:\n- Python", "Bengaluru", "Onsite"),
    ]
    for text, expected_loc, expected_mode in cases:
        loc, mode = JobDescriptionParser.extract_location_and_mode(text)
        assert loc.lower() == expected_loc.lower()
        if expected_mode:
            assert mode.lower() == expected_mode.lower()


def test_dynamic_profile_update_reflected_in_matcher():
    """
    Verifies that when a candidate adds a new skill to their profile,
    the EvidenceMatcher dynamically recognizes it without requiring static YAML edits.
    """
    from careerpilot.parsers.candidate_parser import CandidateParser
    from careerpilot.analysis.evidence_matcher import EvidenceMatcher
    from careerpilot.models.job import JobRequirement
    from careerpilot.core.constants import TaxonomyCategory

    profile = CandidateParser.parse_all()
    # Add a custom newly added skill
    profile.skills.append(
        Skill(
            name="Snowflake",
            category=SkillCategory.DATABASE,
            evidence_level="PROFESSIONAL",
            evidence_status="VERIFIED",
            proficiency_level="Advanced",
            years_of_experience=2.0,
        )
    )

    matcher = EvidenceMatcher(candidate_profile=profile)
    req = JobRequirement(
        skill_name="Snowflake",
        normalized_skill="Snowflake",
        category=TaxonomyCategory.DATABASE,
        importance=RequirementImportance.MUST_HAVE,
    )
    match_result = matcher.match_requirement(req)
    assert match_result.match_status == MatchStatus.MATCH
    assert "Snowflake" in match_result.candidate_evidence_text
