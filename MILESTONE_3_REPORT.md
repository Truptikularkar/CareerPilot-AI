# Milestone 3 Report — Job Analysis Engine & LangGraph Agent

**Project:** CareerPilot AI  
**Milestone:** 3 (Job Analysis Engine & LangGraph Agent)  
**Status:** Completed & Validated  
**Date:** 2026-08-30  

---

## 1. Architecture Implemented

Milestone 3 implements the intelligent Job Analysis subsystem of **CareerPilot AI**, orchestrating Job Description parsing, role classification, work distribution estimation (Role Reality), requirement extraction, candidate RAG grounding, experience gap calculation, cloud transferability evaluation, deterministic fit scoring, risk analysis, and final recommendation generation (`APPLY` / `REVIEW` / `SKIP`).

```
==================================================================================================
                                    CAREERPILOT JOB ANALYSIS PIPELINE
==================================================================================================

  [Unstructured Job Description] (Text / TXT / PDF)
                │
                ▼
  ┌───────────────────────────────┐
  │      JobDescriptionParser     │ ──▶ Normalizes text, preserves bullet nuances,
  └───────────────┬───────────────┘     extracts explicit years & taxonomy categories
                  │
                  ▼
  ┌───────────────────────────────┐
  │   RoleClassifier & Reality    │ ──▶ Discovers primary role, secondary role,
  └───────────────┬───────────────┘     and practical work distribution % (e.g. 50% DE / 30% AI)
                  │
                  ▼
  ┌───────────────────────────────┐
  │     EvidenceMatcher (RAG)     │ ──▶ Queries Candidate Evidence Store (data/candidate/)
  └───────────────┬───────────────┘     Verifies SUPPORTED claims & calculates tenure gaps
                  │
                  ▼
  ┌───────────────────────────────┐
  │   CloudTransferability & Pref │ ──▶ Evaluates GCP ➔ AWS/Azure transferability &
  └───────────────┬───────────────┘     preference alignment (Pune/Nagpur, CTC, direction)
                  │
                  ▼
  ┌───────────────────────────────┐
  │     CandidateJobFitScorer     │ ──▶ Deterministic weighted 7-component scoring model
  └───────────────┬───────────────┘     with Must-Have Gap Penalties
                  │
                  ▼
  ┌───────────────────────────────┐
  │         RiskAnalyzer          │ ──▶ Detects Experience, Seniority, Cloud, and Tech risks
  └───────────────┬───────────────┘     with severity ratings (LOW / MEDIUM / HIGH / CRITICAL)
                  │
                  ▼
  ┌───────────────────────────────┐
  │        DecisionEngine         │ ──▶ Evaluates thresholds + risks ➔ APPLY / REVIEW / SKIP
  └───────────────┬───────────────┘     Outputs structured, explainable reasoning
                  │
                  ▼
  [JobAnalysisResult / CLI Report]
```

---

## 2. Files Created & Modified

### 📦 Models & Configuration
- [`careerpilot/models/job.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/models/job.py) — Pydantic schemas for `JobRequirement`, `RoleClassification`, `RoleReality`, `SeniorityDetection`, `CloudTransferability`, `RequirementMatch`, `RiskItem`, `FitScoreBreakdown`, `JobDescription`, and `JobAnalysisResult`.
- [`careerpilot/models/candidate.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/models/candidate.py) — Enhanced candidate model validators for resilient enum mapping.
- [`careerpilot/core/constants.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/core/constants.py) — Standardized enums (`SeniorityLevel`, `RoleCategory`, `TaxonomyCategory`, `MatchStatus`, `CloudTransferabilityStatus`, `RiskSeverity`, `RiskType`, `DecisionRecommendation`).
- [`careerpilot/core/config.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/core/config.py) — Configurable scoring weights, penalty deductions, and decision thresholds.

### 🔍 Parsers & Analysis Services
- [`careerpilot/parsers/jd_parser.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/parsers/jd_parser.py) — Multi-format parser (Plain text, TXT, PDF via PyMuPDF) with taxonomy mapping and section segmentation.
- [`careerpilot/analysis/role_classifier.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/analysis/role_classifier.py) — `RoleClassifier`, `RoleRealityAnalyzer` (day-to-day work split %), and `SeniorityDetector`.
- [`careerpilot/analysis/evidence_matcher.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/analysis/evidence_matcher.py) — Candidate RAG grounding, experience gap calculation, cloud transferability reasoning, and preference checks.
- [`careerpilot/analysis/fit_scorer.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/analysis/fit_scorer.py) — Explainable 7-factor weighted scoring model with must-have gap penalty deductions.
- [`careerpilot/analysis/risk_analyzer.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/analysis/risk_analyzer.py) — Risk factor analysis with severity levels and mitigation strategies.
- [`careerpilot/analysis/decision_engine.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/analysis/decision_engine.py) — Deterministic recommendation engine (`APPLY`, `REVIEW`, `SKIP`) with rich explainable breakdowns.
- [`careerpilot/analysis/analyze_job.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/analysis/analyze_job.py) — CLI analysis runner script.

### 🌐 LangGraph Workflow
- [`careerpilot/graphs/state.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/graphs/state.py) — `JobAnalysisState` TypedDict.
- [`careerpilot/graphs/job_analysis_graph.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/graphs/job_analysis_graph.py) — Compiled stateful LangGraph workflow orchestrating 7 sequential nodes.

### 🧪 Evaluation Dataset & Test Suite
- `data/jobs/evaluation/` — 10 realistic evaluation job descriptions covering all target roles, seniority variations, and cloud scenarios:
  1. `01_ai_data_engineer.txt` (AI Data Engineer with GCP, BigQuery, Airflow, RAG, LLMs ➔ `APPLY`)
  2. `02_data_engineer_gcp.txt` (GCP Data Engineer with BigQuery, Airflow, SQL ➔ `APPLY`)
  3. `03_genai_rag_engineer.txt` (GenAI / RAG Engineer with FAISS, Gemini, LangChain ➔ `APPLY`)
  4. `04_gcp_cloud_data_engineer.txt` (GCP Cloud Data Engineer in Nagpur ➔ `APPLY`)
  5. `05_aws_data_engineer_transferable.txt` (AWS Data Engineer with transferable GCP background ➔ `APPLY`)
  6. `06_aws_heavy_glue_redshift_gap.txt` (Senior AWS Big Data Engineer mandating Glue/EMR/Redshift ➔ `SKIP`)
  7. `07_pure_ml_research_scientist.txt` (AI Research Scientist in Deep Learning Theory ➔ `SKIP`)
  8. `08_staff_lead_10yr_seniority_gap.txt` (Staff Data Architect with 8-10+ yrs leadership ➔ `SKIP`)
  9. `09_weakly_related_bi_analytics.txt` (Lead BI Dashboard & Tableau Developer ➔ `SKIP`)
  10. `10_product_company_ai_data_engineer.txt` (Product Company Data & AI Platform Engineer in Pune ➔ `APPLY`)
- `tests/test_jd_parser.py`
- `tests/test_role_classifier.py`
- `tests/test_fit_scorer.py`
- `tests/test_risk_analyzer.py`
- `tests/test_decision_engine.py`
- `tests/test_job_analysis_graph.py`

---

## 3. Scoring Formula & Decision Thresholds

### Weighted Fit Scoring Model
$$\text{Raw Score} = \sum_{i=1}^{7} (W_i \times S_i)$$

| Component ($S_i$) | Default Weight ($W_i$) | Evaluation Basis |
| :--- | :--- | :--- |
| **Must-Have Skills** | 35% | Exact candidate RAG evidence match for core requirements |
| **Relevant Experience** | 20% | Candidate verified tenure (1.9+ yrs) vs. JD explicit required years |
| **Role Alignment** | 15% | Primary classified role match against target priority hierarchy |
| **GenAI Alignment** | 10% | Presence and depth of RAG, LLM, Agentic, and Gemini capabilities |
| **Data Engineering Alignment** | 10% | Presence of Python, SQL, BigQuery, Airflow, and Data Quality |
| **Cloud Alignment** | 5% | Direct GCP match (100%), Transferable AWS (75%), Unmet cloud gap (20%) |
| **Candidate Preferences** | 5% | Location (Pune/Nagpur/Remote), career direction, company type |

### Must-Have Penalty Deduction
$$\text{Final Fit Score} = \max(0.0, \min(100.0, \text{Raw Score} - (N_{\text{missing\_must\_have}} \times 12.0)))$$

### Decision Thresholds
- **`APPLY`**: $\text{Fit Score} \ge 75.0$, No `CRITICAL` or `HIGH` risks, $\le 1$ must-have gap.
- **`REVIEW`**: $55.0 \le \text{Fit Score} < 75.0$, OR Transferable cloud gap (e.g. GCP ➔ AWS), OR Moderate experience tenure shortfall.
- **`SKIP`**: $\text{Fit Score} < 55.0$, OR Any `CRITICAL` risk, OR $\ge 3$ must-have gaps, OR Severe role mismatch (e.g., academic ML research / hardware).

---

## 4. Sample CLI Execution Results

### Sample 1: Target Match (01_ai_data_engineer.txt)
```
============================================================
CAREERPILOT JOB ANALYSIS
============================================================
Company:        CognitiveScale Labs
Job Title:      AI Data Engineer

ROLE CLASSIFICATION:
  Primary:      AI_DATA_ENGINEER
  Secondary:    DATA_ENGINEER
  Seniority:    JUNIOR (Standard yrs required)

ROLE REALITY (Day-to-day Work Split):
  Data Engineering: 46.7%, GenAI / RAG / Agents: 20.0%, Cloud & Backend Infrastructure: 33.3%
  Primary Type: Data Engineering

FIT SCORE:       100.0 / 100
RECOMMENDATION:  [APPLY]

MUST-HAVE REQUIREMENTS:
  [+] Python
  [+] SQL
  [+] BigQuery
  [+] Google Cloud Platform (GCP)
  [+] Google Cloud Storage (GCS)
  [+] Apache Airflow
  [+] RAG (Retrieval-Augmented Generation)
  [+] LLM Orchestration
  [+] Data Quality Frameworks
  [+] Data Validation

CLOUD TRANSFERABILITY:
  * Status: MATCH
  * Details: Direct verified production match. Candidate has deep production experience across BigQuery, Airflow, Vertex AI, and GCP Cloud Storage.
============================================================
```

### Sample 2: Transferable AWS (05_aws_data_engineer_transferable.txt)
```
============================================================
Company:        Nexus Infotech
Job Title:      Data Engineer (Python / SQL / Airflow)
FIT SCORE:       98.8 / 100
RECOMMENDATION:  [APPLY]
CLOUD TRANSFERABILITY:
  * Status: TRANSFERABLE
  * Details: GCP is verified in production. AWS data architecture patterns (Redshift, Glue, S3) are transferable from BigQuery and GCS.
RISK ASSESSMENT:
  * [LOW] Role requests AWS experience; candidate's primary production cloud is GCP (transferable data pipeline concepts).
============================================================
```

### Sample 3: Significant AWS Gap (06_aws_heavy_glue_redshift_gap.txt)
```
============================================================
Company:        CloudPioneer Global
Job Title:      Senior AWS Big Data Engineer
FIT SCORE:       0.0 / 100
RECOMMENDATION:  [SKIP]
KEY FACTOR: Rejected due to critical risk: Multiple critical must-have requirements missing (4 unevidenced skills: Amazon Redshift, AWS Glue, AWS EMR, Apache Spark).
CLOUD TRANSFERABILITY:
  * Status: SIGNIFICANT_GAP
  * Details: JD heavily mandates deep AWS-specific proprietary services (Glue/EMR/Redshift) and AWS certifications, which are unevidenced in candidate production history.
============================================================
```

---

## 5. Test Suite Verification

All **41 automated unit and integration tests** pass with 100% success rate:
```bash
pytest -v tests/
======================== 41 passed, 1 warning in 2.40s ========================
```

---

## 6. Known Limitations
- **External Network Dependency:** In offline / unit test environments, the system runs with deterministic vector embedding and mock LLM reasoning, ensuring test stability without external API latency.
- **Strict Read-Only Enforcement:** All candidate data files under `data/candidate/` remain strictly unmodified.

---

## 7. Exact Next Recommended Milestone

**Milestone 4 — Resume Tailoring Engine**
- Implement resume tailoring strategies based on classified role (`AI_DATA_ENGINEER`, `DATA_ENGINEER`, `GENAI_ENGINEER`, `GCP_DATA_ENGINEER`).
- Build verified bullet point selection from candidate evidence chunks.
- Implement strict anti-hallucination truth guards ensuring 100% factual fidelity to `data/candidate/` files.
- Export tailored resumes in structured Markdown and clean DOCX formats.
