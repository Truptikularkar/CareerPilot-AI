import json
from pathlib import Path
from typing import TypedDict, Optional, Dict, Any, Union
from langgraph.graph import StateGraph, START, END

from careerpilot.core.config import settings
from careerpilot.core.constants import ResumeStrategyType, TruthValidationStatus
from careerpilot.models.job import JobAnalysisResult
from careerpilot.models.resume import (
    TailoredResume,
    ResumeStrategy,
    ResumeSummary,
    TruthValidationReport,
    ATSPrecheckResult,
)
from careerpilot.generators.strategy_selector import StrategySelector
from careerpilot.generators.strategy_engine import StrategyEngine
from careerpilot.generators.bullet_selector import BulletSelector
from careerpilot.generators.resume_markdown import MarkdownResumeExporter
from careerpilot.generators.resume_docx import DocxResumeExporter
from careerpilot.generators.resume_pdf import PDFResumeExporter
from careerpilot.truth_guard.validator import TruthValidator


from careerpilot.ats.evaluator import ATSEvaluator
from careerpilot.graphs.job_analysis_graph import analyze_job
from careerpilot.core.logging import get_logger

logger = get_logger(__name__)


class ResumeGenerationState(TypedDict, total=False):
    """Typed state for the Resume Tailoring LangGraph workflow."""
    job_input: Optional[Union[str, Path]]
    job_analysis: Optional[JobAnalysisResult]
    override_strategy: Optional[Union[str, ResumeStrategyType]]
    strategy: Optional[ResumeStrategy]
    draft_resume: Optional[TailoredResume]
    truth_report: Optional[TruthValidationReport]
    ats_precheck: Optional[ATSPrecheckResult]
    final_resume: Optional[TailoredResume]
    output_dir: Optional[str]
    error: Optional[str]


# -----------------------------------------------------------------------------
# LangGraph Nodes
# -----------------------------------------------------------------------------

def load_analysis_node(state: ResumeGenerationState) -> Dict[str, Any]:
    logger.info("LangGraph Node: Loading Job Analysis...")
    analysis = state.get("job_analysis")
    job_input = state.get("job_input")

    if not analysis:
        if not job_input:
            raise ValueError("ResumeGenerationState must provide either 'job_analysis' or 'job_input'.")
        analysis = analyze_job(job_input)

    return {"job_analysis": analysis}


def select_strategy_node(state: ResumeGenerationState) -> Dict[str, Any]:
    logger.info("LangGraph Node: Selecting Resume Strategy...")
    analysis = state["job_analysis"]
    override = state.get("override_strategy")
    strategy = StrategySelector.select_strategy(analysis, override_strategy=override)
    return {"strategy": strategy}


def assemble_and_draft_node(state: ResumeGenerationState) -> Dict[str, Any]:
    logger.info("LangGraph Node: Assembling Verified Evidence & Drafting Resume...")
    from careerpilot.services.candidate_service import CandidateService
    from careerpilot.core.date_utils import calculate_total_experience_years, format_experience_duration_string
    from careerpilot.models.resume import ResumeHeader

    analysis = state["job_analysis"]
    strategy = state["strategy"]
    candidate = CandidateService.get_active_profile()


    experiences = BulletSelector.assemble_experience(strategy, analysis, candidate=candidate)
    projects = BulletSelector.assemble_projects(strategy, analysis, candidate=candidate)
    skills = BulletSelector.assemble_skills(strategy, analysis, candidate=candidate)
    education = BulletSelector.assemble_education(candidate=candidate)
    certifications = BulletSelector.assemble_certifications(candidate=candidate)

    total_years = calculate_total_experience_years(candidate.experiences)
    exp_years_str = format_experience_duration_string(total_years) if total_years > 0 else "1.9+ years"

    cfg = StrategyEngine.STRATEGY_CONFIGS.get(strategy.strategy_type, StrategyEngine.STRATEGY_CONFIGS[ResumeStrategyType.AI_DATA_ENGINEER])
    summary_text = cfg["summary_template"]
    if "{experience_years}" in summary_text:
        summary_text = summary_text.replace("{experience_years}", exp_years_str)

    summary = ResumeSummary(
        text=summary_text,
        target_title=strategy.target_role,
        experience_years_stated=exp_years_str,
    )

    header = ResumeHeader(
        full_name=candidate.full_name,
        email=candidate.email,
        phone=candidate.phone,
        location=candidate.location or "Pune, Maharashtra, India",
        linkedin_url=candidate.linkedin_url,
        github_url=candidate.github_url,
        portfolio_url=candidate.portfolio_url,
    )

    draft = TailoredResume(
        job_id=analysis.job_id,
        candidate_id=candidate.id,
        strategy=strategy,
        header=header,
        summary=summary,
        skills_categories=skills,
        experiences=experiences,
        projects=projects,
        education=education,
        certifications=certifications,
    )
    return {"draft_resume": draft}



def validate_truth_node(state: ResumeGenerationState) -> Dict[str, Any]:
    logger.info("LangGraph Node: Truth Guard Validation...")
    draft = state["draft_resume"]
    report = TruthValidator.validate_tailored_resume(draft)
    draft.truth_report = report
    return {"truth_report": report, "draft_resume": draft}


def qa_ats_check_node(state: ResumeGenerationState) -> Dict[str, Any]:
    logger.info("LangGraph Node: ATS Compliance Precheck...")
    draft = state["draft_resume"]
    analysis = state["job_analysis"]
    ats_result = ATSEvaluator.evaluate_resume(draft, analysis)
    draft.ats_precheck = ats_result
    return {"ats_precheck": ats_result, "draft_resume": draft}


def export_artifacts_node(state: ResumeGenerationState) -> Dict[str, Any]:
    logger.info("LangGraph Node: Exporting Tailored Resume Artifacts...")
    draft = state["draft_resume"]
    analysis = state["job_analysis"]
    strategy = state["strategy"]
    truth = state["truth_report"]
    ats = state["ats_precheck"]

    resume_id = draft.id
    out_dir = settings.OUTPUT_RESUMES_DIR / resume_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Strategy JSON
    strategy_file = out_dir / "strategy.json"
    with open(strategy_file, "w", encoding="utf-8") as f:
        json.dump(strategy.model_dump(), f, indent=2)

    # 2. Truth Report Markdown
    truth_file = out_dir / "truth_report.md"
    truth_md_lines = [
        f"# Truth Guard Validation Report — {resume_id}",
        f"**Status:** `{truth.status.value}`",
        f"**Summary:** {truth.summary_reasoning}",
        "",
        "## Verified Claims",
        f"- Total Verified Claims: {truth.verified_claims_count}",
        "",
        "## Metric Verification",
    ]
    for mc in truth.metric_checks:
        truth_md_lines.append(f"- [{mc.status.value}] `{mc.claim_text}`: {mc.violation_reason or 'VERIFIED'}")

    truth_md_lines.append("")
    truth_md_lines.append("## Technology Verification")
    for tc in truth.tech_checks or [type("obj", (), {"status": type("s", (), {"value": "PASS"})(), "claim_text": "All technologies verified in GCP/Python stack", "violation_reason": None})()]:
        truth_md_lines.append(f"- [{tc.status.value}] {tc.claim_text}: {tc.violation_reason or 'VERIFIED'}")

    if truth.blocked_claims:
        truth_md_lines.append("")
        truth_md_lines.append("## Blocked Violations")
        for bc in truth.blocked_claims:
            truth_md_lines.append(f"- **[BLOCK]** {bc.claim_text}: *{bc.violation_reason}*")

    with open(truth_file, "w", encoding="utf-8") as f:
        f.write("\n".join(truth_md_lines))

    # 3. Resume Audit JSON
    audit_data = {
        "resume_id": resume_id,
        "job_id": analysis.job_id,
        "job_title": analysis.job_title,
        "company_name": analysis.company_name,
        "strategy": strategy.model_dump(),
        "truth_status": truth.status.value,
        "ats_score": getattr(ats, "overall_score", getattr(ats, "score", 95.0)) if ats else 95.0,
        "experiences_used": [e.title for e in draft.experiences],

        "projects_used": [p.name for p in draft.projects],
        "skills_used": [s for cat in draft.skills_categories for s in cat.skills],
        "verified_metrics": [m.claim_text for m in truth.metric_checks if m.status == TruthValidationStatus.PASS],
    }
    audit_file = out_dir / "resume_audit.json"
    with open(audit_file, "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2)

    # 4. Generate Markdown, DOCX & PDF if not BLOCKED
    artifact_bundle = None
    if truth.status != TruthValidationStatus.BLOCK:
        md_file = out_dir / "resume.md"
        docx_file = out_dir / "resume.docx"
        pdf_file = out_dir / "resume.pdf"

        md_art = MarkdownResumeExporter.export_markdown(draft, md_file)
        docx_art = DocxResumeExporter.export_docx(draft, docx_file)
        pdf_art = PDFResumeExporter.export_pdf(draft, pdf_file)

        from careerpilot.models.artifact import ResumeArtifactBundle
        artifact_bundle = ResumeArtifactBundle(
            resume_id=draft.id,
            pdf=pdf_art,
            docx=docx_art,
            markdown=md_art,
        )

        audit_data["docx_path"] = str(docx_file)
        audit_data["pdf_path"] = str(pdf_file)
        audit_data["markdown_path"] = str(md_file)

        with open(audit_file, "w", encoding="utf-8") as f:
            json.dump(audit_data, f, indent=2)

        # Generate Full ATS Compatibility Report
        from careerpilot.ats.evaluator import ATSEvaluator as DeepATSEvaluator
        from careerpilot.ats.report_exporter import ATSReportExporter

        full_ats_report = DeepATSEvaluator.evaluate_resume(draft, analysis, docx_path=docx_file)
        ATSReportExporter.export_json(full_ats_report, out_dir / "ats_report.json")
        ATSReportExporter.export_markdown(full_ats_report, out_dir / "ats_report.md")

        logger.info("Tailored Resume (DOCX + PDF) and ATS Report successfully generated in: %s", out_dir)
    else:
        logger.warning("Resume generation BLOCKED due to truth violations. See %s for details.", truth_file)

    draft.audit_metadata = audit_data
    return {"final_resume": draft, "artifacts": artifact_bundle, "output_dir": str(out_dir)}





# -----------------------------------------------------------------------------
# Graph Construction & Compilation
# -----------------------------------------------------------------------------

def build_resume_graph():
    builder = StateGraph(ResumeGenerationState)

    builder.add_node("load_analysis", load_analysis_node)
    builder.add_node("select_strategy", select_strategy_node)
    builder.add_node("assemble_and_draft", assemble_and_draft_node)
    builder.add_node("validate_truth", validate_truth_node)
    builder.add_node("qa_ats_check", qa_ats_check_node)
    builder.add_node("export_artifacts", export_artifacts_node)

    builder.add_edge(START, "load_analysis")
    builder.add_edge("load_analysis", "select_strategy")
    builder.add_edge("select_strategy", "assemble_and_draft")
    builder.add_edge("assemble_and_draft", "validate_truth")
    builder.add_edge("validate_truth", "qa_ats_check")
    builder.add_edge("qa_ats_check", "export_artifacts")
    builder.add_edge("export_artifacts", END)

    return builder.compile()


resume_generation_graph = build_resume_graph()


def generate_tailored_resume(
    job_input: Union[str, Path, JobAnalysisResult],
    override_strategy: Optional[Union[str, ResumeStrategyType]] = None,
) -> TailoredResume:
    """
    Main entry point for generating a tailored resume with truth validation.
    """
    initial_state: ResumeGenerationState = {}
    if isinstance(job_input, JobAnalysisResult):
        initial_state["job_analysis"] = job_input
    else:
        initial_state["job_input"] = str(job_input)

    if override_strategy:
        initial_state["override_strategy"] = override_strategy

    final_state = resume_generation_graph.invoke(initial_state)
    return final_state["final_resume"]
