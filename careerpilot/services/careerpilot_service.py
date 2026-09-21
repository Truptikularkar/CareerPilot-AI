import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timezone

from careerpilot.core.config import settings
from careerpilot.core.constants import (

    ApplicationStatus,
    DecisionRecommendation,
    ResumeStrategyType,
    MockInterviewMode,
    InterviewDifficulty,
    InterviewerPersona,
    HintMode,
    FeedbackMode,
)
from careerpilot.models.application import (
    Application,
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationFilter,
    ResumeVersionRecord,
    DashboardMetrics,
    SkillGapSummary,
)
from careerpilot.models.job import JobDescription, JobAnalysisResult
from careerpilot.models.resume import TailoredResume
from careerpilot.models.ats import ATSReport
from careerpilot.models.mock_interview import (

    MockInterviewTurn,
    AnswerEvaluation,
    FinalInterviewReport,
)
from careerpilot.graphs.state import MockInterviewState
from careerpilot.db.repository import (
    ApplicationRepository,
    JobRepository,
    ResumeRepository,
    InterviewPrepRepository,
    MockSessionRepository,
    AnalyticsRepository,
)
from careerpilot.db.schema import (
    ResumeVersionDB,
    InterviewPrepDB,
)
from careerpilot.core.logging import get_logger

logger = get_logger(__name__)


class CareerPilotService:
    """
    Unified high-level application orchestrator connecting Streamlit UI,
    LangGraph workflows, RAG engines, ATS scoring, and interview systems.
    Does NOT duplicate business logic; orchestrates established modules cleanly.
    """

    # -------------------------------------------------------------------------
    # 1. Job Analysis & Application Ingestion
    # -------------------------------------------------------------------------
    @classmethod
    def analyze_job(
        cls,
        input_source: Union[str, Path],
        company_name: Optional[str] = None,
        job_title: Optional[str] = None,
        job_location: Optional[str] = None,
        job_url: Optional[str] = None,
    ) -> Tuple[JobAnalysisResult, Application]:
        """
        Executes Milestone 3 Job Analysis workflow, persists job description and analysis,
        and creates/updates a tracked Application record.
        """
        from careerpilot.graphs.job_analysis_graph import analyze_job as run_job_analysis
        from careerpilot.parsers.jd_parser import JobDescriptionParser
        from careerpilot.services.candidate_service import CandidateService

        active_cid = settings.active_candidate_id
        active_profile = CandidateService.get_active_profile(candidate_id=active_cid)

        logger.info("CareerPilotService: Executing job analysis for candidate '%s' on input: %s", active_cid, str(input_source)[:60])
        analysis: JobAnalysisResult = run_job_analysis(
            input_source=input_source,
            candidate_profile=active_profile,
            candidate_id=active_cid,
            company_name=company_name,
            job_title=job_title,
            job_location=job_location,
        )

        # Parse or retrieve structured JobDescription
        if isinstance(input_source, Path) or (isinstance(input_source, str) and (Path(input_source).exists() or input_source.endswith((".txt", ".md", ".pdf")))):
            jd = JobDescriptionParser.parse_file(Path(input_source), company_name=company_name, job_title=job_title, location=job_location)
        else:
            jd = JobDescriptionParser.parse_raw_text(str(input_source), company_name=company_name, job_title=job_title, location=job_location)

        # Override metadata if explicitly provided
        if company_name:
            jd.company_name = company_name
            analysis.company_name = company_name
        if job_title:
            jd.job_title = job_title
            analysis.job_title = job_title
        if job_location and job_location != "Remote / Flexible":
            jd.location = job_location

        # 1. Save Job and Analysis in DB
        jd.id = analysis.job_id
        JobRepository.save_job_description(jd)
        JobRepository.save_job_analysis(analysis, candidate_id=active_cid)

        # 2. Create / Update Application record
        app_id = f"app_{analysis.job_id.replace('job_', '')}"
        app = ApplicationRepository.create_application(
            app_id=app_id,
            job_id=analysis.job_id,
            company=analysis.company_name or "Target Company",
            job_title=analysis.job_title or "AI Data Engineer",
            job_location=jd.location or job_location or "Remote / Flexible",
            job_url=job_url,
            job_description_text=jd.raw_text,
            job_analysis_id=analysis.id,
            fit_score=analysis.fit_score.overall_score,
            system_rec=analysis.recommendation,
            user_dec=analysis.recommendation,
            status=ApplicationStatus.ANALYZED,
            candidate_id=active_cid,
        )

        logger.info("CareerPilotService: Successfully analyzed job '%s' -> Application '%s' (Candidate: %s)", analysis.job_id, app.application_id, active_cid)
        return analysis, app

    # -------------------------------------------------------------------------
    # 2. Application Tracking & Decision Management
    # -------------------------------------------------------------------------
    @classmethod
    def get_application(cls, app_id: str) -> Optional[Application]:
        return ApplicationRepository.get_application(app_id)

    @classmethod
    def get_application_by_job_id(cls, job_id: str) -> Optional[Application]:
        return ApplicationRepository.get_application_by_job_id(job_id)

    @classmethod
    def list_applications(cls, filter_criteria: Optional[ApplicationFilter] = None) -> List[Application]:
        cand_id = getattr(filter_criteria, "candidate_id", None) if filter_criteria else None
        target_cid = cand_id or settings.active_candidate_id
        if not filter_criteria:
            return ApplicationRepository.list_applications(candidate_id=target_cid)
        return ApplicationRepository.list_applications(
            status=filter_criteria.status,
            recommendation=filter_criteria.recommendation,
            role_category=filter_criteria.role_category,
            location=filter_criteria.location,
            search_query=filter_criteria.search_query,
            candidate_id=target_cid,
        )

    @classmethod
    def update_application_decision(cls, app_id: str, user_decision: DecisionRecommendation) -> Optional[Application]:
        return ApplicationRepository.update_decision(app_id, user_decision)

    @classmethod
    def update_application_status(
        cls,
        app_id: str,
        new_status: ApplicationStatus,
        notes: Optional[str] = None,
        applied_date: Optional[datetime] = None,
    ) -> Optional[Application]:
        return ApplicationRepository.update_status(app_id, new_status, notes, applied_date)

    @classmethod
    def add_application_note(cls, app_id: str, note_text: str) -> Optional[Application]:
        return ApplicationRepository.add_note(app_id, note_text)

    # -------------------------------------------------------------------------
    # 3. Resume Tailoring & Versioning (Milestone 4 & 5)
    # -------------------------------------------------------------------------
    @classmethod
    def generate_resume_for_application(
        cls,
        app_id: str,
        strategy: Optional[Union[str, ResumeStrategyType]] = None,
    ) -> Tuple[TailoredResume, ATSReport, Application]:
        """
        Executes Milestone 4 Resume Tailoring and Milestone 5 ATS Evaluation,
        records a new version snapshot, and links it to the Application record.
        """
        from careerpilot.graphs.resume_graph import generate_tailored_resume
        from careerpilot.ats.evaluator import ATSEvaluator

        app = ApplicationRepository.get_application(app_id)
        if not app:
            raise ValueError(f"Application '{app_id}' not found.")

        analysis_db = JobRepository.get_job_analysis(app.job_id)
        if not analysis_db:
            # Fallback to analyzing the job description text
            jd_db = JobRepository.get_job_description(app.job_id)
            if not jd_db:
                raise ValueError(f"JobDescription for Application '{app_id}' not found.")
            analysis, _ = cls.analyze_job(jd_db.raw_text, company_name=app.company, job_title=app.job_title)
        else:
            # Re-run or construct analysis for resume generation
            from careerpilot.graphs.job_analysis_graph import analyze_job
            analysis = analyze_job(app.job_description or app.job_id)
            analysis.job_id = app.job_id

        # 1. Generate Tailored Resume
        override_strat = None
        if strategy and strategy != "AUTO":
            override_strat = ResumeStrategyType(strategy) if isinstance(strategy, str) else strategy

        resume = generate_tailored_resume(analysis, override_strategy=override_strat)
        resume.job_id = app.job_id

        # 2. Evaluate ATS Score
        ats_report = ATSEvaluator.evaluate_resume(resume, analysis)
        ats_report.job_id = app.job_id

        # 3. Generate Artifacts cleanly via Artifact Exporters
        artifacts = cls.get_or_generate_resume_artifacts(resume, company=app.company)

        # 4. Determine next version tag (v1.0, v2.0, v3.0, etc.)
        existing_versions = ResumeRepository.list_versions_for_job(app.job_id)
        next_ver_num = len(existing_versions) + 1
        version_tag = f"v{next_ver_num}.0"

        # 5. Save Resume Version Record
        resume_ver_db = ResumeVersionDB(
            id=resume.id,
            job_id=app.job_id,
            candidate_id=getattr(resume, "candidate_id", None) or getattr(app, "candidate_id", None) or settings.active_candidate_id,
            strategy_type=resume.strategy.strategy_type.value,
            version_tag=version_tag,
            tailored_resume_json=resume.model_dump(),
            ats_score=ats_report.overall_score,
            ats_report_json=ats_report.model_dump(),
            truth_audit_json=[c.model_dump() for c in resume.truth_validation.claims_evaluated] if resume.truth_validation else [],
            docx_file_path=artifacts.docx.file_path if artifacts.docx else None,
            pdf_file_path=artifacts.pdf.file_path if artifacts.pdf else None,
            markdown_file_path=artifacts.markdown.file_path if artifacts.markdown else None,
        )
        ResumeRepository.save_resume_version(resume_ver_db)

        # 6. Link to Application
        res_record = ResumeVersionRecord(
            resume_id=resume.id,
            version_tag=version_tag,
            strategy_type=resume.strategy.strategy_type.value,
            ats_score=ats_report.overall_score,
            docx_file_path=artifacts.docx.file_path if artifacts.docx else None,
            pdf_file_path=artifacts.pdf.file_path if artifacts.pdf else None,
            markdown_file_path=artifacts.markdown.file_path if artifacts.markdown else None,
        )
        updated_app = ApplicationRepository.record_resume_version(app.application_id, res_record)

        logger.info("CareerPilotService: Created Resume %s (%s) for App '%s' with ATS Score %.1f", resume.id, version_tag, app_id, ats_report.overall_score)
        return resume, ats_report, updated_app

    @classmethod
    def get_or_generate_resume_artifacts(
        cls,
        resume: TailoredResume,
        company: Optional[str] = None,
    ) -> ResumeArtifactBundle:
        """
        Retrieves or dynamically builds the full suite of file artifacts (PDF, DOCX, Markdown)
        for a TailoredResume instance without mutating the domain model.
        """
        from careerpilot.generators.resume_pdf import PDFResumeExporter
        from careerpilot.generators.resume_docx import DocxResumeExporter
        from careerpilot.generators.resume_markdown import MarkdownResumeExporter
        from careerpilot.models.artifact import ResumeArtifactBundle

        out_dir = Path(settings.BASE_DIR) / "data" / "generated" / "resumes" / resume.id
        out_dir.mkdir(parents=True, exist_ok=True)

        pdf_path = out_dir / "resume.pdf"
        docx_path = out_dir / "resume.docx"
        md_path = out_dir / "resume.md"

        pdf_art = PDFResumeExporter.export_pdf(resume, output_path=pdf_path, company=company)
        docx_art = DocxResumeExporter.export_docx(resume, output_path=docx_path, company=company)
        md_art = MarkdownResumeExporter.export_markdown(resume, output_path=md_path, company=company)

        return ResumeArtifactBundle(
            resume_id=resume.id,
            pdf=pdf_art,
            docx=docx_art,
            markdown=md_art,
        )

    @classmethod
    def generate_pdf_artifact(
        cls,
        resume: TailoredResume,
        company: Optional[str] = None,
    ) -> ResumeArtifact:
        """Generates and validates a single ATS PDF artifact."""
        from careerpilot.generators.resume_pdf import PDFResumeExporter
        return PDFResumeExporter.export_pdf(resume, company=company)

    @classmethod
    def generate_docx_artifact(
        cls,
        resume: TailoredResume,
        company: Optional[str] = None,
    ) -> ResumeArtifact:
        """Generates a single ATS DOCX artifact."""
        from careerpilot.generators.resume_docx import DocxResumeExporter
        return DocxResumeExporter.export_docx(resume, company=company)


    @classmethod
    def evaluate_ats_for_application(cls, app_id: str, resume_id: Optional[str] = None) -> ATSReport:
        """Evaluates or retrieves the ATS Report for an application."""
        from careerpilot.ats.evaluator import ATSEvaluator
        from careerpilot.graphs.job_analysis_graph import analyze_job

        app = ApplicationRepository.get_application(app_id)
        if not app:
            raise ValueError(f"Application '{app_id}' not found.")

        target_resume_id = resume_id or app.resume_id
        if not target_resume_id:
            raise ValueError(f"No resume generated yet for Application '{app_id}'.")

        res_db = ResumeRepository.get_resume_version(target_resume_id)
        if not res_db:
            raise ValueError(f"ResumeVersion '{target_resume_id}' not found.")

        if res_db.ats_report_json:
            return ATSReport(**res_db.ats_report_json)

        # Recompute if not cached
        resume = TailoredResume(**res_db.tailored_resume_json)
        analysis = analyze_job(app.job_description or app.job_id)
        analysis.job_id = app.job_id
        ats_rep = ATSEvaluator.evaluate_resume(resume, analysis)
        ats_rep.job_id = app.job_id

        res_db.ats_report_json = ats_rep.model_dump()
        res_db.ats_score = ats_rep.overall_score
        ResumeRepository.save_resume_version(res_db)
        return ats_rep


    # -------------------------------------------------------------------------
    # 4. Interview Preparation (Milestone 6)
    # -------------------------------------------------------------------------
    @classmethod
    def prepare_interview_for_application(cls, app_id: str, roadmap_days: int = 7) -> Dict[str, Any]:
        """
        Executes Milestone 6 Interview Preparation pipeline: generates categorized questions,
        answers, STAR narratives, system design, roadmap, and readiness score.
        """
        from careerpilot.graphs.interview_prep_graph import interview_prep_graph
        from careerpilot.graphs.job_analysis_graph import analyze_job

        app = ApplicationRepository.get_application(app_id)
        if not app:
            raise ValueError(f"Application '{app_id}' not found.")

        # Run Interview Prep Graph
        initial_state = {
            "job_input": app.job_description or app.job_id,
            "roadmap_days": roadmap_days,
        }
        prep_state = interview_prep_graph.invoke(initial_state)

        prep_id = prep_state.get("prep_id", f"prep_{uuid.uuid4().hex[:8]}")
        r_score_raw = prep_state.get("readiness_score")
        if hasattr(r_score_raw, "overall_readiness_score"):
            readiness_score = r_score_raw.overall_readiness_score
        elif isinstance(r_score_raw, dict):
            readiness_score = r_score_raw.get("overall_readiness_score", 85.0)
        else:
            readiness_score = 85.0

        # Save to DB
        prep_db = InterviewPrepDB(
            id=prep_id,
            job_id=app.job_id,
            candidate_id=getattr(app, "candidate_id", None) or settings.active_candidate_id,
            target_role=app.job_title,
            readiness_score=readiness_score,
            seed_json=prep_state.get("readiness_seed", {}).model_dump() if hasattr(prep_state.get("readiness_seed"), "model_dump") else prep_state.get("readiness_seed", {}),
            plan_json={"questions_count": len(prep_state.get("questions", []))},
            roadmap_json=prep_state.get("roadmap", {}).model_dump() if hasattr(prep_state.get("roadmap"), "model_dump") else prep_state.get("roadmap", {}),
        )

        InterviewPrepRepository.save_prep(prep_db)

        # Link to application
        ApplicationRepository.update_interview_prep(app.application_id, prep_id)

        logger.info("CareerPilotService: Generated Interview Prep '%s' for App '%s' (Readiness: %.1f)", prep_id, app_id, readiness_score)
        return prep_state

    # -------------------------------------------------------------------------
    # 5. Adaptive Mock Interview (Milestone 7)
    # -------------------------------------------------------------------------
    @classmethod
    def start_mock_interview_for_application(
        cls,
        app_id: str,
        mode: MockInterviewMode = MockInterviewMode.FULL_INTERVIEW,
        difficulty: InterviewDifficulty = InterviewDifficulty.ADAPTIVE,
        persona: InterviewerPersona = InterviewerPersona.SENIOR_ENGINEER,
        feedback_mode: FeedbackMode = FeedbackMode.INTERVIEW_MODE,
        total_questions: int = 6,
    ) -> MockInterviewState:
        """Starts an interactive mock interview session for the target application."""
        from careerpilot.interview.mock_service import MockInterviewService

        app = ApplicationRepository.get_application(app_id)
        if not app:
            raise ValueError(f"Application '{app_id}' not found.")

        job_src = app.job_description if app.job_description else app.job_id
        state = MockInterviewService.start_session(
            job_input=job_src,
            mode=mode,
            difficulty=difficulty,
            persona=persona,
            feedback_mode=feedback_mode,
            total_questions=total_questions,
        )
        return state

    @classmethod
    def submit_mock_answer(
        cls,
        session_id: str,
        answer_text: str,
        hint_used: HintMode = HintMode.NO_HINT,
    ) -> AnswerEvaluation:
        from careerpilot.interview.mock_service import MockInterviewService
        return MockInterviewService.submit_answer(session_id, answer_text, hint_used)

    @classmethod
    def continue_mock_session(cls, session_id: str) -> Tuple[Optional[MockInterviewTurn], bool]:
        from careerpilot.interview.mock_service import MockInterviewService
        return MockInterviewService.continue_session(session_id)

    @classmethod
    def finish_mock_interview(cls, session_id: str) -> FinalInterviewReport:
        from careerpilot.interview.mock_service import MockInterviewService
        return MockInterviewService.finish_session(session_id)

    # -------------------------------------------------------------------------
    # 6. Analytics & Intelligence
    # -------------------------------------------------------------------------
    @classmethod
    def get_dashboard_metrics(cls, candidate_id: Optional[str] = None) -> DashboardMetrics:
        cid = candidate_id or settings.active_candidate_id
        return AnalyticsRepository.get_dashboard_metrics(candidate_id=cid)

    @classmethod
    def get_skill_gaps_summary(cls) -> SkillGapSummary:
        return AnalyticsRepository.get_skill_gaps_summary()

    # -------------------------------------------------------------------------
    # 7. Candidate Profile Management & RAG Sync
    # -------------------------------------------------------------------------
    @classmethod
    def get_candidate_profile(cls, candidate_id: Optional[str] = None):
        from careerpilot.services.candidate_service import CandidateService
        cid = candidate_id or settings.active_candidate_id
        return CandidateService.get_active_profile(candidate_id=cid)

    @classmethod
    def save_candidate_profile(cls, profile, change_summary: str = "Updated profile", changed_sections: Optional[List[str]] = None):
        from careerpilot.services.candidate_service import CandidateService
        return CandidateService.save_active_profile(profile, change_summary=change_summary, changed_sections=changed_sections)

    @classmethod
    def add_candidate_project(cls, project):
        from careerpilot.services.candidate_service import CandidateService
        return CandidateService.add_project(project)

    @classmethod
    def update_candidate_project(cls, project):
        from careerpilot.services.candidate_service import CandidateService
        return CandidateService.update_project(project)

    @classmethod
    def delete_candidate_project(cls, project_id_or_name: str):
        from careerpilot.services.candidate_service import CandidateService
        return CandidateService.delete_project(project_id_or_name)

    @classmethod
    def add_candidate_skill(cls, skill):
        from careerpilot.services.candidate_service import CandidateService
        return CandidateService.add_skill(skill)

    @classmethod
    def update_candidate_skill(cls, skill):
        from careerpilot.services.candidate_service import CandidateService
        return CandidateService.update_skill(skill)

    @classmethod
    def delete_candidate_skill(cls, skill_name: str):
        from careerpilot.services.candidate_service import CandidateService
        return CandidateService.delete_skill(skill_name)

    @classmethod
    def update_candidate_experiences(cls, experiences):
        from careerpilot.services.candidate_service import CandidateService
        return CandidateService.update_experiences(experiences)

    @classmethod
    def update_candidate_preferences(cls, preferences):
        from careerpilot.services.candidate_service import CandidateService
        return CandidateService.update_preferences(preferences)

    @classmethod
    def sync_candidate_rag(cls, profile=None) -> int:
        from careerpilot.services.candidate_service import CandidateService
        return CandidateService.sync_profile_to_rag(profile)

    @classmethod
    def rebuild_candidate_rag(cls) -> int:
        from careerpilot.services.candidate_service import CandidateService
        return CandidateService.rebuild_candidate_rag()

    @classmethod
    def get_candidate_rag_status(cls) -> Dict[str, Any]:
        from careerpilot.services.candidate_service import CandidateService
        return CandidateService.get_rag_sync_status()

    @classmethod
    def get_candidate_profile_health(cls, profile=None):
        from careerpilot.services.candidate_service import CandidateService
        return CandidateService.get_profile_health(profile)

    @classmethod
    def list_candidate_profile_versions(cls):
        from careerpilot.services.candidate_service import CandidateService
        return CandidateService.list_profile_versions()

    @classmethod
    def restore_candidate_profile_version(cls, version_id: str):
        from careerpilot.services.candidate_service import CandidateService
        return CandidateService.restore_profile_version(version_id)

