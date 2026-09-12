import pytest
from careerpilot.core.constants import (
    EvidenceStatus,
    EvidenceType,
    SeniorityLevel,
    RoleCategory,
    RequirementType,
    DecisionRecommendation,
    ResumeStrategyType,
    QuestionCategory,
    InterviewDifficulty,
)
from careerpilot.models.evidence import CandidateEvidence, VerificationResult
from careerpilot.models.candidate import CandidateProfile, Skill, Experience, Project, Education
from careerpilot.models.job import JobDescription, JobRequirement, MatchScore, JobAnalysis
from careerpilot.models.resume import TailoredResume, ResumeStrategy, ATSReport
from careerpilot.models.interview import InterviewQuestion, GroundedAnswer, MockSession


def test_candidate_evidence_creation():
    ev = CandidateEvidence(
        candidate_id="cand_123",
        evidence_type=EvidenceType.WORK_EXPERIENCE,
        source_section="Experience: Senior AI Engineer",
        content="Architected RAG system serving 45k monthly users",
        skill_tags=["Python", "RAG", "LangChain"],
        metrics=["45,000 monthly users"],
        status=EvidenceStatus.SUPPORTED,
    )
    assert ev.evidence_type == EvidenceType.WORK_EXPERIENCE
    assert ev.status == EvidenceStatus.SUPPORTED
    assert len(ev.metrics) == 1
    assert "Python" in ev.skill_tags


def test_job_description_model():
    req = JobRequirement(
        title="5+ years Python",
        requirement_type=RequirementType.MUST_HAVE,
        category="Programming",
        description="Must have 5+ years writing production Python.",
        target_skills=["Python"],
    )
    jd = JobDescription(
        raw_text="Job text here...",
        company_name="TechCorp",
        job_title="Senior AI Engineer",
        extracted_role=RoleCategory.AI_ENGINEER,
        estimated_seniority=SeniorityLevel.SENIOR,
        must_have_skills=["Python", "FastAPI"],
        requirements=[req],
    )
    assert jd.company_name == "TechCorp"
    assert jd.extracted_role == RoleCategory.AI_ENGINEER
    assert len(jd.requirements) == 1


def test_job_analysis_model():
    scores = MatchScore(
        overall_fit_score=92.5,
        must_have_score=95.0,
        nice_to_have_score=85.0,
        seniority_fit_score=100.0,
        experience_fit_score=90.0,
    )
    analysis = JobAnalysis(
        job_id="job_001",
        candidate_id="cand_001",
        scores=scores,
        matched_skills=["Python", "RAG", "FastAPI"],
        key_strengths=["Strong production RAG experience"],
        recommendation=DecisionRecommendation.APPLY,
        explainable_reasoning="Candidate matches 95% of must-have requirements.",
    )
    assert analysis.recommendation == DecisionRecommendation.APPLY
    assert analysis.scores.overall_fit_score == 92.5
