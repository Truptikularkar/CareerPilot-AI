from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from careerpilot.core.constants import (
    QuestionCategory,
    QuestionPriority,
    DifficultyLevel,
    AnswerLengthMode,
    InterviewerPersona,
    TruthValidationStatus,
)


class InterviewQuestion(BaseModel):
    """Structured interview question with strategic rationale and intent."""
    question_id: str
    category: QuestionCategory
    subcategory: str
    question: str
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    priority: QuestionPriority = QuestionPriority.HIGH
    why_this_question: str
    source_requirements: List[str] = Field(default_factory=list)
    candidate_evidence_ids: List[str] = Field(default_factory=list)
    expected_topics: List[str] = Field(default_factory=list)
    interviewer_intent: str = ""
    follow_up_questions: List[str] = Field(default_factory=list)
    answer_template_id: Optional[str] = None


class InterviewAnswer(BaseModel):
    """Evidence-grounded interview response across multiple length modes."""
    answer_id: str
    question_id: str
    direct_answer: str
    explanation: str
    candidate_example: str
    technical_details: str
    result_impact: str
    possible_followup: str = ""
    short_version: str = ""      # 30-45 seconds
    standard_version: str = ""   # 60-90 seconds
    detailed_version: str = ""   # 2-3 minutes
    grounded_evidence_ids: List[str] = Field(default_factory=list)
    evidence_status: str = "VERIFIED"  # "VERIFIED", "INSUFFICIENT_EVIDENCE", "TRANSFERABLE"
    is_insufficient_evidence: bool = False

    @property
    def short_answer(self) -> str:
        return self.short_version or self.direct_answer

    @property
    def standard_answer(self) -> str:
        return self.standard_version or f"{self.direct_answer} {self.candidate_example}"

    @property
    def detailed_answer(self) -> str:
        return self.detailed_version or f"{self.direct_answer} {self.technical_details} {self.candidate_example} {self.result_impact}"

    @property
    def evidence_ids_used(self) -> List[str]:
        return self.grounded_evidence_ids


class STARAnswer(BaseModel):
    """Structured STAR behavioral interview answer grounded in candidate truth."""
    star_id: str
    question_id: str
    situation: str
    task: str
    action: str
    result: str
    key_takeaway: str
    competency: str = "Engineering Ownership & STAR Delivery"
    question: str = "Describe a key technical challenge you solved."
    is_insufficient_evidence: bool = False
    insufficient_evidence_reason: Optional[str] = None
    grounded_evidence_ids: List[str] = Field(default_factory=list)


class SystemDesignScenario(BaseModel):
    """Role-specific system design interview challenge."""
    scenario_id: str
    title: str
    target_role: str
    functional_requirements: List[str] = Field(default_factory=list)
    non_functional_requirements: List[str] = Field(default_factory=list)
    scale_assumptions: Any = Field(default_factory=dict)
    architecture_components: Any = ""
    data_flow: List[str] = Field(default_factory=list)
    storage: str = ""
    processing: str = ""
    orchestration: str = ""
    monitoring: str = ""
    failure_handling: str = ""
    security: str = ""
    cost_considerations: str = ""
    trade_offs: Any = Field(default_factory=list)
    follow_up_questions: List[str] = Field(default_factory=list)

    @property
    def scenario_title(self) -> str:
        return self.title

    @property
    def storage_layer(self) -> str:
        return self.storage

    @property
    def processing_layer(self) -> str:
        return self.processing


class PreparationDayPlan(BaseModel):
    """Single-day actionable interview preparation focus plan."""
    day_number: int
    title: str
    focus_areas: List[str] = Field(default_factory=list)
    target_question_ids: List[str] = Field(default_factory=list)
    practice_drills: List[str] = Field(default_factory=list)

    @property
    def theme(self) -> str:
        return self.title

    @property
    def tasks(self) -> str:
        return ", ".join(self.practice_drills) if self.practice_drills else "Practice drills and concept review."


class PreparationRoadmap(BaseModel):
    """Multi-day preparation roadmap tailored to JD gaps and candidate strengths."""
    roadmap_id: str
    title: str = "Focused Study Schedule"
    days_total: int = 7  # 1, 3, 7, or 14
    target_role: str
    daily_schedule: List[PreparationDayPlan] = Field(default_factory=list)

    @property
    def days(self) -> List[PreparationDayPlan]:
        return self.daily_schedule


class InterviewReadinessScore(BaseModel):
    """Deterministic multi-dimensional readiness scoring."""
    technical_readiness: float
    resume_confidence: float
    project_confidence: float
    gap_readiness: float
    system_design_readiness: float
    behavioral_readiness: float
    overall_readiness: float
    explanations: Dict[str, str] = Field(default_factory=dict)

    @property
    def overall_readiness_score(self) -> float:
        return self.overall_readiness


class CodingChallenge(BaseModel):
    """Hands-on coding, SQL, or algorithmic challenge for technical interviews."""
    challenge_id: str
    title: str
    category: str = "PYTHON"  # PYTHON, SQL, PYSPARK, ALGORITHMS
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    problem_statement: str
    input_format: str = ""
    output_format: str = ""
    example_input: str = ""
    example_output: str = ""
    constraints: List[str] = Field(default_factory=list)
    starter_code: str = ""
    solution_code: str = ""
    explanation: str = ""
    time_complexity: str = ""
    space_complexity: str = ""
    interviewer_focus: str = ""

    @property
    def language(self) -> str:
        return self.category


class InterviewPlan(BaseModel):
    """Complete Interview Preparation Package for a specific job description."""
    prep_id: str
    job_id: str
    job_title: str
    target_role: str
    strategy: str
    questions: List[InterviewQuestion] = Field(default_factory=list)
    answers: List[InterviewAnswer] = Field(default_factory=list)
    star_answers: List[STARAnswer] = Field(default_factory=list)
    system_designs: List[SystemDesignScenario] = Field(default_factory=list)
    coding_challenges: List[CodingChallenge] = Field(default_factory=list)
    roadmap: PreparationRoadmap
    readiness_score: InterviewReadinessScore
    truth_report: Optional[Dict[str, Any]] = None


# Backward-compatibility aliases
PrepRoadmap = PreparationRoadmap
ReadinessScore = InterviewReadinessScore
GroundedAnswer = InterviewAnswer





class MockTurn(BaseModel):
    user_message: str = ""
    ai_response: str = ""


class MockSession(BaseModel):
    session_id: str = ""
    turns: List[MockTurn] = Field(default_factory=list)

