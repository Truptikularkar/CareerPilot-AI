# CareerPilot AI — Final UI Test & Verification Matrix

**Date:** 2026-08-31  
**Scope:** Complete functional testing matrix across all 12 Streamlit application pages.

---

## 1. Application Page Action Matrix

| Page | Action | Input | Expected Output | Actual Output | Status | Error Found | Fix Applied |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`1_Dashboard.py`** | Load Dashboard | Default DB session | Key metrics (total jobs, apply count, avg score) & recent applications | All metric tiles and pipeline tables rendered cleanly | **PASS** | None | Presentation datetime formatter applied |
| **`2_Analyze_Job.py`** | Paste & Analyze JD | AI Data Engineer JD text | Role classified as `AI_DATA_ENGINEER`, fit score ~90%, Decision: `APPLY` | Seniority detected as MID, Fit score calculated, Saved to DB | **PASS** | `AttributeError: SeniorityDetection has no attribute estimated_level` | Added `.estimated_level` property alias on `SeniorityDetection` |
| **`3_Applications.py`** | Update Application Status | Change status to `INTERVIEW` | Application updated in SQLite with timestamp and note | Status badge updated to `INTERVIEW` | **PASS** | `TypeError: datetime is not subscriptable` | Used `format_datetime()` at UI display boundary |
| **`4_Resume_Builder.py`** | Generate Resume | Select App, Strategy: `AUTO` | `TailoredResume` generated, Truth Guard PASS, ATS score ~95% | Resume displayed across 4 tabs with ATS metrics | **PASS** | `AttributeError: ATSReport has no attribute keyword_alignment` | Added `.keyword_alignment` component accessor on `ATSReport` |
| **`4_Resume_Builder.py`** | Download PDF | Click `⬇️ Download ATS Clean PDF` | Valid `.pdf` stream downloaded, single column, searchable text | Native PDF downloaded and validated with `PDFValidator` | **PASS** | `AttributeError: TailoredResume has no attribute pdf_path` | Decoupled artifacts via `ResumeArtifactBundle` & `CareerPilotService.get_or_generate_resume_artifacts()` |
| **`4_Resume_Builder.py`** | Download DOCX | Click `⬇️ Download ATS Clean DOCX` | Valid `.docx` file downloaded with clean styles and bullets | DOCX downloaded successfully | **PASS** | None | Implemented `DocxResumeExporter` |
| **`4_Resume_Builder.py`** | Switch Version | Select `v1.0` from dropdown | Displays exact `v1.0` resume content and ATS score | Version 1 loaded with correct historical metrics | **PASS** | `TypeError: datetime subscriptable` in version choice label | Used `format_datetime()` for version dropdown items |
| **`5_ATS_Analysis.py`** | Inspect ATS Breakdown | Select active application | 6-component radar/score breakdown, requirement coverage matrix | All components and missing requirements rendered | **PASS** | None | Contract aligned with `ATSReport` |
| **`6_Interview_Prep.py`** | Generate Study Plan | Select Target Job | Technical Q&A, STAR stories, system design architectures, 1/3/7-day roadmap | Full curriculum rendered with evidence citations | **PASS** | None | Validated with `InterviewPrepGraph` |
| **`7_Mock_Interview.py`** | Practice 5-Turn Interview | Audio/Text answers | Real-time 10D scoring, dynamic follow-ups, final scorecard | Completed with live feedback and radar score | **PASS** | None | Verified with `MockInterviewGraph` |
| **`8_Skill_Gaps.py`** | Market Skill Analysis | Aggregate jobs | High-demand skill breakdown, GCP-to-AWS transferable bridges | Displayed transferability matrix and priority learning | **PASS** | None | Verified with `SkillGapSummary` |
| **`9_Candidate_Profile.py`** | Add Personal Project | "AI Ticket Classifier", type: `PERSONAL_PROJECT` | Added to profile, isolated from experience, synced to RAG | New project saved, ChromaDB evidence indexed | **PASS** | `sqlite3.OperationalError: no column achievements_json` | Added automatic `ALTER TABLE` migration in `init_db()` |
| **`9_Candidate_Profile.py`** | Master Resume Import | Upload resume `.pdf` | Diff matrix generated (`ADDED`, `REMOVED`), selective merge | Changes reviewed, approved, and merged to active profile | **PASS** | `ModuleNotFoundError: pypdf` | Replaced with `pymupdf` (PyMuPDF) across parsing pipeline |
| **`9_Candidate_Profile.py`** | Version Rollback | Click `Restore Version v1.0` | Active profile reverted to initial baseline snapshot | Reverted snapshot and synchronized with RAG | **PASS** | Empty initial experience in SQLite seeding | Enriched `init_db()` to seed full profile from `CandidateParser.parse_all()` |
| **`10_Settings.py`** | System Settings | View Configuration | LLM Provider, Vector Store paths, Environment modes | Clean system status and verified candidate identity | **PASS** | None | Reordered page number cleanly |
| **`11_About.py`** | Architecture Overview | Browse documentation | Full system diagrams, tech stack, and portfolio positioning | Rendered architecture documentation | **PASS** | None | Reordered page number cleanly |
| **`12_Evaluation.py`** | AI Evaluation Suite | Run Deep RAG Benchmarks | Multi-dataset retrieval precision, Truth Guard pass rate, ATS scores | 100% metrics displayed with latency and token telemetry | **PASS** | None | Verified with Milestone 11 evaluation runners |
