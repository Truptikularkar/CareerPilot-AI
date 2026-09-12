from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from careerpilot.core.constants import (
    MockInterviewMode,
    InterviewDifficulty,
    InterviewerPersona,
    HintMode,
    FeedbackMode,
    SessionStatus,
    EvaluationDimension,
)


class TruthAuditItem(BaseModel):
    """Candidate truth verification item during live interview turns."""
    claim_text: str
    status: str = "VERIFIED"  # "VERIFIED", "UNSUPPORTED_CLAIM", "METRIC_MISMATCH", "PERSONAL_PROJECT_MISMATCH"
    is_unsupported_claim: bool = False
    is_metric_mismatch: bool = False
    is_personal_project_mismatch: bool = False
    explanation: str = ""
    suggested_framing: Optional[str] = None


class AnswerEvaluation(BaseModel):
    """Structured, 10-dimensional evaluation of candidate answer."""
    evaluation_id: str
    turn_id: str
    dimension_scores: Dict[str, float] = Field(default_factory=dict)  # 0.0 to 5.0 per dimension
    overall_turn_score: float = 0.0  # 0 to 100%
    is_i_dont_know: bool = False
    hint_penalty_applied: float = 0.0
    correct_concepts: List[str] = Field(default_factory=list)
    missing_concepts: List[str] = Field(default_factory=list)
    misconceptions: List[str] = Field(default_factory=list)
    strengths_observed: List[str] = Field(default_factory=list)
    weaknesses_observed: List[str] = Field(default_factory=list)
    star_coverage: Dict[str, bool] = Field(default_factory=dict)
    system_design_coverage: Dict[str, bool] = Field(default_factory=dict)
    truth_checks: List[TruthAuditItem] = Field(default_factory=list)
    feedback: str = ""
    coaching_tip: str = ""
    suggested_followup_question: Optional[str] = None
    recommended_difficulty_shift: int = 0  # +1 (harder), 0 (maintain), -1 (easier)


class MockInterviewTurn(BaseModel):
    """Single question-answer-evaluation turn in an adaptive mock session."""
    turn_id: str
    turn_number: int
    question_id: str
    question_text: str
    category: str
    topic: str
    difficulty: str
    followup_depth: int = 0  # 0 to 4
    candidate_answer: str = ""
    hint_used: HintMode = HintMode.NO_HINT
    evaluation: Optional[AnswerEvaluation] = None
    timestamp: str = ""


class TopicMastery(BaseModel):
    """Candidate mastery tracking by technical or behavioral domain."""
    topic: str
    mastery_score: float = 0.0  # 0.0 to 5.0
    questions_asked: int = 0
    status: str = "DEVELOPING"  # "MASTERED", "PROFICIENT", "DEVELOPING", "WEAK"


class WeaknessItem(BaseModel):
    """Identified candidate knowledge or communication gap."""
    topic: str
    description: str
    evidence_turn_ids: List[str] = Field(default_factory=list)
    suggested_remedy: str = ""


class StrengthItem(BaseModel):
    """Identified candidate strength or standout answer."""
    topic: str
    description: str
    evidence_turn_ids: List[str] = Field(default_factory=list)


class JDCoverageItem(BaseModel):
    """Tracking coverage of major Job Description requirements."""
    skill_or_requirement: str
    importance: str = "MUST_HAVE"
    status: str = "NOT_COVERED"  # "COVERED", "PARTIALLY_COVERED", "NOT_COVERED"
    score: Optional[float] = None


class FinalInterviewReport(BaseModel):
    """Comprehensive final evaluation and readiness analysis for mock session."""
    session_id: str
    job_id: str
    target_role: str
    mode: MockInterviewMode
    persona: InterviewerPersona
    total_turns: int
    overall_score: float  # 0.0 to 100.0
    technical_score: float = 0.0
    communication_score: float = 0.0
    resume_knowledge_score: float = 0.0
    project_score: float = 0.0
    system_design_score: float = 0.0
    behavioral_score: float = 0.0
    problem_solving_score: float = 0.0
    experience_accuracy_score: float = 0.0
    topic_mastery: Dict[str, TopicMastery] = Field(default_factory=dict)
    strengths: List[StrengthItem] = Field(default_factory=list)
    weaknesses: List[WeaknessItem] = Field(default_factory=list)
    jd_coverage: List[JDCoverageItem] = Field(default_factory=list)
    challenging_questions: List[str] = Field(default_factory=list)
    questions_answered_well: List[str] = Field(default_factory=list)
    questions_answered_poorly: List[str] = Field(default_factory=list)
    unsupported_claims: List[TruthAuditItem] = Field(default_factory=list)
    recommended_study_topics: List[str] = Field(default_factory=list)
    recommended_next_mock_mode: MockInterviewMode = MockInterviewMode.FULL_INTERVIEW
    executive_summary: str = ""
