# CareerPilot AI — UI Action & Page Inventory

**Document:** `docs/UI_ACTION_INVENTORY.md`  
**Scope:** Complete inventory of all user interface pages, controls, inputs, service invocations, return types, displayed fields, and database side effects.

---

## 1. Main Home / Landing (`careerpilot/ui/app.py`)
- **Page Title:** CareerPilot AI Home
- **Inputs & Selectors:** None (Navigation & System Health).
- **Service Calls:**
  - `CareerPilotService.get_dashboard_metrics()` $\rightarrow$ returns `DashboardMetrics`.
  - `get_system_health()` $\rightarrow$ returns `SystemHealth`.
- **Displayed Fields:** Total Jobs Analyzed, Jobs to Apply, Applications Active, Average Mock Score, Component Health Badges (RAG, DB, LLM, Truth Guard, File System).
- **Database Side Effects:** Read-only queries to `AnalyticsRepository`.

---

## 2. Page 1: Dashboard (`careerpilot/ui/pages/1_Dashboard.py`)
- **Inputs & Selectors:** None (Read-only intelligence view).
- **Service Calls:**
  - `CareerPilotService.get_dashboard_metrics()` $\rightarrow$ `DashboardMetrics`
  - `CareerPilotService.list_applications()` $\rightarrow$ `List[Application]`
  - `JobRepository.list_jobs()` $\rightarrow$ `List[JobDescriptionDB]`
  - `CareerPilotService.get_skill_gaps_summary()` $\rightarrow$ `SkillGapSummary`
  - `MockSessionRepository.list_all_sessions()` $\rightarrow$ `List[MockInterviewSessionDB]`
- **Displayed Fields:** KPI summary cards, Active Applications table (Company, Role, Fit, ATS Score, System Rec, User Decision, Status, Next Action), Recent Analyzed Jobs, Priority Learning Actions, Recent Mock Sessions.
- **Database Side Effects:** Read-only analytics retrieval.

---

## 3. Page 2: Analyze Job (`careerpilot/ui/pages/2_Analyze_Job.py`)
- **Inputs & Selectors:**
  - Tab 1: Text inputs for Job Title, Company Name, Location, URL, and raw Job Description text area.
  - Tab 2: `st.file_uploader` for `.txt` or `.pdf` JD files with size & extension validation.
  - Tab 3: `st.selectbox` for 10 evaluation benchmark jobs (`data/evaluation/jobs/*.txt`).
  - Decision Override: `st.selectbox` (`APPLY`, `REVIEW`, `SKIP`).
- **Buttons & Actions:**
  - `🚀 Analyze Job Description` (Primary Button): Calls `CareerPilotService.analyze_job(...)`.
  - `💾 Save Decision Override` (Action Button): Calls `CareerPilotService.update_application_decision(...)`.
- **Expected Return Types:** `Tuple[JobAnalysisResult, Application]`.
- **Displayed Fields:** System Recommendation badge, Candidate Fit Score (`%`), Role Reality label, Seniority detection level, Requirements Breakdown table (with match status & evidence IDs), Strengths list, Gaps list, Risk Factors list, Cloud Transferability guide.
- **Database Side Effects:** Saves `JobDescriptionDB`, `JobAnalysisDB`, and creates/updates `ApplicationDB`.

---

## 4. Page 3: Applications Tracker (`careerpilot/ui/pages/3_Applications.py`)
- **Inputs & Selectors:**
  - Filter Selectbox: Status (`ALL`, `SAVED`, `ANALYZED`, `APPLYING`, `APPLIED`, `INTERVIEW`, `OFFER`, `REJECTED`, `WITHDRAWN`, `SKIPPED`).
  - Filter Selectbox: Recommendation (`ALL`, `APPLY`, `REVIEW`, `SKIP`).
  - Text Search: Role filter & Company keywords.
  - Application Selector: Selectbox of active applications.
  - Status Change Selectbox: Pipeline status updater.
  - Note Text Input: Add note field.
- **Buttons & Actions:**
  - `➕ Add Note`: Calls `CareerPilotService.add_application_note(...)`.
  - `💾 Update Status`: Calls `CareerPilotService.update_application_status(...)`.
  - `⬇️ Download Latest Resume`: DOCX file download button.
- **Expected Return Types:** `List[Application]`, `Application`.
- **Displayed Fields:** Main application pipeline table, Application Deep Inspector (Fit score, Recommendation, Status, Next action, Resume version history, Candidate notes, Mock interview history).
- **Database Side Effects:** Updates `ApplicationDB` status, adds notes, records history.

---

## 5. Page 4: Resume Builder (`careerpilot/ui/pages/4_Resume_Builder.py`)
- **Inputs & Selectors:**
  - Target Application Selectbox (`selected_app`).
  - Resume Strategy Selectbox (`AUTO`, `AI_DATA_ENGINEER`, `DATA_ENGINEER`, `GENAI_ENGINEER`, `GCP_DATA_ENGINEER`).
- **Buttons & Actions:**
  - `✨ Generate Tailored Resume` (Primary Button): Calls `CareerPilotService.generate_resume_for_application(...)`.
  - `⬇️ Download ATS Clean DOCX Resume` (Download Button): Streams binary DOCX payload.
- **Expected Return Types:** `Tuple[TailoredResume, ATSReport, Application]`.
- **Displayed Fields:** ATS Compatibility Score (`%`), Keyword Alignment (`%`), Semantic Alignment (`%`), Truth Guard Status (`PASS`), Professional Summary preview, Tailored Experience Bullets (with verified evidence tags), Projects preview, Skills preview, Truth Guard audit table.
- **Database Side Effects:** Saves `ResumeVersionDB`, links version to `ApplicationDB`, exports `.md` and `.docx` artifacts to disk.

---

## 6. Page 5: ATS Analysis (`careerpilot/ui/pages/5_ATS_Analysis.py`)
- **Inputs & Selectors:**
  - Target Application Selectbox.
  - Resume Version Selectbox (`v1.0`, `v2.0`, etc.).
- **Buttons & Actions:** Automatic load / inspection.
- **Service Calls:** `CareerPilotService.evaluate_ats_for_application(...)` $\rightarrow$ `ATSReport`.
- **Displayed Fields:** Overall ATS Score, Must-Have match ratio, Nice-to-Have match ratio, Truth status, Score interpretation, Component Scoring Breakdown table (Keyword, Taxonomy, Semantic, Experience, Structure, Formatting, Readability), Requirements Coverage Matrix table, Missing Requirements alerts, Formatting & Stuffing checks, Optimization suggestions.
- **Database Side Effects:** Caches/updates `ats_report_json` in `ResumeVersionDB`.

---

## 7. Page 6: Interview Prep (`careerpilot/ui/pages/6_Interview_Prep.py`)
- **Inputs & Selectors:**
  - Target Application Selectbox.
  - Preparation Timeline Slider (1, 3, 7, 14 Days).
  - Question Category Filter.
  - Answer Length Mode Radio (`Short 30-45s`, `Standard 60-90s`, `Detailed 2-3m`).
- **Buttons & Actions:**
  - `🚀 Generate Interview Prep Plan`: Calls `CareerPilotService.prepare_interview_for_application(...)`.
- **Expected Return Types:** `Dict[str, Any]` (containing `InterviewPlan`, questions, answers, STAR stories, system design, roadmap, readiness score).
- **Displayed Fields:** Readiness score card, Total questions generated, Study timeline, Categorized Q&A expanders with multi-length evidence-grounded answers, STAR Behavioral narratives, System Design Scenarios, Cloud Transferability guide, Study Schedule roadmap.
- **Database Side Effects:** Saves `InterviewPrepDB` and updates `ApplicationDB.interview_prep_id`.

---

## 8. Page 7: Mock Interview (`careerpilot/ui/pages/7_Mock_Interview.py`)
- **Inputs & Selectors:**
  - Configuration Selectboxes: Application, Interview Mode (Full, Tech, System Design, Behavioral), Difficulty (Adaptive, Junior, Mid, Senior, Lead), Persona (Senior Engineer, Hiring Manager, Strict Architect, Friendly Mentor), Feedback Mode (Coaching, Interview), Question Count Slider (2–12).
  - Answer Text Area (`turn_ans_N`).
- **Buttons & Actions:**
  - `🚀 Start Mock Interview Session`: Calls `CareerPilotService.start_mock_interview_for_application(...)`.
  - `💡 Small Hint (-5%)`: Injects lightweight clue.
  - `💡 Full Hint (-15%)`: Injects structural outline.
  - `🤷 I Don't Know`: Pre-populates honest admission.
  - `💬 Submit Answer & Continue`: Calls `CareerPilotService.submit_mock_answer(...)` and `continue_mock_session(...)`.
  - `⏹️ Finish Interview Early`: Calls `finish_mock_interview(...)`.
  - `🔄 Start New Mock Interview Session`: Resets session state.
- **Expected Return Types:** `MockInterviewState`, `AnswerEvaluation`, `FinalInterviewReport`.
- **Displayed Fields:** Turn question prompt, Follow-up depth level, Turn score, Correct concepts, Missing concepts, Truth warnings, Final report scorecard, Dimension scores table, Topic Mastery table, Strengths, Weaknesses, Recommended study topics, Full conversation transcript.
- **Database Side Effects:** Creates & updates `MockInterviewSessionDB`.

---

## 9. Page 8: Skill Gaps (`careerpilot/ui/pages/8_Skill_Gaps.py`)
- **Inputs & Selectors:** None (Cross-application intelligence).
- **Service Calls:** `CareerPilotService.get_skill_gaps_summary()` $\rightarrow$ `SkillGapSummary`.
- **Displayed Fields:** Top missing skills count, Top demanded skills count, Priority learning roadmap items, Missing skills frequency table, Demanded technologies candidate alignment table.
- **Database Side Effects:** Read-only analytics aggregation across `JobAnalysisDB`.

---

## 10. Page 9: Settings (`careerpilot/ui/pages/9_Settings.py`)
- **Inputs & Selectors:** Read-only configuration inspection.
- **Displayed Fields:** Candidate Source-of-Truth Protection banner (Read-only status of `data/candidate/`), LLM provider settings, Local embedding model, ChromaDB collection names, Decision thresholds, Candidate profile summary.
- **Database Side Effects:** None.

---

## 11. Page 10: About (`careerpilot/ui/pages/10_About.py`)
- **Displayed Fields:** Product vision, Core guardrail rules, System architecture diagram, Verified technology stack, Security & privacy model.
- **Database Side Effects:** None.

---

## 12. Page 11: Evaluation (`careerpilot/ui/pages/11_Evaluation.py`)
- **Buttons & Actions:**
  - `🔄 Re-run All Evaluation Benchmarks`: Executes `evaluate_job_analysis`, `evaluate_rag_retrieval`, `evaluate_truth_guard`, `evaluate_resume_generation`, `evaluate_interview_engine`, `run_regression_suite`.
- **Displayed Fields:** Top KPI cards (RAG Recall@5, MRR, Truth Guard F1, Role Classifier Accuracy, Regression Status), Dual-Store RAG Performance & Method Comparison, 12-Case Golden Audit Breakdown & Confusion Matrix, Job Analysis Extraction Performance, Latency percentiles bar chart, LLM Token & Cost model, Live Event Traces (Zero PII).
- **Database Side Effects:** Read-only benchmark executions.
