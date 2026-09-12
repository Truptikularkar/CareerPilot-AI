# CareerPilot AI — Milestone 12 Architecture & Codebase Audit Report

**Date:** September 4, 2026  
**Document:** `docs/MILESTONE_12_ARCHITECTURE_AUDIT.md`  
**Status:** **AUDITED & ARCHITECTURAL RESOLUTIONS DESIGNED**  
**Audit Scope:** Full repository (`careerpilot/`, `data/`, `tests/`, `docs/`, Streamlit UI pages, Pydantic domain models, SQLAlchemy database schemas, repository layer, LangGraph stateful pipelines, RAG stores, LLM providers, and ATS/Resume generators).

---

## Executive Summary

Before introducing external profile integrations (GitHub, LinkedIn, Naukri) and real Gemini live inference, this audit evaluated the entire CareerPilot AI codebase for systemic stability, data authority, model cleanliness, UI consistency, and data provenance.

The audit identified **17 distinct structural items** requiring architectural correction. Below is the itemized analysis and the approved resolution for each.

---

## Detailed Findings & Resolutions (Items 1 to 17)

### 1. Duplicate Models
- **Findings:**
  - `careerpilot/graphs/state.py` maintained loose/redundant TypedDict definitions (`ResumeGenerationState`, `JobAnalysisState`) where types drifted from canonical domain models in `careerpilot/models/job.py` and `careerpilot/models/resume.py`.
  - `JobRequirement` in `careerpilot/models/job.py` contained legacy duplicate fields (`title`, `description`, `target_skills`, `requirement_type`) alongside standardized fields (`skill_name`, `source_text`, `normalized_skill`, `importance`).
  - `SeniorityDetection` duplicated property aliases for `detected_seniority`, `estimated_level`, and `seniority`.
  - `InterviewReadinessSeed` was defined in `careerpilot/models/ats.py` despite being an interview-domain entity.
- **Resolution:**
  - Retain backwards-compatibility aliases with explicit deprecation wrappers.
  - Standardize all pipeline nodes on canonical Pydantic models.
  - Align `CandidateEvidence` in `models/evidence.py` with full provenance fields.

### 2. Duplicate Services
- **Findings:**
  - Streamlit UI pages frequently mixed calls between `CareerPilotService`, `CandidateService`, `JobRepository`, and `CandidateRepository`.
  - `resume_import_service.py` duplicated extraction logic present in `CandidateParser.parse_all()` and `CandidateService.sync_profile_to_rag()`.
- **Resolution:**
  - Establish a clean service layer hierarchy: UI pages call `CandidateService` for candidate profile/provenance/integrations and `CareerPilotService` for workflow orchestration. Repositories are strictly accessed via the service layer.

### 3. Duplicate Tables
- **Findings:**
  - SQLite database (`careerpilot.db`) contains 11 tables (`candidate_profiles`, `job_descriptions`, `interview_questions`, `mock_sessions`, `skill_gaps`, `candidate_evidences`, `job_analyses`, `interview_preparations`, `applications`, `resume_versions`, `profile_versions`).
  - `applications` table tracked `status` and `fit_score` without storing status transition history or canonical job linkage across multiple sources.
- **Resolution:**
  - Preserve the 11 tables without schema fragmentation.
  - Add `CanonicalJobDB` and `ExternalProfileDB` to model deduplicated jobs and third-party profile sync states cleanly without duplicating existing entities.

### 4. Dead / Unused Code
- **Findings:**
  - `candidate_parser.py` contained unused helper methods for raw string splitting.
  - Evaluation directory contained legacy scratch files (`check_db.py`, unreferenced JSON files).
- **Resolution:**
  - Keep production directories clean; ensure only active service code is referenced.

### 5. Mock / Demo Data Accidentally Used in LOCAL_PRIVATE
- **Findings:**
  - In `careerpilot/llm/factory.py` (lines 28-29), `get_llm_provider()` was unconditionally returning `MockLLMProvider()`:
    ```python
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        return MockLLMProvider()  # Silently mocked all requests!
    ```
    This caused `LOCAL_PRIVATE` mode to silently use mock responses even when valid Gemini credentials were provided!
  - `AnalyticsRepository.get_skill_gaps_summary()` hardcoded static priority learning topics rather than deriving them from actual missing skills in `job_analyses`.
- **Resolution:**
  - Implement `GeminiProvider` using the official `google.genai` SDK (`gemini-3.6-flash`).
  - In `LOCAL_PRIVATE`, never fall back to mock data silently. If Gemini fails, display explicit `GEMINI UNAVAILABLE: <reason>`.
  - Dynamically compute skill gaps and priority topics from live database records.

### 6. Hard-Coded Candidate Information
- **Findings:**
  - `careerpilot/ui/app.py` (lines 78-81) hardcoded:
    `Trupti Kularkar`, `1.9+ Years at Cognizant`, `GCP (BigQuery, Airflow, Pub/Sub, Vertex AI)` in the sidebar.
  - `careerpilot/ui/pages/10_Settings.py` (lines 38-48) hardcoded the same candidate profile strings.
  - If a user edited their profile in SQLite or ran a different candidate profile, these UI components continued displaying static strings.
- **Resolution:**
  - Remove all hardcoded profile strings from `app.py` and `10_Settings.py`.
  - Bind UI displays dynamically to `CandidateService.get_active_profile()`.

### 7. Hard-Coded Fit Scores
- **Findings:**
  - In earlier versions, fallback fit scores defaulted to 80% or 90% when requirements were missing or role match was ambiguous.
- **Resolution:**
  - Implement Phase 5 calibrated fit scoring engine with 9 distinct components, explicit experience shortfall penalties, and zero ungrounded bonuses.

### 8. Hard-Coded Resume Information
- **Findings:**
  - `careerpilot/generators/strategy_engine.py` (lines 32-37 and 55-60) used static summary templates with fixed metric numbers (`1.9+ years`, `BigQuery cost optimization (~25%)`, `reducing data quality incidents by 35%`).
- **Resolution:**
  - Parameterize all summary templates to inject candidate verified metrics and calculated years of experience dynamically from the approved SQLite candidate profile.

### 9. Duplicate UI Metrics
- **Findings:**
  - `1_Dashboard.py` rendered 8 KPI metrics at the top, while sidebar rendered 4 overlapping metrics, and `3_Applications.py` rendered application count metrics.
- **Resolution:**
  - Consolidate dashboard KPIs into a clean 4-card funnel (Total Analyzed, Worth Applying, Active Applications, Mock Interviews).
  - Clean up sidebar metrics to prevent visual clutter.

### 10. Duplicate Tables
- **Findings:**
  - `1_Dashboard.py` rendered two near-identical tables: "Active Applications" and "Recent Analyzed Jobs", both listing the same evaluated job records.
- **Resolution:**
  - Streamline `1_Dashboard.py` to display the active application funnel and career insights, directing granular job inspection to `3_Applications.py`.

### 11. Unused Benchmark Data in Production UI
- **Findings:**
  - `2_Analyze_Job.py` included a tab labeled "📂 Load Evaluation Benchmark" (`01_ai_data_engineer.txt`, `02_data_engineer_gcp.txt`, etc.). This developer evaluation feature cluttered the candidate's real job application flow.
- **Resolution:**
  - Remove the benchmark tab from `2_Analyze_Job.py`.
  - Retain benchmark suites exclusively on `12_Evaluation.py`.

### 12. Incorrect Page Numbering
- **Findings:**
  - Project documentation referenced 10 Streamlit pages (e.g. `9_Settings.py`, `10_About.py`).
  - In reality, `9_Candidate_Profile.py` was introduced, shifting Settings to `10_Settings.py`, About to `11_About.py`, and adding `12_Evaluation.py`.
- **Resolution:**
  - Update all documentation and navigation links to reflect the canonical 12-page structure.

### 13. Documentation Inconsistencies
- **Findings:**
  - `README.md` listed `careerpilot/mock_interview/` in its directory tree, but the actual codebase path is `careerpilot/interview/`.
- **Resolution:**
  - Correct the directory tree in `README.md` and `ARCHITECTURE.md`.

### 14. SQLite vs. YAML Source Conflicts
- **Findings:**
  - `profile.yaml`, `experience.md`, `projects.md`, and `skills.md` in `data/candidate/` acted as competing sources of truth against `data/careerpilot.db`. Edits in SQLite were not reflected in the YAML files, and some loaders re-read YAML files, overwriting database changes.
- **Resolution:**
  - Establish **SQLite as the SINGLE authoritative source of truth**.
  - Treat YAML/Markdown files strictly as **Import / Export / Backup / Migration** representations.
  - Implement bidirectional export to keep file backups in sync when SQLite changes.

### 15. ChromaDB Source-of-Truth Mistakes
- **Findings:**
  - `CandidateStore.parse_candidate_directory()` indexed static YAML files from disk rather than reading verified candidate facts from the SQLite database.
- **Resolution:**
  - Enforce: **Candidate Profile (SQLite) ➔ Evidence Ledger (SQLite) ➔ ChromaDB (Vector Index)**.
  - ChromaDB is an index, never a primary source of truth.

### 16. Gemini Fallback Problems
- **Findings:**
  - The system silently defaulted to `MockLLMProvider()` whenever Gemini was unavailable or threw an exception, giving users the illusion of AI reasoning while returning canned test data.
- **Resolution:**
  - Introduce strict error propagation in `LOCAL_PRIVATE` mode: show `GEMINI UNAVAILABLE: <reason>` with detailed diagnosis. Keep `MockLLMProvider` strictly for unit testing.

### 17. Resume Generation Data Provenance Problems
- **Findings:**
  - `BulletSelector` assembled resume bullets from candidate text without verifying that every bullet mapped to a verifiable atomic `fact_id` in the SQLite evidence ledger.
- **Resolution:**
  - Implement `ResumePreflight` and audit every claim against candidate evidence provenance before rendering DOCX or PDF.
