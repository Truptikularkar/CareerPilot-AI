from pathlib import Path
from typing import Union, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END

from careerpilot.graphs.state import JobAnalysisState
from careerpilot.parsers.jd_parser import JobDescriptionParser
from careerpilot.analysis.role_classifier import RoleClassifier, RoleRealityAnalyzer
from careerpilot.analysis.evidence_matcher import EvidenceMatcher
from careerpilot.analysis.fit_scorer import CandidateJobFitScorer
from careerpilot.analysis.risk_analyzer import RiskAnalyzer
from careerpilot.analysis.decision_engine import DecisionEngine
from careerpilot.models.job import JobAnalysisResult
from careerpilot.core.logging import get_logger

logger = get_logger(__name__)


# -----------------------------------------------------------------------------
# Graph Node Functions
# -----------------------------------------------------------------------------

def parse_jd_node(state: JobAnalysisState) -> Dict[str, Any]:
    """Node 1: Parses raw text or file into structured JobDescription."""
    logger.info("LangGraph Node: Parsing Job Description...")
    file_path = state.get("file_path")
    raw_input = state.get("raw_input")
    company_name = state.get("company_name")
    job_title = state.get("job_title")
    job_location = state.get("job_location")
    work_mode = state.get("work_mode")

    if file_path:
        jd = JobDescriptionParser.parse_file(
            file_path,
            company_name=company_name,
            job_title=job_title,
            location=job_location,
            work_mode=work_mode,
        )
    elif raw_input:
        jd = JobDescriptionParser.parse_raw_text(
            raw_input,
            company_name=company_name,
            job_title=job_title,
            location=job_location,
            work_mode=work_mode,
        )
    else:
        raise ValueError("JobAnalysisState must contain either 'raw_input' or 'file_path'.")

    return {"job_description": jd, "requirements": jd.requirements}


def classify_role_node(state: JobAnalysisState) -> Dict[str, Any]:
    """Node 2: Classifies actual role family, seniority, and work reality."""
    logger.info("LangGraph Node: Classifying Role & Reality...")
    jd = state["job_description"]
    role_class = RoleClassifier.classify(jd)
    role_reality = RoleRealityAnalyzer.analyze(jd, role_class.primary_role)
    return {
        "role_classification": role_class,
        "role_reality": role_reality,
    }


def extract_requirements_node(state: JobAnalysisState) -> Dict[str, Any]:
    """Node 3: Formats and verifies extracted structured requirements."""
    logger.info("LangGraph Node: Extracting Requirements...")
    jd = state["job_description"]
    return {"requirements": jd.requirements}


def retrieve_evidence_node(state: JobAnalysisState) -> Dict[str, Any]:
    """Node 4: Retrieves verified candidate evidence from Candidate Profile & RAG store."""
    logger.info("LangGraph Node: Retrieving Candidate Evidence from RAG...")
    jd = state["job_description"]
    role_class = state["role_classification"]
    candidate_profile = state.get("candidate_profile")
    candidate_id = state.get("candidate_id")

    # If candidate_profile not provided in state, retrieve active candidate profile
    if not candidate_profile:
        try:
            from careerpilot.services.candidate_service import CandidateService
            candidate_profile = CandidateService.get_active_profile(candidate_id=candidate_id)
        except Exception as e:
            logger.debug("Could not fetch active candidate profile: %s", e)

    matcher = EvidenceMatcher(
        candidate_profile=candidate_profile,
        candidate_id=candidate_id,
    )

    matches = [matcher.match_requirement(req) for req in jd.requirements]
    cloud_eval = matcher.evaluate_cloud_transferability(jd)
    pref_score, _ = matcher.evaluate_preferences(jd, role_class.primary_role)

    return {
        "matches": matches,
        "cloud_transferability": cloud_eval,
        "preference_score": pref_score,
        "candidate_profile": candidate_profile,
    }


def score_fit_node(state: JobAnalysisState) -> Dict[str, Any]:
    """Node 5: Computes explainable deterministic fit score."""
    logger.info("LangGraph Node: Computing Fit Score...")
    jd = state["job_description"]
    matches = state["matches"]
    role_class = state["role_classification"]
    cloud_eval = state["cloud_transferability"]
    pref_score = state.get("preference_score", 90.0)
    candidate_profile = state.get("candidate_profile")

    fit_score = CandidateJobFitScorer.compute_fit_score(
        matches=matches,
        role_class=role_class,
        cloud_eval=cloud_eval,
        preference_score=pref_score,
        jd=jd,
        candidate_profile=candidate_profile,
    )
    return {"fit_score": fit_score}


def analyze_risks_node(state: JobAnalysisState) -> Dict[str, Any]:
    """Node 6: Identifies application risks, experience gaps, and cloud mismatches."""
    logger.info("LangGraph Node: Analyzing Risks...")
    jd = state["job_description"]
    matches = state["matches"]
    role_class = state["role_classification"]
    cloud_eval = state["cloud_transferability"]

    risks = RiskAnalyzer.analyze_risks(
        matches=matches,
        role_class=role_class,
        cloud_eval=cloud_eval,
        jd=jd,
    )
    return {"risks": risks}


def decide_recommendation_node(state: JobAnalysisState) -> Dict[str, Any]:
    """Node 7: Deterministic decision engine producing final explainable result."""
    logger.info("LangGraph Node: Generating Final Decision (Apply / Review / Skip)...")
    jd = state["job_description"]
    role_class = state["role_classification"]
    role_reality = state["role_reality"]
    cloud_eval = state["cloud_transferability"]
    matches = state["matches"]
    fit_score = state["fit_score"]
    risks = state["risks"]
    candidate_profile = state.get("candidate_profile")

    result = DecisionEngine.evaluate_decision(
        jd=jd,
        role_class=role_class,
        role_reality=role_reality,
        cloud_eval=cloud_eval,
        matches=matches,
        fit_score=fit_score,
        risks=risks,
        candidate_profile=candidate_profile,
    )
    return {"analysis_result": result}


# -----------------------------------------------------------------------------
# Graph Construction & Compilation
# -----------------------------------------------------------------------------

def build_job_analysis_graph():
    """Builds and compiles the Job Analysis LangGraph workflow."""
    builder = StateGraph(JobAnalysisState)

    # Register nodes
    builder.add_node("parse_jd", parse_jd_node)
    builder.add_node("classify_role", classify_role_node)
    builder.add_node("extract_requirements", extract_requirements_node)
    builder.add_node("retrieve_evidence", retrieve_evidence_node)
    builder.add_node("score_fit", score_fit_node)
    builder.add_node("analyze_risks", analyze_risks_node)
    builder.add_node("decide_recommendation", decide_recommendation_node)

    # Define linear execution edge flow
    builder.add_edge(START, "parse_jd")
    builder.add_edge("parse_jd", "classify_role")
    builder.add_edge("classify_role", "extract_requirements")
    builder.add_edge("extract_requirements", "retrieve_evidence")
    builder.add_edge("retrieve_evidence", "score_fit")
    builder.add_edge("score_fit", "analyze_risks")
    builder.add_edge("analyze_risks", "decide_recommendation")
    builder.add_edge("decide_recommendation", END)

    return builder.compile()


# Global compiled workflow instance
job_analysis_graph = build_job_analysis_graph()


def analyze_job(
    input_source: Union[str, Path],
    candidate_profile: Optional[Any] = None,
    candidate_id: Optional[str] = None,
    company_name: Optional[str] = None,
    job_title: Optional[str] = None,
    job_location: Optional[str] = None,
    work_mode: Optional[str] = None,
) -> JobAnalysisResult:
    """
    Main entry point for executing full Job Analysis agent workflow.
    Accepts raw JD text or file path along with active candidate profile and metadata.
    """
    initial_state: JobAnalysisState = {
        "candidate_profile": candidate_profile,
        "candidate_id": candidate_id,
        "company_name": company_name,
        "job_title": job_title,
        "job_location": job_location,
        "work_mode": work_mode,
    }
    if isinstance(input_source, Path) or (isinstance(input_source, str) and (Path(input_source).exists() or input_source.endswith((".txt", ".md", ".pdf")))):
        initial_state["file_path"] = str(input_source)
    else:
        initial_state["raw_input"] = str(input_source)

    final_state = job_analysis_graph.invoke(initial_state)
    return final_state["analysis_result"]
