from pathlib import Path
from typing import Dict, Any, List, Optional, TypedDict, Union
from careerpilot.core.constants import (
    MockInterviewMode,
    InterviewDifficulty,
    InterviewerPersona,
    HintMode,
    FeedbackMode,
    SessionStatus,
    ResumeStrategyType,
)
from careerpilot.models.interview import InterviewQuestion
from careerpilot.models.mock_interview import (
    MockInterviewTurn,
    AnswerEvaluation,
    TopicMastery,
    WeaknessItem,
    StrengthItem,
    JDCoverageItem,
    FinalInterviewReport,
)
from careerpilot.models.job import JobAnalysisResult
from careerpilot.models.resume import (
    TailoredResume,
    ResumeStrategy,
    ResumeSummary,
    TruthValidationReport,
    ATSPrecheckResult,
)
from careerpilot.models.ats import InterviewReadinessSeed


class JobAnalysisState(TypedDict, total=False):
    """LangGraph state schema for Job Analysis and fit scoring workflow."""
    file_path: Optional[Union[str, Path]]
    raw_input: Optional[str]
    company_name: Optional[str]
    job_title: Optional[str]
    job_location: Optional[str]
    work_mode: Optional[str]
    candidate_id: Optional[str]
    candidate_profile: Optional[Any]
    job_description: Optional[Any]
    requirements: Optional[List[Any]]
    role_classification: Optional[Any]
    role_reality: Optional[Any]
    matches: Optional[List[Any]]
    cloud_transferability: Optional[Any]
    preference_score: Optional[float]
    fit_score: Optional[Any]
    risks: Optional[Any]
    risk_analysis: Optional[Any]
    analysis_result: Optional[JobAnalysisResult]
    final_analysis: Optional[JobAnalysisResult]




class ResumeGenerationState(TypedDict, total=False):
    """Typed state for the Resume Tailoring LangGraph workflow."""
    job_input: Optional[Union[str, Path]]
    job_analysis: Optional[JobAnalysisResult]
    override_strategy: Optional[Union[str, ResumeStrategyType]]
    strategy: Optional[ResumeStrategy]
    draft_resume: Optional[TailoredResume]
    truth_report: Optional[TruthValidationReport]
    ats_precheck: Optional[ATSPrecheckResult]
    tailored_resume: Optional[TailoredResume]
    markdown_path: Optional[str]
    docx_path: Optional[str]
    output_dir: Optional[str]


class MockInterviewState(TypedDict, total=False):
    """
    LangGraph state schema for multi-turn adaptive mock interview sessions.
    Persists across interactive candidate turns.
    """
    session_id: str
    job_id: str
    job_input: Optional[Union[str, Path]]
    role: str
    strategy: str
    mode: MockInterviewMode
    difficulty: InterviewDifficulty
    persona: InterviewerPersona
    feedback_mode: FeedbackMode
    hint_mode: HintMode

    # Context & References
    job_analysis: JobAnalysisResult
    tailored_resume: TailoredResume
    readiness_seed: InterviewReadinessSeed
    all_available_questions: List[InterviewQuestion]

    # Current Turn Pointers
    total_questions_planned: int
    questions_asked: int
    questions_remaining: int
    current_turn_number: int
    current_question: Optional[InterviewQuestion]
    current_question_text: str
    current_question_type: str
    current_topic: str
    current_difficulty: str
    followup_depth: int
    current_answer: str
    current_hint: HintMode
    current_evaluation: Optional[AnswerEvaluation]

    # History & Cumulative Metrics
    turns: List[MockInterviewTurn]
    question_history: List[str]
    answer_history: List[str]
    evaluation_history: List[AnswerEvaluation]
    topic_scores: Dict[str, float]
    skill_scores: Dict[str, float]
    weakness_topics: List[str]
    strength_topics: List[str]
    jd_coverage: Dict[str, str]
    candidate_confidence: float

    # Lifecycle & Reporting
    session_status: SessionStatus
    final_score: Optional[float]
    final_report: Optional[FinalInterviewReport]
    output_dir: Optional[str]
