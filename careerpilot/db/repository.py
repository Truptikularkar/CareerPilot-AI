from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from careerpilot.db.session import get_db
from careerpilot.core.config import settings
import uuid
from careerpilot.db.schema import (
    ApplicationDB,
    JobDescriptionDB,
    JobAnalysisDB,
    ResumeVersionDB,
    InterviewPrepDB,
    MockSessionDB,
    SkillGapDB,
    CandidateProfileDB,
    CandidateEvidenceDB,
    ProfileVersionDB,
    CanonicalJobDB,
    ExternalProfileDB,
    UserDB,
    UserSessionDB,
)
from careerpilot.core.constants import ApplicationStatus, DecisionRecommendation
from careerpilot.models.application import (
    Application,
    ApplicationCreate,
    ApplicationUpdate,
    ResumeVersionRecord,
    DashboardMetrics,
    SkillGapItem,
    SkillGapSummary,
)
from careerpilot.models.job import JobDescription, JobAnalysisResult
from careerpilot.models.candidate import (
    CandidateProfile,
    Skill,
    Experience,
    Project,
    Education,
    Achievement,
    CareerPreference,
)
from careerpilot.core.logging import get_logger

logger = get_logger(__name__)



def to_application_model(db_obj: ApplicationDB) -> Application:
    """Convert an ApplicationDB SQLAlchemy model into an Application Pydantic domain model."""
    raw_versions = db_obj.resume_versions_json or []
    parsed_versions = [ResumeVersionRecord(**v) if isinstance(v, dict) else v for v in raw_versions]

    raw_notes = db_obj.notes_json or []
    notes_list = [str(n) for n in raw_notes]

    sys_rec = DecisionRecommendation(db_obj.system_recommendation) if db_obj.system_recommendation in DecisionRecommendation._value2member_map_ else DecisionRecommendation.REVIEW
    user_dec = DecisionRecommendation(db_obj.user_decision) if db_obj.user_decision in DecisionRecommendation._value2member_map_ else DecisionRecommendation.REVIEW
    app_stat = ApplicationStatus(db_obj.status) if db_obj.status in ApplicationStatus._value2member_map_ else ApplicationStatus.SAVED

    # Determine recommended next action
    next_action = "Analyze job requirements"
    if app_stat == ApplicationStatus.SAVED:
        next_action = "Analyze job description"
    elif app_stat == ApplicationStatus.ANALYZED:
        if user_dec == DecisionRecommendation.APPLY:
            next_action = "Generate tailored resume"
        elif user_dec == DecisionRecommendation.REVIEW:
            next_action = "Review skill gaps and transferable experience"
        else:
            next_action = "Review skip reasoning or archive"
    elif app_stat == ApplicationStatus.APPLYING:
        if not db_obj.resume_id:
            next_action = "Generate tailored resume"
        elif db_obj.ats_score and db_obj.ats_score < 80.0:
            next_action = "Optimize resume keywords for ATS alignment"
        else:
            next_action = "Submit job application on company portal"
    elif app_stat == ApplicationStatus.APPLIED:
        if not db_obj.interview_prep_id:
            next_action = "Generate interview preparation plan & questions"
        else:
            next_action = "Practice adaptive mock interview session"
    elif app_stat == ApplicationStatus.INTERVIEW:
        next_action = "Practice high-priority technical & system design questions"
    elif app_stat in (ApplicationStatus.OFFER, ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN, ApplicationStatus.SKIPPED):
        next_action = "Application complete / archived"

    return Application(
        application_id=db_obj.id,
        candidate_id=getattr(db_obj, "candidate_id", None),
        canonical_job_id=getattr(db_obj, "canonical_job_id", None) or db_obj.job_id,

        company=db_obj.company_name,
        job_title=db_obj.role_title,
        source=getattr(db_obj, "source", "DIRECT") or "DIRECT",
        job_location=db_obj.job_location or "Remote / Flexible",
        job_url=db_obj.job_url,
        job_description=db_obj.job_description_text or "",
        job_id=db_obj.job_id,
        job_analysis_id=db_obj.job_analysis_id,
        system_recommendation=sys_rec,
        user_decision=user_dec,
        fit_score=db_obj.fit_score or 0.0,
        selected_strategy=db_obj.selected_strategy,
        resume_id=db_obj.resume_id,
        resume_version=getattr(db_obj, "resume_version", None),
        ats_score=db_obj.ats_score,
        interview_prep_id=db_obj.interview_prep_id,
        application_status=app_stat,
        date_added=db_obj.created_at.isoformat() if db_obj.created_at else datetime.now(timezone.utc).isoformat(),
        date_applied=db_obj.applied_date.isoformat() if db_obj.applied_date else None,
        applied_date=db_obj.applied_date.isoformat() if db_obj.applied_date else None,
        last_updated=db_obj.updated_at.isoformat() if getattr(db_obj, "updated_at", None) else (db_obj.created_at.isoformat() if db_obj.created_at else datetime.now(timezone.utc).isoformat()),
        interview_status=db_obj.interview_status or "Not Started",
        recruiter=getattr(db_obj, "recruiter", None),
        final_outcome=getattr(db_obj, "final_outcome", None),
        notes=notes_list,
        resume_versions=parsed_versions,
        status_history=list(getattr(db_obj, "status_history_json", []) or []),
        next_action=next_action,
    )



class JobRepository:
    """Repository for Job Descriptions and Analysis results."""

    @classmethod
    def save_job_description(cls, job: JobDescription) -> JobDescriptionDB:
        with get_db() as db:
            existing = db.query(JobDescriptionDB).filter(JobDescriptionDB.id == job.id).first()
            if existing:
                existing.company_name = job.company_name
                existing.job_title = job.job_title
                existing.location = job.location
                existing.work_mode = job.work_mode
                existing.extracted_role = job.extracted_role
                existing.estimated_seniority = job.estimated_seniority.value if hasattr(job.estimated_seniority, "value") else str(job.estimated_seniority)
                existing.raw_text = job.raw_text
                existing.summary = job.summary
                existing.responsibilities_json = job.responsibilities
                existing.must_have_skills_json = job.must_have_skills
                existing.nice_to_have_skills_json = job.nice_to_have_skills
                existing.tech_stack_json = job.tech_stack
                existing.requirements_json = [r.model_dump() for r in job.requirements]
                db.commit()
                db.refresh(existing)
                return existing

            db_job = JobDescriptionDB(
                id=job.id,
                company_name=job.company_name,
                job_title=job.job_title,
                location=job.location,
                work_mode=job.work_mode,
                extracted_role=job.extracted_role,
                estimated_seniority=job.estimated_seniority.value if hasattr(job.estimated_seniority, "value") else str(job.estimated_seniority),
                raw_text=job.raw_text,
                summary=job.summary,
                responsibilities_json=job.responsibilities,
                must_have_skills_json=job.must_have_skills,
                nice_to_have_skills_json=job.nice_to_have_skills,
                tech_stack_json=job.tech_stack,
                requirements_json=[r.model_dump() for r in job.requirements],
            )
            db.add(db_job)
            db.commit()
            db.refresh(db_job)
            return db_job

    @classmethod
    def get_job_description(cls, job_id: str) -> Optional[JobDescriptionDB]:
        with get_db() as db:
            return db.query(JobDescriptionDB).filter(JobDescriptionDB.id == job_id).first()

    @classmethod
    def save_job_analysis(cls, analysis: JobAnalysisResult, candidate_id: Optional[str] = None) -> JobAnalysisDB:
        cid = candidate_id or getattr(analysis, "candidate_id", None) or settings.active_candidate_id
        with get_db() as db:
            existing = db.query(JobAnalysisDB).filter(JobAnalysisDB.id == analysis.id).first()
            if existing:
                existing.candidate_id = cid
                existing.overall_fit_score = analysis.fit_score.overall_score
                existing.scores_json = analysis.fit_score.model_dump()
                existing.matched_skills_json = [m.requirement_skill for m in analysis.matches if m.is_matched]
                existing.missing_skills_json = analysis.key_gaps
                existing.key_strengths_json = analysis.key_strengths
                existing.risk_factors_json = [r.model_dump() for r in analysis.risks]
                existing.recommendation = analysis.recommendation.value
                existing.explainable_reasoning = analysis.explainable_reasoning
                db.commit()
                db.refresh(existing)
                return existing

            db_analysis = JobAnalysisDB(
                id=analysis.id,
                job_id=analysis.job_id,
                candidate_id=cid,
                overall_fit_score=analysis.fit_score.overall_score,
                scores_json=analysis.fit_score.model_dump(),
                matched_skills_json=[m.requirement_skill for m in analysis.matches if m.is_matched],
                missing_skills_json=analysis.key_gaps,
                key_strengths_json=analysis.key_strengths,
                risk_factors_json=[r.model_dump() for r in analysis.risks],
                recommendation=analysis.recommendation.value,
                explainable_reasoning=analysis.explainable_reasoning,
                suggested_resume_strategy=analysis.metadata.get("suggested_strategy"),
            )
            db.add(db_analysis)
            db.commit()
            db.refresh(db_analysis)
            return db_analysis

    @classmethod
    def get_job_analysis(cls, job_id_or_analysis_id: str) -> Optional[JobAnalysisDB]:
        with get_db() as db:
            return db.query(JobAnalysisDB).filter(
                (JobAnalysisDB.id == job_id_or_analysis_id) | (JobAnalysisDB.job_id == job_id_or_analysis_id)
            ).first()

    @classmethod
    def list_jobs(cls) -> List[JobDescriptionDB]:
        with get_db() as db:
            return db.query(JobDescriptionDB).order_by(desc(JobDescriptionDB.created_at)).all()


class UserRepository:
    """Repository for managing Users and persistent Sessions."""

    @classmethod
    def get_by_email(cls, email: str) -> Optional[UserDB]:
        with get_db() as db:
            return db.query(UserDB).filter(UserDB.email == email.strip().lower()).first()

    @classmethod
    def get_by_id(cls, user_id: str) -> Optional[UserDB]:
        with get_db() as db:
            return db.query(UserDB).filter(UserDB.id == user_id).first()

    @classmethod
    def get_by_candidate_id(cls, candidate_id: str) -> Optional[UserDB]:
        with get_db() as db:
            cand = db.query(CandidateProfileDB).filter(CandidateProfileDB.id == candidate_id).first()
            if cand and cand.user_id:
                return db.query(UserDB).filter(UserDB.id == cand.user_id).first()
            return None


class ApplicationRepository:
    """Repository for managing candidate job application lifecycles and tracking."""

    @classmethod
    def create_application(
        cls,
        app_id: str,
        job_id: str,
        company: str,
        job_title: str,
        job_location: str = "Remote / Flexible",
        job_url: Optional[str] = None,
        job_description_text: Optional[str] = "",
        job_analysis_id: Optional[str] = None,
        fit_score: float = 0.0,
        system_rec: DecisionRecommendation = DecisionRecommendation.REVIEW,
        user_dec: Optional[DecisionRecommendation] = None,
        status: ApplicationStatus = ApplicationStatus.ANALYZED,
        notes: Optional[List[str]] = None,
        canonical_job_id: Optional[str] = None,
        source: str = "DIRECT",
        recruiter: Optional[str] = None,
        candidate_id: Optional[str] = None,
    ) -> Application:
        cid = candidate_id or settings.active_candidate_id
        with get_db() as db:
            existing = db.query(ApplicationDB).filter(ApplicationDB.id == app_id).first()
            if not existing:
                existing = db.query(ApplicationDB).filter(ApplicationDB.job_id == job_id).first()

            if existing:
                existing.company_name = company
                existing.role_title = job_title
                if cid:
                    existing.candidate_id = cid
                if canonical_job_id:
                    existing.canonical_job_id = canonical_job_id
                if source:
                    existing.source = source
                if recruiter:
                    existing.recruiter = recruiter
                if job_location:
                    existing.job_location = job_location
                if job_url:
                    existing.job_url = job_url
                if job_description_text:
                    existing.job_description_text = job_description_text
                if job_analysis_id:
                    existing.job_analysis_id = job_analysis_id
                existing.fit_score = fit_score
                existing.system_recommendation = system_rec.value
                if user_dec:
                    existing.user_decision = user_dec.value
                existing.status = status.value
                if notes:
                    curr_notes = list(existing.notes_json or [])
                    curr_notes.extend(notes)
                    existing.notes_json = curr_notes
                db.commit()
                db.refresh(existing)
                return to_application_model(existing)

            initial_history = [
                {
                    "from_status": "NONE",
                    "to_status": status.value,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "note": "Application created",
                }
            ]

            db_app = ApplicationDB(
                id=app_id,
                canonical_job_id=canonical_job_id or job_id,
                candidate_id=cid,
                job_id=job_id,
                company_name=company,
                role_title=job_title,
                source=source or "DIRECT",
                job_location=job_location,
                job_url=job_url,
                job_description_text=job_description_text,
                job_analysis_id=job_analysis_id,
                system_recommendation=system_rec.value,
                user_decision=(user_dec or system_rec).value,
                fit_score=fit_score,
                status=status.value,
                recruiter=recruiter,
                notes_json=notes or [],
                resume_versions_json=[],
                status_history_json=initial_history,
            )
            db.add(db_app)
            db.commit()
            db.refresh(db_app)
            return to_application_model(db_app)

    @classmethod
    def get_application(cls, app_id: str, candidate_id: Optional[str] = None) -> Optional[Application]:
        with get_db() as db:
            query = db.query(ApplicationDB).filter(ApplicationDB.id == app_id)
            if candidate_id:
                query = query.filter(ApplicationDB.candidate_id == candidate_id)
            db_app = query.first()
            return to_application_model(db_app) if db_app else None

    @classmethod
    def get_application_by_job_id(cls, job_id: str, candidate_id: Optional[str] = None) -> Optional[Application]:
        with get_db() as db:
            query = db.query(ApplicationDB).filter(ApplicationDB.job_id == job_id)
            if candidate_id:
                query = query.filter(ApplicationDB.candidate_id == candidate_id)
            db_app = query.first()
            return to_application_model(db_app) if db_app else None

    @classmethod
    def list_applications(
        cls,
        status: Optional[ApplicationStatus] = None,
        recommendation: Optional[DecisionRecommendation] = None,
        role_category: Optional[str] = None,
        location: Optional[str] = None,
        search_query: Optional[str] = None,
        candidate_id: Optional[str] = None,
    ) -> List[Application]:
        with get_db() as db:
            query = db.query(ApplicationDB)
            cid = candidate_id if candidate_id is not None else settings.active_candidate_id
            if cid and cid != "ALL":
                query = query.filter(ApplicationDB.candidate_id == cid)
            if status:
                query = query.filter(ApplicationDB.status == status.value)
            if recommendation:
                query = query.filter(ApplicationDB.system_recommendation == recommendation.value)
            if location:
                query = query.filter(ApplicationDB.job_location.ilike(f"%{location}%"))
            if search_query:
                query = query.filter(
                    (ApplicationDB.company_name.ilike(f"%{search_query}%"))
                    | (ApplicationDB.role_title.ilike(f"%{search_query}%"))
                )

            db_apps = query.order_by(desc(ApplicationDB.updated_at)).all()
            apps = [to_application_model(a) for a in db_apps]

            if role_category:
                apps = [a for a in apps if role_category.lower() in a.job_title.lower() or role_category.lower() in (a.selected_strategy or "").lower()]

            return apps

    @classmethod
    def update_decision(
        cls,
        app_id: str,
        user_decision: DecisionRecommendation,
        candidate_id: Optional[str] = None,
    ) -> Optional[Application]:
        with get_db() as db:
            db_app = db.query(ApplicationDB).filter(ApplicationDB.id == app_id).first()
            if not db_app:
                return None
            if candidate_id and db_app.candidate_id != candidate_id:
                raise PermissionError(f"Unauthorized: Application '{app_id}' does not belong to candidate '{candidate_id}'.")
            old_status = db_app.status
            db_app.user_decision = user_decision.value
            if user_decision == DecisionRecommendation.APPLY and db_app.status == ApplicationStatus.SAVED.value:
                db_app.status = ApplicationStatus.APPLYING.value
            elif user_decision == DecisionRecommendation.SKIP:
                db_app.status = ApplicationStatus.SKIPPED.value

            if db_app.status != old_status:
                hist = list(db_app.status_history_json or [])
                hist.append({
                    "from_status": old_status,
                    "to_status": db_app.status,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "note": f"Decision updated to {user_decision.value}",
                })
                db_app.status_history_json = hist

            db.commit()
            db.refresh(db_app)
            return to_application_model(db_app)

    @classmethod
    def update_status(
        cls,
        app_id: str,
        new_status: ApplicationStatus,
        notes: Optional[str] = None,
        applied_date: Optional[datetime] = None,
        candidate_id: Optional[str] = None,
    ) -> Optional[Application]:
        with get_db() as db:
            db_app = db.query(ApplicationDB).filter(ApplicationDB.id == app_id).first()
            if not db_app:
                return None
            if candidate_id and db_app.candidate_id != candidate_id:
                raise PermissionError(f"Unauthorized: Application '{app_id}' does not belong to candidate '{candidate_id}'.")
            old_status = db_app.status
            db_app.status = new_status.value
            if applied_date:
                db_app.applied_date = applied_date
            elif new_status == ApplicationStatus.APPLIED and not db_app.applied_date:
                db_app.applied_date = datetime.now(timezone.utc)
            if notes:
                curr_notes = list(db_app.notes_json or [])
                curr_notes.append(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}] {notes}")
                db_app.notes_json = curr_notes

            # Status history tracking
            hist = list(db_app.status_history_json or [])
            hist.append({
                "from_status": old_status,
                "to_status": new_status.value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "note": notes or f"Status changed to {new_status.value}",
            })
            db_app.status_history_json = hist

            db.commit()
            db.refresh(db_app)
            return to_application_model(db_app)

    @classmethod
    def get_status_history(cls, app_id: str, candidate_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with get_db() as db:
            query = db.query(ApplicationDB).filter(ApplicationDB.id == app_id)
            if candidate_id:
                query = query.filter(ApplicationDB.candidate_id == candidate_id)
            db_app = query.first()
            if not db_app:
                return []
            return list(db_app.status_history_json or [])


    @classmethod
    def add_note(cls, app_id: str, note_text: str) -> Optional[Application]:
        with get_db() as db:
            db_app = db.query(ApplicationDB).filter(ApplicationDB.id == app_id).first()
            if not db_app:
                return None
            curr_notes = list(db_app.notes_json or [])
            curr_notes.append(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}] {note_text}")
            db_app.notes_json = curr_notes
            db.commit()
            db.refresh(db_app)
            return to_application_model(db_app)

    @classmethod
    def record_resume_version(
        cls,
        app_id: str,
        resume_record: ResumeVersionRecord,
    ) -> Optional[Application]:
        with get_db() as db:
            db_app = db.query(ApplicationDB).filter(ApplicationDB.id == app_id).first()
            if not db_app:
                return None
            curr_versions = list(db_app.resume_versions_json or [])
            curr_versions.append(resume_record.model_dump())
            db_app.resume_versions_json = curr_versions
            db_app.resume_id = resume_record.resume_id
            if resume_record.ats_score is not None:
                db_app.ats_score = resume_record.ats_score
            db_app.selected_strategy = resume_record.strategy_type
            if db_app.status in (ApplicationStatus.SAVED.value, ApplicationStatus.ANALYZED.value):
                db_app.status = ApplicationStatus.APPLYING.value
            db.commit()
            db.refresh(db_app)
            return to_application_model(db_app)

    @classmethod
    def update_interview_prep(cls, app_id: str, prep_id: str) -> Optional[Application]:
        with get_db() as db:
            db_app = db.query(ApplicationDB).filter(ApplicationDB.id == app_id).first()
            if not db_app:
                return None
            db_app.interview_prep_id = prep_id
            db_app.interview_status = "Prepared"
            db.commit()
            db.refresh(db_app)
            return to_application_model(db_app)


class ResumeRepository:
    """Repository for Resume Versions and ATS Compatibility reports."""

    @classmethod
    def save_resume_version(
        cls,
        version: Optional[ResumeVersionDB] = None,
        job_id: Optional[str] = None,
        resume_data: Optional[Dict[str, Any]] = None,
        tailoring_strategy: Optional[str] = None,
        candidate_id: Optional[str] = None,
        strategy_type: Optional[str] = None,
        ats_score: float = 0.0,
        ats_report_json: Optional[Dict[str, Any]] = None,
        truth_audit_json: Optional[List[Any]] = None,
        docx_file_path: Optional[str] = None,
        pdf_file_path: Optional[str] = None,
        markdown_file_path: Optional[str] = None,
    ) -> ResumeVersionDB:
        if version is None:
            strat = tailoring_strategy or strategy_type or "STANDARD"
            cid = candidate_id or "trupti_kularkar"
            ver_id = f"res_{uuid.uuid4().hex[:8]}"
            version = ResumeVersionDB(
                id=ver_id,
                job_id=job_id or "job_default",
                candidate_id=cid,
                strategy_type=strat,
                tailored_resume_json=resume_data or {},
                ats_score=ats_score,
                ats_report_json=ats_report_json or {},
                truth_audit_json=truth_audit_json or [],
                docx_file_path=docx_file_path,
                pdf_file_path=pdf_file_path,
                markdown_file_path=markdown_file_path,
                created_at=datetime.now(timezone.utc),
            )

        with get_db() as db:
            existing = db.query(ResumeVersionDB).filter(ResumeVersionDB.id == version.id).first()
            if existing:
                existing.ats_score = version.ats_score
                existing.ats_report_json = version.ats_report_json
                existing.truth_audit_json = version.truth_audit_json
                existing.docx_file_path = version.docx_file_path
                existing.pdf_file_path = version.pdf_file_path
                existing.markdown_file_path = version.markdown_file_path
                db.commit()
                db.refresh(existing)
                return existing

            db.add(version)
            db.commit()
            db.refresh(version)
            return version


    @classmethod
    def get_resume_version(cls, resume_id: str, candidate_id: Optional[str] = None) -> Optional[ResumeVersionDB]:
        with get_db() as db:
            query = db.query(ResumeVersionDB).filter(ResumeVersionDB.id == resume_id)
            if candidate_id:
                query = query.filter(ResumeVersionDB.candidate_id == candidate_id)
            return query.first()

    @classmethod
    def list_versions_for_job(cls, job_id: str, candidate_id: Optional[str] = None) -> List[ResumeVersionDB]:
        with get_db() as db:
            query = db.query(ResumeVersionDB).filter(ResumeVersionDB.job_id == job_id)
            if candidate_id:
                query = query.filter(ResumeVersionDB.candidate_id == candidate_id)
            return query.order_by(desc(ResumeVersionDB.created_at)).all()


class InterviewPrepRepository:
    """Repository for Interview Preparation plans and question seeds."""

    @classmethod
    def save_prep(cls, prep: InterviewPrepDB) -> InterviewPrepDB:
        with get_db() as db:
            existing = db.query(InterviewPrepDB).filter(InterviewPrepDB.id == prep.id).first()
            if existing:
                existing.readiness_score = prep.readiness_score
                existing.seed_json = prep.seed_json
                existing.plan_json = prep.plan_json
                existing.roadmap_json = prep.roadmap_json
                db.commit()
                db.refresh(existing)
                return existing

            db.add(prep)
            db.commit()
            db.refresh(prep)
            return prep

    @classmethod
    def get_prep_for_job(cls, job_id: str) -> Optional[InterviewPrepDB]:
        with get_db() as db:
            return db.query(InterviewPrepDB).filter(InterviewPrepDB.job_id == job_id).order_by(desc(InterviewPrepDB.created_at)).first()

    @classmethod
    def get_prep(cls, prep_id: str) -> Optional[InterviewPrepDB]:
        with get_db() as db:
            return db.query(InterviewPrepDB).filter(InterviewPrepDB.id == prep_id).first()


class MockSessionRepository:
    """Repository for querying Mock Interview sessions."""

    @classmethod
    def list_all_sessions(cls) -> List[MockSessionDB]:
        with get_db() as db:
            return db.query(MockSessionDB).order_by(desc(MockSessionDB.created_at)).all()

    @classmethod
    def list_sessions_for_job(cls, job_id: str) -> List[MockSessionDB]:
        with get_db() as db:
            return db.query(MockSessionDB).filter(MockSessionDB.job_id == job_id).order_by(desc(MockSessionDB.created_at)).all()


class AnalyticsRepository:
    """Analytics and cross-application intelligence engine."""

    @classmethod
    def get_dashboard_metrics(cls, candidate_id: Optional[str] = None) -> DashboardMetrics:
        cid = candidate_id or settings.active_candidate_id
        with get_db() as db:
            total_jobs = db.query(JobDescriptionDB).count()
            apps_q = db.query(ApplicationDB)
            if cid and cid != "ALL":
                apps_q = apps_q.filter(ApplicationDB.candidate_id == cid)
            apps = apps_q.all()
            preps_q = db.query(InterviewPrepDB)
            if cid and cid != "ALL":
                preps_q = preps_q.filter(InterviewPrepDB.candidate_id == cid)
            preps = preps_q.count()
            mocks_q = db.query(MockSessionDB).filter(MockSessionDB.is_completed == True)
            if cid and cid != "ALL":
                mocks_q = mocks_q.filter(MockSessionDB.candidate_id == cid)
            mocks = mocks_q.all()

            jobs_to_apply = sum(1 for a in apps if a.user_decision == DecisionRecommendation.APPLY.value or a.system_recommendation == DecisionRecommendation.APPLY.value)
            jobs_reviewed = sum(1 for a in apps if a.user_decision == DecisionRecommendation.REVIEW.value or a.system_recommendation == DecisionRecommendation.REVIEW.value)
            jobs_skipped = sum(1 for a in apps if a.user_decision == DecisionRecommendation.SKIP.value or a.system_recommendation == DecisionRecommendation.SKIP.value)
            apps_submitted = sum(1 for a in apps if a.status in (
                ApplicationStatus.APPLIED.value,
                ApplicationStatus.ACKNOWLEDGED.value,
                ApplicationStatus.SCREENING.value,
                ApplicationStatus.INTERVIEWING.value,
                ApplicationStatus.TECHNICAL_ROUND.value,
                ApplicationStatus.HR_ROUND.value,
                ApplicationStatus.OFFER.value,
                "APPLYING",
                "INTERVIEW",
            ))

            interviews_count = sum(1 for a in apps if a.status in (
                ApplicationStatus.INTERVIEWING.value,
                ApplicationStatus.TECHNICAL_ROUND.value,
                ApplicationStatus.HR_ROUND.value,
                "INTERVIEW",
            ))
            offers_count = sum(1 for a in apps if a.status == ApplicationStatus.OFFER.value)
            rejected_count = sum(1 for a in apps if a.status == ApplicationStatus.REJECTED.value)
            no_response_count = sum(1 for a in apps if a.status in (ApplicationStatus.NO_RESPONSE.value, ApplicationStatus.ON_HOLD.value))

            mock_scores = []
            for m in mocks:
                rep = (m.readiness_json or {}).get("final_report", {})
                if "overall_score" in rep:
                    mock_scores.append(rep["overall_score"])
            avg_mock = round(sum(mock_scores) / len(mock_scores), 1) if mock_scores else 0.0

            ats_scores = [a.ats_score for a in apps if a.ats_score is not None]
            avg_ats = round(sum(ats_scores) / len(ats_scores), 1) if ats_scores else 0.0

            return DashboardMetrics(
                total_jobs=total_jobs or len(apps),
                total_jobs_analyzed=total_jobs or len(apps),
                jobs_to_apply=jobs_to_apply,
                worth_applying=jobs_to_apply,
                jobs_reviewed=jobs_reviewed,
                under_review=jobs_reviewed,
                jobs_skipped=jobs_skipped,
                applications_submitted=apps_submitted,
                applications_sent=apps_submitted,
                interviews=interviews_count,
                offers=offers_count,
                rejected=rejected_count,
                no_response=no_response_count,
                interview_preps_completed=preps,
                mock_interviews_completed=len(mocks),
                average_mock_score=avg_mock,
                average_ats_score=avg_ats,
            )

    @classmethod
    def get_skill_gaps_summary(cls) -> SkillGapSummary:
        with get_db() as db:
            analyses = db.query(JobAnalysisDB).all()
            missing_counts: Dict[str, int] = {}
            demanded_counts: Dict[str, int] = {}

            for a in analyses:
                for skill in (a.missing_skills_json or []):
                    missing_counts[skill] = missing_counts.get(skill, 0) + 1
                    demanded_counts[skill] = demanded_counts.get(skill, 0) + 1
                for skill in (a.matched_skills_json or []):
                    demanded_counts[skill] = demanded_counts.get(skill, 0) + 1

            strong_skills = {"python", "sql", "bigquery", "airflow", "gcp", "google cloud storage", "rag", "vertex ai", "fastapi"}
            transferable_skills = {"aws", "redshift", "s3", "glue", "lambda", "kubernetes", "snowflake"}

            missing_items: List[SkillGapItem] = []
            for skill, cnt in sorted(missing_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                skill_l = skill.lower()
                status = "Transferable" if any(t in skill_l for t in transferable_skills) else "Genuine Gap"
                rec = "Rehearse GCP-to-AWS cloud conceptual mapping." if status == "Transferable" else "Practice core fundamentals and design trade-offs."
                missing_items.append(
                    SkillGapItem(
                        skill_name=skill,
                        frequency_count=cnt,
                        candidate_status=status,
                        recommendation=rec,
                    )
                )

            demanded_items: List[SkillGapItem] = []
            for skill, cnt in sorted(demanded_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                skill_l = skill.lower()
                status = "Verified Strong" if any(s in skill_l for s in strong_skills) else ("Transferable" if any(t in skill_l for t in transferable_skills) else "Genuine Gap")
                demanded_items.append(
                    SkillGapItem(
                        skill_name=skill,
                        frequency_count=cnt,
                        candidate_status=status,
                        recommendation="Verified production strength." if status == "Verified Strong" else "Transferable knowledge.",
                    )
                )

            # Dynamically derive priority learning topics from top missing skills
            priority_topics: List[str] = []
            for item in missing_items[:4]:
                s_lower = item.skill_name.lower()
                if "aws" in s_lower or "glue" in s_lower or "redshift" in s_lower:
                    topic = f"{item.skill_name}: AWS-to-GCP Architectural Service Mapping (Redshift vs BigQuery, Glue vs Airflow)"
                elif "spark" in s_lower or "kafka" in s_lower:
                    topic = f"{item.skill_name}: Distributed Streaming, Partitions, Watermarking & Exactly-Once Semantics"
                elif "k8s" in s_lower or "kubernetes" in s_lower or "docker" in s_lower:
                    topic = f"{item.skill_name}: Container Orchestration, Pod Lifecycle & Production Deployments"
                else:
                    topic = f"{item.skill_name}: Production Implementation, Failure Modes & Design Trade-offs"
                if topic not in priority_topics:
                    priority_topics.append(topic)

            if not priority_topics:
                priority_topics = [
                    "Airflow Fault Tolerance, Exponential Backoff, and DAG Idempotency",
                    "BigQuery Query Cost Optimization (Partitioning, Clustering, Slot Tuning)",
                    "Hybrid Search with FAISS + BM25 & Reciprocal Rank Fusion",
                ]

            return SkillGapSummary(
                top_missing_skills=missing_items,
                top_demanded_skills=demanded_items,
                priority_learning_topics=priority_topics,
            )

    @classmethod
    def get_career_insights(cls, candidate_id: Optional[str] = None) -> Dict[str, Any]:
        """Calculates granular historical intelligence across all tracked applications."""
        with get_db() as db:
            apps_q = db.query(ApplicationDB)
            if candidate_id:
                apps_q = apps_q.filter(ApplicationDB.candidate_id == candidate_id)
            apps = apps_q.all()
            if len(apps) < 3:
                return {
                    "has_sufficient_data": False,
                    "message": "Not enough historical data.",
                    "total_applications": len(apps),
                }

            # Most applied roles
            role_counts: Dict[str, int] = {}
            for a in apps:
                role_counts[a.role_title] = role_counts.get(a.role_title, 0) + 1
            most_applied = sorted(role_counts.items(), key=lambda x: x[1], reverse=True)[:3]

            # Average fit score
            avg_fit = sum(a.fit_score for a in apps) / len(apps) if apps else 0.0

            # Interview conversion
            sent_count = sum(1 for a in apps if a.status in (
                ApplicationStatus.APPLIED.value,
                ApplicationStatus.SCREENING.value,
                ApplicationStatus.INTERVIEWING.value,
                ApplicationStatus.TECHNICAL_ROUND.value,
                ApplicationStatus.HR_ROUND.value,
                ApplicationStatus.OFFER.value,
                ApplicationStatus.REJECTED.value,
                "APPLYING",
                "INTERVIEW",
            ))
            interview_count = sum(1 for a in apps if a.status in (
                ApplicationStatus.INTERVIEWING.value,
                ApplicationStatus.TECHNICAL_ROUND.value,
                ApplicationStatus.HR_ROUND.value,
                ApplicationStatus.OFFER.value,
                "INTERVIEW",
            ))
            conversion_rate = round((interview_count / sent_count * 100), 1) if sent_count > 0 else 0.0

            # Common rejection reasons
            rejection_reasons = []
            for a in apps:
                if a.status == ApplicationStatus.REJECTED.value:
                    if a.final_outcome:
                        rejection_reasons.append(a.final_outcome)
                    for n in (a.notes_json or []):
                        if "reject" in str(n).lower() or "gap" in str(n).lower():
                            rejection_reasons.append(str(n))

            return {
                "has_sufficient_data": True,
                "total_applications": len(apps),
                "most_applied_roles": [f"{r[0]} ({r[1]})" for r in most_applied],
                "average_fit_score": round(avg_fit, 1),
                "interview_conversion_rate": f"{conversion_rate}%",
                "applications_sent": sent_count,
                "interviews_secured": interview_count,
                "rejection_reasons": rejection_reasons[:5] if rejection_reasons else ["Skill gap on cloud requirements"],
            }



class CandidateRepository:
    """Repository for managing Candidate Profiles, Evidences, and Version History."""

    @classmethod
    def get_profile(cls, candidate_id: Optional[str] = None, user_id: Optional[str] = None) -> CandidateProfile:
        with get_db() as db:
            if user_id:
                db_prof = db.query(CandidateProfileDB).filter(CandidateProfileDB.user_id == user_id).first()
                if db_prof:
                    return cls._db_to_model(db_prof)
                user_rec = db.query(UserDB).filter(UserDB.id == user_id).first()
                if user_rec:
                    new_cid = candidate_id or f"cand_{uuid.uuid4().hex[:8]}"
                    new_db_prof = CandidateProfileDB(
                        id=new_cid,
                        user_id=user_id,
                        full_name=user_rec.full_name,
                        email=user_rec.email,
                        professional_summary="Professional candidate profile. Update your summary in Candidate Profile.",
                        skills_json=[],
                        experiences_json=[],
                        projects_json=[],
                        education_json=[],
                        certifications_json=[],
                        achievements_json=[],
                        preferences_json={},
                    )
                    db.add(new_db_prof)
                    db.commit()
                    db.refresh(new_db_prof)
                    return cls._db_to_model(new_db_prof)

            if candidate_id:
                db_prof = db.query(CandidateProfileDB).filter(CandidateProfileDB.id == candidate_id).first()
                if db_prof:
                    return cls._db_to_model(db_prof)

            # Prioritize default verified profile over arbitrary first
            db_prof = db.query(CandidateProfileDB).filter(
                CandidateProfileDB.id.in_(["cand_verified", "trupti_kularkar"])
            ).first()
            if db_prof:
                return cls._db_to_model(db_prof)

            # Fallback to first profile
            db_prof = db.query(CandidateProfileDB).first()
            if db_prof:
                return cls._db_to_model(db_prof)

        # Fallback to parsing candidate files and seed the DB
        from careerpilot.parsers.candidate_parser import CandidateParser
        profile = CandidateParser.parse_all()
        if candidate_id:
            profile.id = candidate_id
        if user_id:
            profile.user_id = user_id
        cls.save_profile(profile, change_summary="Initial master profile baseline", changed_sections=["all"])
        return profile

    @classmethod
    def _db_to_model(cls, db_prof: CandidateProfileDB) -> CandidateProfile:
        skills = [Skill(**s) if isinstance(s, dict) else s for s in (db_prof.skills_json or [])]
        experiences = [Experience(**e) if isinstance(e, dict) else e for e in (db_prof.experiences_json or [])]
        projects = [Project(**p) if isinstance(p, dict) else p for p in (db_prof.projects_json or [])]
        education = [Education(**ed) if isinstance(ed, dict) else ed for ed in (db_prof.education_json or [])]
        achievements = [Achievement(**a) if isinstance(a, dict) else a for a in (getattr(db_prof, "achievements_json", []) or [])]

        pref_dict = db_prof.preferences_json or {}
        preferences = CareerPreference(**pref_dict) if isinstance(pref_dict, dict) else CareerPreference()

        from careerpilot.parsers.evidence_extractor import EvidenceExtractor
        profile = CandidateProfile(
            id=db_prof.id,
            user_id=getattr(db_prof, "user_id", None),
            full_name=db_prof.full_name,
            email=db_prof.email,
            phone=db_prof.phone,
            linkedin_url=db_prof.linkedin_url,
            github_url=db_prof.github_url,
            professional_summary=db_prof.professional_summary,
            skills=skills,
            experiences=experiences,
            projects=projects,
            education=education,
            certifications=list(db_prof.certifications_json or []),
            achievements=achievements,
            preferences=preferences,
            last_updated_at=db_prof.updated_at.isoformat() if db_prof.updated_at else datetime.now(timezone.utc).isoformat(),
        )
        profile.atomic_evidence = EvidenceExtractor.atomize_candidate_profile(profile)
        return profile

    @classmethod
    def save_profile(
        cls,
        profile: CandidateProfile,
        change_summary: str = "Updated profile",
        changed_sections: Optional[List[str]] = None,
        candidate_id: Optional[str] = None,
    ) -> ProfileVersionDB:
        with get_db() as db:
            cid = candidate_id or profile.id
            existing = None
            if cid:
                existing = db.query(CandidateProfileDB).filter(CandidateProfileDB.id == cid).first()
            if not existing and profile.user_id:
                existing = db.query(CandidateProfileDB).filter(CandidateProfileDB.user_id == profile.user_id).first()

            skills_data = [s.model_dump() for s in profile.skills]
            exp_data = [e.model_dump() for e in profile.experiences]
            proj_data = [p.model_dump() for p in profile.projects]
            edu_data = [ed.model_dump() for ed in profile.education]
            cert_data = list(profile.certifications)
            ach_data = [a.model_dump() for a in getattr(profile, "achievements", [])]
            pref_data = profile.preferences.model_dump()

            if existing:
                existing.full_name = profile.full_name
                existing.email = profile.email
                existing.phone = profile.phone
                existing.linkedin_url = profile.linkedin_url
                existing.github_url = profile.github_url
                existing.professional_summary = profile.professional_summary
                existing.skills_json = skills_data
                existing.experiences_json = exp_data
                existing.projects_json = proj_data
                existing.education_json = edu_data
                existing.certifications_json = cert_data
                existing.achievements_json = ach_data
                existing.preferences_json = pref_data
                if profile.user_id:
                    existing.user_id = profile.user_id
                existing.updated_at = datetime.now(timezone.utc)
                db_prof = existing
            else:
                db_prof = CandidateProfileDB(
                    id=cid or profile.id or f"cand_{uuid.uuid4().hex[:8]}",
                    user_id=profile.user_id,
                    full_name=profile.full_name,
                    email=profile.email,
                    phone=profile.phone,
                    linkedin_url=profile.linkedin_url,
                    github_url=profile.github_url,
                    professional_summary=profile.professional_summary,
                    skills_json=skills_data,
                    experiences_json=exp_data,
                    projects_json=proj_data,
                    education_json=edu_data,
                    certifications_json=cert_data,
                    achievements_json=ach_data,
                    preferences_json=pref_data,
                )
                db.add(db_prof)

            db.commit()
            db.refresh(db_prof)

            # Create a Profile Version snapshot
            past_versions_count = db.query(ProfileVersionDB).filter(ProfileVersionDB.candidate_id == db_prof.id).count()
            version_tag = f"v{past_versions_count + 1}.0"
            version_row = ProfileVersionDB(
                id=f"pver_{uuid.uuid4().hex[:8]}",
                candidate_id=db_prof.id,
                version_tag=version_tag,
                profile_json=profile.model_dump(),
                change_summary=change_summary,
                changed_sections_json=changed_sections or ["profile"],
            )
            db.add(version_row)
            db.commit()
            db.refresh(version_row)

            # Sync CandidateEvidenceDB
            from careerpilot.parsers.evidence_extractor import EvidenceExtractor
            evidences = EvidenceExtractor.atomize_candidate_profile(profile)
            # Remove old evidences for candidate
            db.query(CandidateEvidenceDB).filter(CandidateEvidenceDB.candidate_id == db_prof.id).delete()
            for ev in evidences:
                ev_id = f"ev_{db_prof.id}_{ev.id}" if not ev.id.startswith(f"ev_{db_prof.id}_") else ev.id
                db.add(
                    CandidateEvidenceDB(
                        id=ev_id,
                        fact_id=ev.fact_id or ev.id,
                        candidate_id=db_prof.id,
                        source_type=ev.source_type.value if hasattr(ev.source_type, "value") else str(ev.source_type),
                        source_id=ev.source_id,
                        source_document=ev.source_document,
                        section=ev.section,
                        evidence_type=ev.evidence_type.value if hasattr(ev.evidence_type, "value") else str(ev.evidence_type),
                        source_section=ev.source_section,
                        content=ev.content,
                        skill_tags_json=ev.skill_tags,
                        technologies_json=ev.technologies,
                        metrics_json=ev.metrics,
                        confidence=ev.confidence,
                        status=ev.status.value if hasattr(ev.status, "value") else str(ev.status),
                        extra_metadata_json=ev.metadata,
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc),
                    )
                )
            db.commit()
            return version_row

    @classmethod
    def list_profile_versions(cls, candidate_id: str = "trupti_kularkar") -> List[ProfileVersionDB]:
        with get_db() as db:
            return db.query(ProfileVersionDB).filter(
                (ProfileVersionDB.candidate_id == candidate_id) | (ProfileVersionDB.candidate_id == "default_candidate")
            ).order_by(desc(ProfileVersionDB.created_at)).all()

    @classmethod
    def get_profile_version(cls, version_id: str) -> Optional[ProfileVersionDB]:
        with get_db() as db:
            return db.query(ProfileVersionDB).filter(ProfileVersionDB.id == version_id).first()

    @classmethod
    def restore_profile_version(cls, version_id: str) -> CandidateProfile:
        with get_db() as db:
            ver = db.query(ProfileVersionDB).filter(ProfileVersionDB.id == version_id).first()
            if not ver:
                raise ValueError(f"Profile version '{version_id}' not found.")
            profile_data = ver.profile_json
            profile = CandidateProfile.model_validate(profile_data)

        cls.save_profile(
            profile=profile,
            change_summary=f"Restored to version {ver.version_tag} ({ver.change_summary})",
            changed_sections=["all_restored"],
        )
        return profile


class JobDeduplicationRepository:
    """Repository for deduplicating jobs across sources (LinkedIn, Naukri, Website) to a CanonicalJob."""

    @classmethod
    def find_canonical_match(
        cls,
        company_name: Optional[str] = None,
        job_title: Optional[str] = None,
        location: Optional[str] = None,
        source_url: Optional[str] = None,
        raw_text: Optional[str] = None,
        company: Optional[str] = None,
        title: Optional[str] = None,
    ) -> Optional[CanonicalJobDB]:
        import hashlib
        comp = company or company_name or ""
        titl = title or job_title or ""
        comp_norm = comp.strip().lower()
        title_norm = titl.strip().lower()
        text_hash = hashlib.md5((raw_text or "").strip().encode("utf-8")).hexdigest() if raw_text else None

        with get_db() as db:
            # 1. Source URL match (cross-source canonical URL)
            if source_url:
                from careerpilot.analysis.job_deduplicator import JobDeduplicator
                norm_req_url = JobDeduplicator.normalize_url(source_url)
                all_cjobs = db.query(CanonicalJobDB).all()
                for cj in all_cjobs:
                    for u in (cj.source_urls_json or []):
                        if u == source_url or (norm_req_url and JobDeduplicator.normalize_url(u) == norm_req_url):
                            cj.match_type = "CANONICAL_URL_EXACT"
                            cj.job_id = cj.job_ids_json[0] if cj.job_ids_json else cj.id
                            return cj

            # 2. Exact text hash match
            if text_hash:
                match = db.query(CanonicalJobDB).filter(CanonicalJobDB.text_hash == text_hash).first()
                if match:
                    match.match_type = "TEXT_HASH"
                    match.job_id = match.job_ids_json[0] if match.job_ids_json else match.id
                    return match

            # 3. Company + Title normalized match
            if comp_norm and title_norm:
                match = db.query(CanonicalJobDB).filter(
                    CanonicalJobDB.company_normalized == comp_norm,
                    CanonicalJobDB.title_normalized == title_norm,
                ).first()
                if match:
                    match.match_type = "COMPANY_TITLE"
                    match.job_id = match.job_ids_json[0] if match.job_ids_json else match.id
                    return match

            return None

    @classmethod
    def register_or_link_job(
        cls,
        job_id: str,
        company_name: Optional[str] = None,
        job_title: Optional[str] = None,
        source: Optional[str] = None,
        location: Optional[str] = None,
        source_url: Optional[str] = None,
        raw_text: Optional[str] = None,
        title: Optional[str] = None,
        company: Optional[str] = None,
    ) -> CanonicalJobDB:
        comp = company or company_name or "Target Company"
        titl = title or job_title or "Target Role"

        import hashlib
        comp_norm = comp.strip().lower()
        title_norm = titl.strip().lower()
        loc_norm = (location or "Remote").strip().lower()
        text_hash = hashlib.md5((raw_text or f"{comp_norm}_{title_norm}").strip().encode("utf-8")).hexdigest()

        with get_db() as db:
            existing_match = cls.find_canonical_match(
                company_name=comp,
                job_title=titl,
                location=location,
                source_url=source_url,
                raw_text=raw_text,
            )
            if existing_match:
                existing = db.query(CanonicalJobDB).filter(CanonicalJobDB.id == existing_match.id).first()
                if existing:
                    urls = list(existing.source_urls_json or [])
                    if source_url and source_url not in urls:
                        urls.append(source_url)
                        existing.source_urls_json = urls
                    j_ids = list(existing.job_ids_json or [])
                    if job_id not in j_ids:
                        j_ids.append(job_id)
                        existing.job_ids_json = j_ids
                    existing.updated_at = datetime.now(timezone.utc)
                    db.commit()
                    db.refresh(existing)
                    return existing

            canonical_id = f"cjob_{uuid.uuid4().hex[:8]}"
            cjob = CanonicalJobDB(
                id=canonical_id,
                company_name=comp,
                company_normalized=comp_norm,
                job_title=titl,
                title_normalized=title_norm,
                location=location,
                location_normalized=loc_norm,
                text_hash=text_hash,
                source_urls_json=[source_url] if source_url else [],
                job_ids_json=[job_id],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(cjob)
            db.commit()
            db.refresh(cjob)
            return cjob

    get_or_create_canonical = register_or_link_job
    register_canonical_job = register_or_link_job



class ExternalProfileRepository:
    """Repository for managing external profile connections and sync records."""

    @classmethod
    def get_profile(cls, platform: str, candidate_id: str = "trupti_kularkar") -> Optional[ExternalProfileDB]:
        with get_db() as db:
            return db.query(ExternalProfileDB).filter(
                ExternalProfileDB.platform == platform.upper(),
                ExternalProfileDB.candidate_id == candidate_id,
            ).first()

    @classmethod
    def save_profile(
        cls,
        platform: str,
        candidate_id: str = "trupti_kularkar",
        username: Optional[str] = None,
        profile_url: Optional[str] = None,
        is_connected: bool = True,
        sync_status: str = "SYNCED",
        raw_data: Optional[Dict[str, Any]] = None,
    ) -> ExternalProfileDB:
        with get_db() as db:
            existing = db.query(ExternalProfileDB).filter(
                ExternalProfileDB.platform == platform.upper(),
                ExternalProfileDB.candidate_id == candidate_id,
            ).first()

            if existing:
                if username:
                    existing.username = username
                if profile_url:
                    existing.profile_url = profile_url
                existing.is_connected = is_connected
                existing.sync_status = sync_status
                existing.last_synced_at = datetime.now(timezone.utc)
                if raw_data:
                    existing.metadata_json = raw_data
                existing.updated_at = datetime.now(timezone.utc)
                db.commit()
                db.refresh(existing)
                return existing

            new_entry = ExternalProfileDB(
                id=f"ext_{uuid.uuid4().hex[:8]}",
                candidate_id=candidate_id,
                platform=platform.upper(),
                username=username,
                profile_url=profile_url,
                is_connected=is_connected,
                sync_status=sync_status,
                last_synced_at=datetime.now(timezone.utc),
                metadata_json=raw_data or {},
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(new_entry)
            db.commit()
            db.refresh(new_entry)
            return new_entry


