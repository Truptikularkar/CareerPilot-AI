import uuid
from typing import Dict, Any, List, Optional, TypedDict
from pathlib import Path
from langgraph.graph import StateGraph, START, END
from careerpilot.core.config import settings
from careerpilot.models.job import JobAnalysisResult
from careerpilot.models.resume import TailoredResume
from careerpilot.models.ats import InterviewReadinessSeed
from careerpilot.models.interview import (
    InterviewQuestion,
    InterviewAnswer,
    STARAnswer,
    SystemDesignScenario,
    PreparationRoadmap,
    InterviewReadinessScore,
    InterviewPlan,
)
from careerpilot.rag.retriever import retrieve_candidate_evidence, retrieve_technical_knowledge
from careerpilot.interview.question_planner import QuestionPlanner
from careerpilot.interview.question_engine import QuestionEngine
from careerpilot.interview.answer_engine import AnswerEngine
from careerpilot.interview.star_engine import STAREngine
from careerpilot.interview.system_design import SystemDesignEngine
from careerpilot.interview.gap_handler import GapHandler
from careerpilot.interview.readiness_scorer import ReadinessScorer
from careerpilot.interview.roadmap import RoadmapGenerator
from careerpilot.interview.truth_validator import InterviewTruthValidator
from careerpilot.interview.report_exporter import InterviewReportExporter
from careerpilot.graphs.job_analysis_graph import analyze_job
from careerpilot.graphs.resume_graph import generate_tailored_resume
from careerpilot.ats.evaluator import ATSEvaluator
from careerpilot.core.logging import get_logger

logger = get_logger(__name__)


class InterviewPrepState(TypedDict, total=False):
    job_input: Any
    job_analysis: JobAnalysisResult
    tailored_resume: TailoredResume
    readiness_seed: InterviewReadinessSeed
    quotas: Dict[Any, int]
    questions: List[InterviewQuestion]
    answers: List[InterviewAnswer]
    star_answers: List[STARAnswer]
    system_designs: List[SystemDesignScenario]
    truth_report: Any
    readiness_score: InterviewReadinessScore
    roadmap: PreparationRoadmap
    days_total: int
    final_plan: InterviewPlan
    output_dir: str


def load_inputs_node(state: InterviewPrepState) -> Dict[str, Any]:
    logger.info("LangGraph Interview Node: Loading inputs and resolving Job Analysis & Resume...")
    job_input = state.get("job_input")

    # Resolve Job Analysis
    if "job_analysis" in state and state["job_analysis"]:
        analysis = state["job_analysis"]
    else:
        analysis = analyze_job(job_input)

    # Resolve Tailored Resume
    if "tailored_resume" in state and state["tailored_resume"]:
        resume = state["tailored_resume"]
    else:
        resume = generate_tailored_resume(analysis)

    # Resolve Readiness Seed
    if "readiness_seed" in state and state["readiness_seed"]:
        seed = state["readiness_seed"]
    else:
        ats_rep = ATSEvaluator.evaluate_resume(resume, analysis)
        seed = ats_rep.interview_seed

    return {
        "job_analysis": analysis,
        "tailored_resume": resume,
        "readiness_seed": seed,
    }


def retrieve_rag_evidence_node(state: InterviewPrepState) -> Dict[str, Any]:
    logger.info("LangGraph Interview Node: Retrieving Candidate and Technical RAG knowledge...")
    analysis = state["job_analysis"]
    seed = state["readiness_seed"]

    # Retrieve candidate evidence for high-priority skills
    for skill in seed.high_priority_skills[:4]:
        retrieve_candidate_evidence(query=skill, top_k=3)
        retrieve_technical_knowledge(query=skill, top_k=2)

    return {}


def plan_questions_node(state: InterviewPrepState) -> Dict[str, Any]:
    logger.info("LangGraph Interview Node: Planning question quotas...")
    analysis = state["job_analysis"]
    seed = state["readiness_seed"]
    resume = state["tailored_resume"]
    quotas = QuestionPlanner.plan_question_distribution(analysis, seed, resume)
    return {"quotas": quotas}


def generate_questions_node(state: InterviewPrepState) -> Dict[str, Any]:
    logger.info("LangGraph Interview Node: Generating core interview questions...")
    analysis = state["job_analysis"]
    resume = state["tailored_resume"]
    seed = state["readiness_seed"]
    quotas = state["quotas"]
    questions = QuestionEngine.generate_interview_questions(analysis, resume, seed, quotas)
    return {"questions": questions}


def generate_answers_node(state: InterviewPrepState) -> Dict[str, Any]:
    logger.info("LangGraph Interview Node: Generating grounded interview answers...")
    questions = state["questions"]
    answers = AnswerEngine.generate_answers_for_questions(questions)
    return {"answers": answers}


def generate_star_and_system_design_node(state: InterviewPrepState) -> Dict[str, Any]:
    logger.info("LangGraph Interview Node: Generating STAR stories and System Design scenarios...")
    analysis = state["job_analysis"]
    resume = state["tailored_resume"]
    questions = state["questions"]

    star_q, star_answers = STAREngine.generate_star_questions_and_answers()
    system_designs = SystemDesignEngine.generate_system_design_scenarios(analysis, resume)

    all_questions = questions + star_q
    return {
        "questions": all_questions,
        "star_answers": star_answers,
        "system_designs": system_designs,
    }


def generate_gap_and_followups_node(state: InterviewPrepState) -> Dict[str, Any]:
    logger.info("LangGraph Interview Node: Generating gap questions and transferability answers...")
    analysis = state["job_analysis"]
    seed = state["readiness_seed"]
    questions = state["questions"]
    answers = state["answers"]

    gap_q, gap_a = GapHandler.generate_gap_questions_and_answers(analysis, seed)

    return {
        "questions": questions + gap_q,
        "answers": answers + gap_a,
    }


def validate_truth_node(state: InterviewPrepState) -> Dict[str, Any]:
    logger.info("LangGraph Interview Node: Truth Guard validation on interview claims...")
    answers = state["answers"]
    star_answers = state["star_answers"]
    truth_rep = InterviewTruthValidator.validate_interview_answers(answers, star_answers)
    return {"truth_report": truth_rep}


def score_readiness_node(state: InterviewPrepState) -> Dict[str, Any]:
    logger.info("LangGraph Interview Node: Scoring multi-dimensional interview readiness...")
    analysis = state["job_analysis"]
    resume = state["tailored_resume"]
    seed = state["readiness_seed"]
    questions = state["questions"]
    answers = state["answers"]

    score = ReadinessScorer.score_readiness(analysis, resume, seed, questions, answers)
    return {"readiness_score": score}


def generate_roadmap_node(state: InterviewPrepState) -> Dict[str, Any]:
    logger.info("LangGraph Interview Node: Generating study roadmap...")
    analysis = state["job_analysis"]
    resume = state["tailored_resume"]
    seed = state["readiness_seed"]
    questions = state["questions"]
    days = state.get("days_total", 7)

    roadmap = RoadmapGenerator.generate_roadmap(analysis, resume, seed, questions, days_total=days)
    return {"roadmap": roadmap}


def export_artifacts_node(state: InterviewPrepState) -> Dict[str, Any]:
    logger.info("LangGraph Interview Node: Exporting all interview preparation artifacts...")
    analysis = state["job_analysis"]
    resume = state["tailored_resume"]
    questions = state["questions"]
    answers = state["answers"]
    star_answers = state["star_answers"]
    system_designs = state["system_designs"]
    roadmap = state["roadmap"]
    readiness_score = state["readiness_score"]
    truth_rep = state["truth_report"]

    prep_id = f"prep_{uuid.uuid4().hex[:8]}"
    out_dir = settings.OUTPUT_INTERVIEW_DIR / prep_id
    out_dir.mkdir(parents=True, exist_ok=True)

    final_plan = InterviewPlan(
        prep_id=prep_id,
        job_id=analysis.job_id,
        job_title=analysis.job_title,
        target_role=resume.strategy.target_role,
        strategy=resume.strategy.strategy_type.value,
        questions=questions,
        answers=answers,
        star_answers=star_answers,
        system_designs=system_designs,
        roadmap=roadmap,
        readiness_score=readiness_score,
        truth_report=truth_rep.model_dump() if truth_rep else None,
    )

    InterviewReportExporter.export_all(final_plan, out_dir)
    logger.info("Interview Preparation Plan successfully exported to: %s", out_dir)

    return {"final_plan": final_plan, "output_dir": str(out_dir)}


# -----------------------------------------------------------------------------
# Graph Construction & Compilation
# -----------------------------------------------------------------------------
builder = StateGraph(InterviewPrepState)

builder.add_node("load_inputs", load_inputs_node)
builder.add_node("retrieve_rag_evidence", retrieve_rag_evidence_node)
builder.add_node("plan_questions", plan_questions_node)
builder.add_node("generate_questions", generate_questions_node)
builder.add_node("generate_answers", generate_answers_node)
builder.add_node("generate_star_and_system_design", generate_star_and_system_design_node)
builder.add_node("generate_gap_and_followups", generate_gap_and_followups_node)
builder.add_node("validate_truth", validate_truth_node)
builder.add_node("score_readiness", score_readiness_node)
builder.add_node("generate_roadmap", generate_roadmap_node)
builder.add_node("export_artifacts", export_artifacts_node)

builder.add_edge(START, "load_inputs")
builder.add_edge("load_inputs", "retrieve_rag_evidence")
builder.add_edge("retrieve_rag_evidence", "plan_questions")
builder.add_edge("plan_questions", "generate_questions")
builder.add_edge("generate_questions", "generate_answers")
builder.add_edge("generate_answers", "generate_star_and_system_design")
builder.add_edge("generate_star_and_system_design", "generate_gap_and_followups")
builder.add_edge("generate_gap_and_followups", "validate_truth")
builder.add_edge("validate_truth", "score_readiness")
builder.add_edge("score_readiness", "generate_roadmap")
builder.add_edge("generate_roadmap", "export_artifacts")
builder.add_edge("export_artifacts", END)

interview_prep_graph = builder.compile()


def prepare_interview(
    job_input: Any,
    strategy: Optional[str] = "auto",
    days: int = 7,
) -> InterviewPlan:
    """Entrypoint function to run interview preparation graph end-to-end."""
    state = interview_prep_graph.invoke({"job_input": job_input, "days_total": days})
    return state["final_plan"]
