# CareerPilot AI — Candidate Data Validation Report

**Candidate Name:** Trupti Kularkar  
**Date of Validation:** 2026-08-29  
**Source Directory:** `data/candidate/`  
**Validation Status:** **PASSED WITH VERIFIED CONSTRAINTS & FLAGGED NUANCES**

---

## 1. Executive Summary

This validation report performs an exhaustive cross-source verification of the candidate's source-of-truth files:
1. `master_resume.pdf` (Primary Source of Truth)
2. `profile.yaml`
3. `experience.md`
4. `projects.md`
5. `skills.md`
6. `achievements.md`
7. `preferences.yaml`
8. `evidence.json`

All files have been verified under the strict rule: **Zero modification, zero embellishment, zero hallucination**.

---

## 2. Candidate Identity & Profile Verification

| Field | Source: `master_resume.pdf` | Source: `profile.yaml` | Status | Notes |
|---|---|---|---|---|
| **Full Name** | Trupti Kularkar | Trupti Kularkar | Verified | Consistent across all documents. |
| **Email** | `kularkartrupti@gmail.com` | `kularkartrupti@gmail.com` | Verified | Matched. |
| **Phone** | `+91 9834055766` | — | Verified | Present in master resume. |
| **Current Location** | Pune, Maharashtra | Pune, Maharashtra, India | Verified | Matched. |
| **LinkedIn** | `linkedin.com/in/trupti-kularkar-579062210` | — | Verified | Present in master resume. |
| **GitHub** | `github.com/Truptikularkar` | — | Verified | Present in master resume. |
| **Current Experience** | `1.8+ years` | `1.9+ years` (current) / `1.8+` (resume snapshot) | **Flagged Nuance** | `profile.yaml` explicitly notes that current live experience is 1.9+, while the uploaded resume snapshot states 1.8+. Use 1.9+ for profile reasoning and preserve 1.8+ when quoting the resume. |
| **Current Role** | Programmer Analyst | Programmer Analyst | Verified | Cognizant Technology Solutions. |

---

## 3. Professional Experience Verification

### Current Role: Programmer Analyst — Cognizant Technology Solutions
- **Duration:** 11/2025 – Present | Location: Pune, India
- **Verified Production Accomplishments:**
  1. **LLM-Powered Ticket Resolution Agent:** Architected on Vertex AI using Gemini 2.5 Pro. Automated ~60% of repetitive support tickets; reduced mean resolution time from 4 hours to under 30 minutes.
  2. **Data Validation Frameworks:** Built SQL-based frameworks across 15+ ETL pipelines (row-count reconciliation, null checks, duplicate detection, schema consistency); reduced data quality incidents by ~35%.
  3. **BigQuery Optimization:** Partitioning & clustering resulting in ~25% query cost savings.
  4. **Airflow Automation:** Automated 20+ Airflow DAGs; cut manual operational overhead by ~40% and pipeline failure response time by ~50%.
  5. **Real-time Event-Driven ETL:** Cloud Storage → Pub/Sub → Cloud Functions → BigQuery processing 500K+ daily events with sub-2-minute latency.
  6. **Enterprise AI Monitoring:** Collaborated across teams to integrate AI monitoring into workflow systems.
  7. **Mentorship:** Mentored junior engineers on GCP and Airflow pipeline development.

### Previous Role: Programmer Analyst Trainee — Cognizant Technology Solutions
- **Duration:** 11/2024 – 11/2025 | Location: Chennai, India
- **Verified Experience:** Hands-on development in GCP, Python, SQL, and ETL. Built a retail data pipeline for sales trend analysis and forecasting.

---

## 4. Education, Certifications & Publications Verification

### Education
- **Degree:** B.Tech in Artificial Intelligence
- **Institution:** G. H. Raisoni College of Engineering, Nagpur
- **Years:** 2020 – 2024 (Graduated 2024)
- **Academic Score:** CGPA 8.83 (Verified across `master_resume.pdf` and `profile.yaml`)

### Certifications
1. Google Cloud Certified: Associate Data Practitioner
2. Discover Data Analysis Badge by Microsoft

### Publications
- **Title:** *"Intelligent Diabetes Predicting Model for Diverse Ethnicities"*
- **Publisher:** Springer Nature Singapore

---

## 5. Technical Skills Classification & Truth Matrix

In accordance with the CareerPilot AI Truth Guard, candidate skills are categorized into strict evidence classes:

| Skill / Technology | Evidence Source | Evidence Category | Allowed on Resume? | Allowed in Personalized STAR Answers? |
|---|---|---|---|---|
| **Python** | Resume, `experience.md`, `skills.md` | `SUPPORTED` (Production) | ✅ Yes | ✅ Yes (Grounded) |
| **SQL (DDL, DML, CTEs, Tuning)** | Resume, `experience.md`, `skills.md` | `SUPPORTED` (Production) | ✅ Yes | ✅ Yes (Grounded) |
| **Google Cloud Platform (GCP)** | Resume, `experience.md`, `skills.md` | `SUPPORTED` (Production) | ✅ Yes | ✅ Yes (Grounded) |
| **BigQuery & BigQuery ML** | Resume, `experience.md`, `projects.md` | `SUPPORTED` (Production) | ✅ Yes | ✅ Yes (Grounded) |
| **Apache Airflow** | Resume, `experience.md`, `projects.md` | `SUPPORTED` (Production) | ✅ Yes | ✅ Yes (Grounded) |
| **Data Quality Engineering** | Resume, `experience.md`, `projects.md` | `SUPPORTED` (Production) | ✅ Yes | ✅ Yes (Grounded) |
| **Vertex AI & Gemini API (2.5 Pro)** | Resume, `experience.md`, `projects.md` | `SUPPORTED` (Production) | ✅ Yes | ✅ Yes (Grounded) |
| **Cloud Storage, Pub/Sub, Functions, Run** | Resume, `experience.md`, `projects.md` | `SUPPORTED` (Production) | ✅ Yes | ✅ Yes (Grounded) |
| **RAG & Hybrid Retrieval (FAISS+BM25+RRF)** | `projects.md`, `evidence.json` | `SUPPORTED` (Personal Project) | ✅ Yes (As Project) | ✅ Yes (As Personal Project) |
| **LangChain / LangGraph** | `skills.md`, `evidence.json` | `SUPPORTED` (Personal Project) | ✅ Yes (As Project) | ✅ Yes (As Personal Project) |
| **AWS (Redshift, Glue, Lambda)** | Resume ("transferable"), `skills.md` | `PARTIALLY_SUPPORTED` (Transferable) | ⚠️ Flag as Transferable only | ❌ No production claim |
| **Apache Spark** | `skills.md`, `evidence.json` | `NOT_SUPPORTED` (Production) | ❌ Block from Production Claims | ❌ No production claim |
| **Kubernetes** | `skills.md`, `evidence.json` | `NOT_SUPPORTED` (Production) | ❌ Block from Production Claims | ❌ No production claim |

---

## 6. Projects Verification

1. **AI-Driven Data Quality Monitoring & Anomaly Detection**
   - **Stack:** BigQuery ML, SQL, Gemini 2.5 Pro, Vertex AI
   - **Verified Metrics:** ~92% detection accuracy, <5% false positive rate (6-month backtesting), investigation time reduced from ~45m to <5m.
2. **Local RAG & Hybrid Retrieval Sandbox**
   - **Stack:** Python, FAISS, BM25, Reciprocal Rank Fusion, Gemini API, Ollama
   - **Verified Fact:** Local playground with dense/sparse RRF ranking, visual pipeline tracing, and provider-agnostic LLM orchestration.
   - **Constraint:** Strictly personal project; never represent as client production experience.
3. **AI AutoHeal Agent — Automated Job Failure Remediation**
   - **Stack:** GCP Cloud Run, BigQuery, Airflow, Gemini 2.5 Pro, Python, SQL
   - **Verified Metrics:** Autonomously resolved ~75% of transient Airflow failures, cut on-call response time by ~60%, 100% job-level NDJSON audit logs in BigQuery, integrity guardrails.
4. **Automated Sales Data Validation DAG**
   - **Stack:** Apache Airflow, BigQuery, SQL, Python, Power Automate
   - **Verified Metrics:** ~70% reduction in manual effort, discrepancies flagged within minutes, `dag_run.conf` dynamic configuration reducing setup from days to <30m, MS Teams automated alerts.

---

## 7. Verified Metrics Catalog (Zero Invention Rule)

The following metrics are strictly verified and available for resume bullet points and STAR answers:
- `~60%` automated support ticket resolution
- `4 hours → under 30 minutes` mean ticket resolution time
- `~35%` reduction in data quality incidents
- `~25%` BigQuery query cost reduction via partitioning/clustering
- `20+` Airflow DAGs automated
- `~40%` reduction in manual operational overhead
- `~50%` reduction in pipeline failure response time
- `500K+` daily events processed with sub-2-minute latency
- `~92%` anomaly detection accuracy (<5% false positive rate across 6 months)
- `~45 minutes → under 5 minutes` mean anomaly investigation time
- `~75%` transient Airflow failures resolved automatically by AI AutoHeal
- `~60%` reduction in on-call response time
- `100%` job-level audit traceability across remediation events
- `~70%` reduction in manual sales validation effort
- `Days → under 30 minutes` validation workflow onboarding time

---

## 8. Career Preferences & Strategic Positioning

- **Core Career Goal:** Growth at the intersection of AI/GenAI and Data Engineering.
- **Target Role Hierarchy:**
  1. **AI Data Engineer** (Top Priority)
  2. **Data Engineer**
  3. **GenAI Engineer**
  4. **AI Engineer**
  5. **GCP Data Engineer**
  6. **Cloud Data Engineer**
- **Location Preference:**
  - Primary: **Pune**, **Nagpur**
  - Secondary: Remote
  - Other locations: Low priority
- **Company Preferences:**
  - 1st Preference: **Service-based companies**
  - 2nd Preference: **Product-based companies** (wants to explore both, starting with service-based).
- **Compensation Target:**
  - Current CTC: `4.5 LPA`
  - Target CTC: `9 – 10 LPA`
  - Note: Growth, technical ownership, and role alignment are paramount; compensation is not the sole filter.
- **Target Experience Range:** 1 – 4 years experience roles.

---

## 9. Potential Conflicts, Nuances & Guardrail Decisions

1. **Experience Snapshot vs Live Experience:**
   - `master_resume.pdf` states `1.8+ years`, while `profile.yaml` and `preferences.yaml` indicate `1.9+ years`.
   - **Resolution Policy:** When generating profile-level match summaries and role-fit evaluations, use `1.9+ years`. When quoting the exact master resume text, preserve `1.8+ years`.
2. **GCP vs. AWS Cloud Alignment:**
   - Candidate has deep, verified production GCP experience (BigQuery, Airflow/Composer, Pub/Sub, Functions, Cloud Run, Vertex AI).
   - Candidate does **not** have production AWS experience, though concepts (Redshift, Glue, Lambda) are transferable.
   - **Resolution Policy:** The Job Analysis Engine must not auto-reject an AWS JD if the core data engineering / Python / SQL responsibilities strongly match. It will classify AWS as a transferable skill or gap, and provide an explainable recommendation.
3. **Personal Projects vs. Production Experience:**
   - The Local RAG Sandbox (FAISS + BM25 + RRF) and LangChain/LangGraph implementations are personal/open-source projects.
   - **Resolution Policy:** These must strictly be listed in the "Projects" section of tailored resumes and classified as personal project experience in interview answers. Never claim them as client production engagements.
4. **Spark & Kubernetes:**
   - Production experience with Spark or Kubernetes is unevidenced.
   - **Resolution Policy:** Any JD requirement for Spark or Kubernetes must be flagged as a `Skill Gap` or learning item, and never fabricated on generated resumes.

---

## 10. Recommendations for Human Review

1. **Profile Approval:** Confirm that 1.9+ years experience and the target CTC of 9–10 LPA in Pune/Nagpur are set as active evaluation parameters in the configuration.
2. **Resume Strategy Activation:** Set the default resume strategy to **AI Data Engineer** to maximize the candidate's unique dual strength in data pipelines and agentic LLM workflows.
3. **Guardrails Intact:** All candidate files in `data/candidate/` remain untouched and read-only.
