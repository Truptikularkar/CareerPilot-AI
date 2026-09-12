# CareerPilot AI — UI Test & Verification Matrix

**Document:** `docs/UI_TEST_MATRIX.md`  
**Scope:** Action-by-action verification across all 11 Streamlit pages in CareerPilot AI.

---

## 1. UI Action Test Matrix

| Page | Action / Trigger | Input Data / Condition | Expected Result | Actual Result | Status | Error Discovered | Applied Fix |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Dashboard** (`1_Dashboard.py`) | Page Load | Existing SQLite applications | KPI cards, active applications table, recent jobs, skill weaknesses, and mock session history display cleanly. | All sections render with correct metrics; zero errors. | **PASS** | None | Verified analytics repository queries. |
| **Analyze Job** (`2_Analyze_Job.py`) | Paste JD & Click "Analyze Job Description" | Standard JD text (AI Data Engineer) | LangGraph parses requirements, retrieves RAG evidence, calculates fit score (90%+), displays recommendation badge, role reality, seniority. | Full analysis rendered with all 5 tabs active. | **PASS** | `AttributeError: SeniorityDetection has no attribute estimated_level` | Added `@property estimated_level` on `SeniorityDetection` and updated UI to use `detected_seniority`. |
| **Analyze Job** (`2_Analyze_Job.py`) | Select Benchmark Job | `01_ai_data_engineer.txt` | Pre-populates JD text area with benchmark file content. | Benchmark loaded and analyzed successfully. | **PASS** | None | Tested across all 10 evaluation jobs. |
| **Analyze Job** (`2_Analyze_Job.py`) | Upload File (TXT/PDF) | Valid PDF or TXT | Extracts text safely within size/extension constraints. | Text extracted and analyzed cleanly. | **PASS** | None | File parser handles PDF/TXT with size validation. |
| **Analyze Job** (`2_Analyze_Job.py`) | Decision Override | Change to `APPLY` / `SKIP` & click "Save Decision Override" | Updates user decision without altering system recommendation. | State persisted in DB and UI refreshed with updated badge. | **PASS** | None | Separated `system_recommendation` from `user_decision`. |
| **Applications** (`3_Applications.py`) | Filter by Status / Recommendation / Keyword | `Status: ANALYZED` | Filters application table instantaneously. | Applications table updates dynamically. | **PASS** | None | Implemented local pandas/list comprehension filtering. |
| **Applications** (`3_Applications.py`) | Deep Inspect Application | Select active application | Displays summary metrics, resume version history, notes, mock history, and status update panel. | All inspector tabs populate with linked entities. | **PASS** | None | Entity relationships verified. |
| **Applications** (`3_Applications.py`) | Add Note | "Recruiter LinkedIn message received" | Appends note to application record in SQLite. | Note appears immediately in notes history tab. | **PASS** | None | `add_application_note` verified in service layer. |
| **Applications** (`3_Applications.py`) | Update Pipeline Status | Select `APPLIED` + click "Update Status" | Updates pipeline status to `APPLIED`. | Application record updated in DB and reflected in UI. | **PASS** | None | Status transition verified. |
| **Resume Builder** (`4_Resume_Builder.py`) | Select Strategy & Click "Generate Tailored Resume" | Strategy `AI_DATA_ENGINEER` | LangGraph selects bullets, audits Truth Guard (100% grounded), runs ATS evaluation, exports `.md` & `.docx`. | Tailored resume preview displays summary, bullets, projects, skills, Truth Guard audit table. | **PASS** | `AttributeError: ATSReport has no attribute keyword_alignment` | Added `@property keyword_alignment` and `@property keyword_coverage` on `ATSReport`. |
| **Resume Builder** (`4_Resume_Builder.py`) | Download DOCX Resume | Click "Download ATS Clean DOCX" | Streams `.docx` binary file with clean ATS typography and linear layout. | Valid DOCX file downloaded. | **PASS** | None | `DocxGenerator` verified. |
| **ATS Analysis** (`5_ATS_Analysis.py`) | Select Application & Version | Generated Resume `v1.0` | Displays ATS Compatibility Score, Must-Have match, Nice-to-Have match, Truth status, 7-component breakdown table, coverage matrix, and formatting checks. | Detailed ATS report rendered cleanly with zero missing attributes. | **PASS** | None | Integrated with canonical `ATSReport`. |
| **Interview Prep** (`6_Interview_Prep.py`) | Select Timeline (7 Days) & Click "Generate Prep Plan" | Target Application | Generates role-specific questions, multi-length answers, STAR stories, system design scenarios, and daily study roadmap. | All 5 preparation tabs display evidence-grounded content. | **PASS** | `ans.short_answer` / `sd.scenario_title` alias mismatch | Added property accessors on `InterviewAnswer`, `SystemDesignScenario`, and `PreparationRoadmap`. |
| **Mock Interview** (`7_Mock_Interview.py`) | Configure & Click "Start Mock Interview" | Mode: `FULL_INTERVIEW`, Diff: `ADAPTIVE` | Initializes session state, loads questions, asks Turn 1 question prompt. | Turn 1 question displayed with difficulty badge and follow-up depth. | **PASS** | None | State initialization verified. |
| **Mock Interview** (`7_Mock_Interview.py`) | Candidate Answer Submission | Answer text with GCP BigQuery & Airflow | Evaluates answer across 10 dimensions, checks Truth Guard, updates topic mastery, and routes to next question. | Real-time coaching tip and turn score displayed; advances to Turn 2. | **PASS** | None | 10-dimensional evaluation verified. |
| **Mock Interview** (`7_Mock_Interview.py`) | Use Hint / "I Don't Know" | Click "Small Hint" or "I Don't Know" | Applies hint penalty or records honest gap without crashing. | Hint displayed and penalty tracked in evaluation. | **PASS** | None | Hint mode penalty calculation verified. |
| **Mock Interview** (`7_Mock_Interview.py`) | Finish Interview | Click "Finish Interview Early & View Report" | Compiles `FinalInterviewReport`, calculates overall and sub-scores, topic mastery, strengths/weaknesses. | Complete scorecard and full transcript rendered. | **PASS** | None | `finish_mock_interview` verified. |
| **Skill Gaps** (`8_Skill_Gaps.py`) | Page Load | Analyzed JDs in database | Aggregates missing skills, demanded technologies, and priority learning roadmap. | Ranked market skill demand displayed cleanly. | **PASS** | None | Aggregation queries verified. |
| **Settings** (`9_Settings.py`) | Page Load | Environment settings | Displays Read-Only candidate protection banner, model settings, decision thresholds, and profile overview. | All configuration cards rendered cleanly. | **PASS** | None | Read-only candidate source of truth verified. |
| **About** (`10_About.py`) | Page Load | Static content | Renders product mission, core guardrails, system architecture, and tech stack. | High-quality documentation rendered. | **PASS** | None | Markdown content verified. |
| **Evaluation** (`11_Evaluation.py`) | Click "Re-run All Evaluation Benchmarks" | Golden evaluation datasets | Runs automated benchmarks for Job Analysis, RAG, Truth Guard, Resume, Interview, and Regression suite; displays live latencies and traces. | All benchmark tables, confusion matrices, and latency charts populated. | **PASS** | None | Benchmark pipeline verified. |

---

## 2. Test Execution Summary

- **Total UI Actions Tested:** 21
- **PASS Count:** 21
- **FAIL Count:** 0
- **BLOCKED Count:** 0
- **Overall UI Stability Status:** **100% PASS**
