# CAREERPILOT AI — MILESTONE 12 ENGINEERING REPORT
## Career Intelligence, Data Provenance & External Profile Integration

**Author:** Antigravity AI Engineering Team  
**Date:** September 4, 2026  
**Status:** COMPLETED & VERIFIED  
**Repository Branch / Workspace:** `c:/Users/DELL/OneDrive/Desktop/RAG`  
**Active Ground Truth:** SQLite Database (`data/careerpilot.db`) — Candidate: Trupti Kularkar (`trupti_kularkar`)  
**Test Suite Pass Rate:** 100% (17 / 17 Milestone 12 Tests | 209 / 209 Full Regression Suite)

---

## 1. Executive Summary

Milestone 12 transitions CareerPilot from a local resume/interview assistant into an end-to-end **Autonomous Career Intelligence Platform**. Rather than merely formatting documents, CareerPilot now provides:
1. **Authoritative Canonical Data Ground Truth:** Full persistence in SQLite (`data/careerpilot.db`), with dynamic profile hydration across the entire Streamlit UI.
2. **End-to-End Data Provenance:** Every statement, bullet point, and skill links to an evidentiary source (`SQLITE_CANONICAL`, `GITHUB`, `LINKEDIN_EXPORT`, `NAUKRI`, `RESUME_PDF`, `MANUAL_ENTRY`).
3. **Live Gemini 3.6 Flash Integration:** Clean integration with `google.genai` SDK using `gemini-3.6-flash`, with real-time status diagnostics and strict no-silent-mock-fallback enforcement in `LOCAL_PRIVATE` mode.
4. **Calibrated 9-Component Job Fit Engine:** Multi-dimensional alignment analysis with non-linear penalties for experience shortfalls and missing must-have technical requirements.
5. **Canonical Job Deduplication:** Normalized company/title matching and SHA-256 content hashing across LinkedIn, Naukri, and Company Portals.
6. **External Profile Ingestion:** Strictly adhering to Terms of Service (ZERO web scraping):
   - **GitHub:** Public REST API with Windows SSL handling for `Truptikularkar`, classifying repositories into `PERSONAL_PROJECT` with an approval ledger.
   - **LinkedIn:** Authorized export parser with strict documentation of API field limitations and anti-scraping compliance.
   - **Naukri:** Profile export and manual text parser with explicit legal notice documenting absence of public developer APIs.
7. **Preflight Resume Data Lock:** Strict anti-hallucination verification halting generation if ungrounded claims or unauthorized experiences are detected.
8. **1-Page Resume Compression Engine:** Adaptive 3-pass typography and spacing optimizer backed by PyMuPDF (`fitz`), guaranteeing `page_count == 1` for early-career candidates.
9. **Full Funnel Career Intelligence:** Application tracking across 14 lifecycle stages with stage transition histories and funnel conversion metrics.

---

## 2. Architecture & Core Subsystems

### 2.1. Canonical SQLite Ground Truth & Provenance Ledger
- All candidate data flows from `data/careerpilot.db`.
- Every skill, project bullet, and experience entry references a `fact_id` and provenance metadata (`source_type`, `source_id`, `source_document`, `status`, `verified_at`).
- All Streamlit pages (`app.py`, `1_Dashboard.py`, `2_Analyze_Job.py`, `3_Applications.py`, `9_Candidate_Profile.py`, `10_Settings.py`) load dynamically from `CandidateService.get_active_profile()`, eliminating hardcoded mock candidate data.

### 2.2. Live LLM Integration (`GeminiProvider`)
- Implemented in `careerpilot/llm/gemini_provider.py` using `google.genai.Client`.
- Uses `gemini-3.6-flash`.
- In `CAREERPILOT_MODE=LOCAL_PRIVATE`, if the Gemini API key is missing or calls fail, the factory raises an explicit `RuntimeError("GEMINI UNAVAILABLE: ...")` rather than silently defaulting to a mock provider.
- Dynamic telemetry captures connection status, latency, error reasons, and timestamp of last successful invocation.

### 2.3. Calibrated 9-Component Job Fit Engine
Implemented in `careerpilot/analysis/fit_scorer.py`, evaluating:
1. **Core Skills Match (20%)**
2. **Secondary / Tooling Skills (10%)**
3. **Domain & Industry Relevance (12%)**
4. **Experience Level & Seniority (15%)**
5. **Project Complexity & Scale (12%)**
6. **Education & Certifications (6%)**
7. **ATS / Semantic Compatibility (10%)**
8. **Role Trajectory & Transferable Skills (8%)**
9. **Cultural / Leadership Signals (7%)**

#### Calibration & Penalty Rules:
- **Material Experience Shortfall:** If job requires >= 3 years and candidate has < 2 years (shortfall >= 1.0 year):
  - Experience score is penalized by -20.0 points.
  - Overall composite score is penalized by -10.0 points.
- **Missing Must-Have Technical Skills:**
  - Penalty of -10.0 points per missing must-have requirement (up to -30.0 max).

### 2.4. Job Deduplication Engine
Implemented in `careerpilot/analysis/job_deduplicator.py`:
- **Deterministic Text Hash:** SHA-256 hash of normalized job description text.
- **Normalized Fuzzy Match:** Normalized company name (stripped of Inc, LLC, Corp) and normalized job title.
- Enables multi-source ingestion (LinkedIn, Naukri, Company Portals) without polluting candidate application pipelines.

### 2.5. External Profile Integrations (Zero Scraping Policy)
- **GitHub (`careerpilot/integrations/github_connector.py`):**
  - Fetches repositories, languages, commit activity, and stars via `api.github.com/users/{username}/repos`.
  - Windows SSL issue mitigated via custom `ssl.create_default_context(cafile=certifi.where())` and fallback contexts.
  - Classifies repositories as `PERSONAL_PROJECT` or `COMMERCIAL_CONTRIBUTION`.
  - Stages evidence with pending status requiring candidate explicit approval before writing to canonical profile.
- **LinkedIn (`careerpilot/integrations/linkedin_connector.py`):**
  - Zero scraping enforcement.
  - Documents API access restrictions: `r_liteprofile` provides only basic identity; full work history requires LinkedIn Learning/Partner enterprise permissions.
  - Provides automated CSV export parser (`Positions.csv`, `Skills.csv`) to map records into the evidence ledger.
- **Naukri (`careerpilot/integrations/naukri_connector.py`):**
  - Zero scraping enforcement.
  - Clear architectural warning: Naukri offers no public developer REST API (only enterprise recruiter APIs).
  - Provides structured profile text / manual copy parser to ingest sections into candidate evidence ledger.

### 2.6. Preflight Resume Data Lock
Implemented in `careerpilot/generators/resume_preflight.py`:
- Runs anti-hallucination verification before resume compilation or export.
- Verifies candidate identity, registered employers, verified skills, and project claims against `CandidateEvidenceDB` and canonical profile.
- Halts generation with `DataLockViolation` if unverified claims or synthetic companies are detected.

### 2.7. 1-Page Resume Compression Engine
Implemented in `careerpilot/generators/resume_pdf.py`:
- Tailored for early-career candidates (< 3 years experience, e.g., Trupti Kularkar with 1.9 years).
- **Prioritization:** Top 3 relevant experiences, top 4 high-impact projects, top 12 verified skills.
- **3-Pass Adaptive Optimizer:**
  - *Pass 1 (Default):* Normal margins (36pt), 10pt font, standard leading.
  - *Pass 2 (Tight):* 28pt margins, 9.5pt font, reduced bullet spacing.
  - *Pass 3 (Ultra-Compact):* 24pt margins, 9.0pt font, condensed item padding.
- **PyMuPDF Validation:** Post-compilation verification reading page count with `fitz.open(stream=..., filetype="pdf")`. Raises error if `page_count != 1`.

### 2.8. Application Intelligence & Funnel Analytics
- **14 Lifecycle Statuses:** `SAVED`, `APPLIED`, `RESUME_VIEWED`, `SCREENING`, `OA_SCHEDULED`, `OA_SUBMITTED`, `TECHNICAL_ROUND_1`, `TECHNICAL_ROUND_2`, `SYSTEM_DESIGN`, `BEHAVIORAL_ROUND`, `FINAL_ROUND`, `OFFER_RECEIVED`, `ACCEPTED`, `REJECTED`, `WITHDRAWN`.
- Transition history tracked with timestamps and notes in `application_status_history`.
- Funnel metrics (conversion rate, drop-off stages, average time-to-first-response) surfaced in `1_Dashboard.py`.

---

## 3. Data Sources Matrix

| Source | Type | Status | Sync Mechanism | Ground Truth Authority |
| :--- | :--- | :--- | :--- | :--- |
| **SQLite (`careerpilot.db`)** | Relational Database | Active & Primary | Direct SQLAlchemy Session | **Authoritative Ground Truth** |
| **Master Resume PDF** | Document File | Imported | `pdfplumber` Parser | Supporting Evidence |
| **GitHub API** | External REST API | Connected | Public API (`Truptikularkar`) | Staged Evidence (`PERSONAL_PROJECT`) |
| **LinkedIn** | Archive Export | Supported (Export) | CSV / JSON Archive Parser | Staged Evidence (`LINKEDIN_EXPORT`) |
| **Naukri** | Profile Export | Supported (Manual) | Formatted Text Parser | Staged Evidence (`NAUKRI`) |
| **Candidate RAG** | Vector DB (Chroma) | Synchronized | `all-MiniLM-L6-v2` Embeddings | Fast Semantic Retrieval |
| **Gemini 3.6 Flash** | Cloud LLM | Connected | `google.genai` Client | Generative & Evaluative Engine |

---

## 4. Test Verification & Results

### 4.1. Milestone 12 Test Suite (`tests/test_milestone_12.py`)
All 17 dedicated tests passed successfully:

| Test Case | Description | Result |
| :--- | :--- | :--- |
| `test_canonical_profile_loading_from_sqlite` | Verifies dynamic hydration from SQLite for `trupti_kularkar` | **PASSED** |
| `test_data_provenance_schema` | Verifies `CandidateEvidenceDB` schema and provenance fields | **PASSED** |
| `test_evidence_ledger_completeness` | Validates minimum 40+ verified candidate evidence items | **PASSED** |
| `test_gemini_provider_live_or_explicit_error` | Verifies live Gemini API call or explicit failure without mock fallback | **PASSED** |
| `test_calibrated_fit_scoring_9_components` | Validates 9 distinct sub-scores summing correctly | **PASSED** |
| `test_experience_shortfall_penalty` | Tests -20.0 / -10.0 penalty deduction when shortfall >= 1.0 yr | **PASSED** |
| `test_must_have_missing_penalty` | Tests calibrated penalty for missing must-have technologies | **PASSED** |
| `test_job_deduplication_hash_and_normalized` | Verifies SHA-256 hash and normalized company/title deduplication | **PASSED** |
| `test_application_pipeline_14_statuses` | Validates all 14 lifecycle statuses and history transition logging | **PASSED** |
| `test_github_integration_repos_and_classification`| Validates repository fetching, classification, and approval staging | **PASSED** |
| `test_linkedin_connector_policy_and_export_parsing`| Validates zero-scraping policy and CSV export parsing | **PASSED** |
| `test_naukri_connector_policy_and_manual_parsing` | Validates zero-scraping policy and manual text parsing | **PASSED** |
| `test_data_sources_status_matrix` | Validates unified data sources connectivity matrix | **PASSED** |
| `test_resume_preflight_data_lock_pass` | Validates pass result for verified ground truth claims | **PASSED** |
| `test_resume_preflight_data_lock_blocks_hallucination`| Verifies preflight lock blocks unverified employers and skills | **PASSED** |
| `test_1_page_resume_pdf_engine_guarantee` | Validates PyMuPDF verifies `page_count == 1` after adaptive loop | **PASSED** |
| `test_career_intelligence_insights_analytics` | Validates conversion rate and stage analytics calculation | **PASSED** |

### 4.2. Full Regression Test Suite
Ran entire project test suite across all subsystems:
- **Total Tests Collected:** 209
- **Passed:** 209
- **Failed:** 0
- **Errors:** 0
- **Execution Time:** 29.16s

---

## 5. UI Improvements & User Experience

1. **`app.py` & Navigation:**
   - Dynamic candidate profile loading directly from SQLite.
   - Real-time "Data Sources" badge in the sidebar reflecting live status of SQLite, GitHub, Gemini, and RAG.
2. **`1_Dashboard.py`:**
   - Added **Career Intelligence & Funnel Analytics** tab showcasing conversion rates, drop-off stages, and pipeline breakdown across all 14 stages.
3. **`2_Analyze_Job.py`:**
   - Multi-source job intake with automatic duplicate detection banner.
   - Calibrated 9-component fit score radar/breakdown showing exact penalties applied for experience shortfalls.
4. **`3_Applications.py`:**
   - 14-stage lifecycle pipeline with one-click status transitions and full audit history.
5. **`9_Candidate_Profile.py`:**
   - Added **External Profiles** tab:
     - GitHub sync with repository classification and approval ledger.
     - LinkedIn export archive uploader.
     - Naukri text importer with zero-scraping compliance advisory.
6. **`10_Settings.py`:**
   - Dynamic candidate selection, live Gemini API health badge, and System-Wide Data Sources Status matrix.

---

## 6. Known Limitations & Future Roadmap

1. **LinkedIn / Naukri Direct APIs:** Direct real-time bidirectional syncing is constrained by LinkedIn and Naukri developer platform access policies. Manual export parsing and authorized paste intake remain the recommended compliant pathways.
2. **ChromaDB Windows Telemetry Warning:** A non-blocking deprecation warning on Python 3.14 regarding `asyncio.iscoroutinefunction` is noted and will be addressed in future upstream ChromaDB releases.
3. **Multi-Page Resumes for Senior Profiles:** The 1-page engine strictly targets profiles with < 3 years experience. Profiles with >= 5 years will automatically graduate to a 2-page template standard in future milestones.
