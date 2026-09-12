# Milestone 4 Report — Resume Tailoring Engine & Truth Guard

**Project:** CareerPilot AI  
**Milestone:** 4 (Resume Tailoring Engine & Truth Guard)  
**Status:** Completed & Validated  
**Date:** 2026-08-30  

---

## 1. Architecture Implemented

Milestone 4 delivers the evidence-grounded, zero-hallucination **Resume Tailoring Engine** for CareerPilot AI. Grounded strictly in verified candidate data (`data/candidate/`), the system dynamically reorders, emphasizes, and tailors candidate evidence for target job descriptions while enforcing deterministic Truth Guard rules that prevent metric inflation, unverified cloud claims (e.g. AWS production), and project mischaracterization.

```
==================================================================================================
                                CAREERPILOT RESUME TAILORING PIPELINE
==================================================================================================

  [Structured JobAnalysisResult] (from Milestone 3)
                 │
                 ▼
  ┌───────────────────────────────┐
  │       StrategySelector        │ ──▶ Selects AI_DATA_ENGINEER / DATA_ENGINEER / 
  └──────────────┬────────────────┘     GENAI_ENGINEER / GCP_DATA_ENGINEER or User Override
                 │
                 ▼
  ┌───────────────────────────────┐
  │        BulletSelector         │ ──▶ Assembles verified experience & projects from RAG,
  └──────────────┬────────────────┘     prioritizes skills, and maintains metric immutability
                 │
                 ▼
  ┌───────────────────────────────┐
  │      Draft TailoredResume     │ ──▶ Assembles structured Header, Summary, Skills,
  └──────────────┬────────────────┘     Experience, Projects, Education, & Certifications
                 │
                 ▼
  ┌───────────────────────────────┐
  │    Truth Guard & Auditor      │ ──▶ Deterministic checks:
  │                               │     1. Immutable Metrics (25%, 35%, 60%, 75%, 500k+)
  │                               │     2. Prohibited Technologies (AWS / K8s in production)
  │                               │     3. Experience-Type Isolation (Personal != Professional)
  └──────────────┬────────────────┘
                 │
        ┌────────┴────────┐
     PASS / FLAG        BLOCK ──▶ Halts generation & outputs truth_report.md
        │
        ▼
  ┌───────────────────────────────┐
  │      ATS Compliance QA        │ ──▶ Validates required sections, length (1 page),
  └──────────────┬────────────────┘     and keyword alignment %
                 │
                 ▼
  ┌───────────────────────────────┐
  │   Document Exporters & Audit  │ ──▶ Generates:
  └───────────────────────────────┘     • resume.md (Standard ATS Markdown)
                                        • resume.docx (Clean single-column DOCX)
                                        • resume_audit.json (Traceable evidence metadata)
                                        • truth_report.md (Audit log of all claims)
                                        • strategy.json (Target strategy config)
```

---

## 2. Files Created & Modified

### 📦 Resume Models & Configuration
- [`careerpilot/models/resume.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/models/resume.py) — Pydantic schemas for `ResumeHeader`, `ResumeSummary`, `ResumeSkillCategory`, `ResumeBullet`, `ResumeExperienceEntry`, `ResumeProjectEntry`, `ResumeEducationEntry`, `ResumeCertificationEntry`, `ResumeStrategy`, `TailoredResume`, `ATSPrecheckResult`, and `TruthValidationReport`.
- [`careerpilot/core/constants.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/core/constants.py) — Enums for `ResumeStrategyType`, `TruthValidationStatus`, `ClaimType`, and `ExperienceType`.
- [`careerpilot/core/config.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/core/config.py) — Configured `OUTPUT_RESUMES_DIR` (`data/generated/resumes/`).

### 🎯 Strategy Engine & Selection
- [`careerpilot/generators/strategy_engine.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/generators/strategy_engine.py) — Defines the 4 concrete strategy profiles (`AI_DATA_ENGINEER`, `DATA_ENGINEER`, `GENAI_ENGINEER`, `GCP_DATA_ENGINEER`) with specific keyword emphases, project ordering, and summary templates.
- [`careerpilot/generators/strategy_selector.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/generators/strategy_selector.py) — Automated routing from `JobAnalysisResult` with full support for manual user overrides (`AUTO`, `AI_DATA_ENGINEER`, `DATA_ENGINEER`, `GENAI_ENGINEER`, `GCP_DATA_ENGINEER`).

### 🛡️ Truth Guard & Anti-Hallucination Pipeline
- [`careerpilot/truth_guard/classifier.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/truth_guard/classifier.py) — Extracts atomic claims (`METRIC`, `TECHNOLOGY`, `EXPERIENCE_TYPE`, `TENURE`).
- [`careerpilot/truth_guard/auditor.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/truth_guard/auditor.py) — Deterministic auditor verifying immutable metrics against candidate ground truth and blocking unevidenced production claims (AWS, Spark, Kubernetes).
- [`careerpilot/truth_guard/sanitizer.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/truth_guard/sanitizer.py) — Corrects ungrounded phrasing in draft text.
- [`careerpilot/truth_guard/validator.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/truth_guard/validator.py) — Orchestrates resume-wide truth validation audits.

### 📄 Exporters, Evaluators & LangGraph Pipeline
- [`careerpilot/generators/bullet_selector.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/generators/bullet_selector.py) — Assembles verified experience bullets, projects, and skills.
- [`careerpilot/generators/resume_markdown.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/generators/resume_markdown.py) — Formats `TailoredResume` into clean ATS-parseable Markdown.
- [`careerpilot/generators/resume_docx.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/generators/resume_docx.py) — Generates ATS-compliant `.docx` with standard fonts (Calibri), single-column hierarchy, and 0.6in margins.
- [`careerpilot/ats/evaluator.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/ats/evaluator.py) — ATS compliance precheck interface.
- [`careerpilot/graphs/resume_graph.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/graphs/resume_graph.py) — LangGraph state graph orchestrating resume drafting, validation, and artifact export.
- [`careerpilot/generators/generate_resume.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/generators/generate_resume.py) — CLI generation runner.

---

## 3. Truth Guard Rules & Protection Matrix

| Category | Policy / Verified Value | Violation Trigger | Action |
| :--- | :--- | :--- | :--- |
| **Metrics** | Exact verified values: `25%`, `35%`, `60%`, `75%`, `500k+`, `10k+`, `1.9+ yrs` | Inflating metrics (e.g. `25%` ➔ `40%`) or ungrounded percentages | **BLOCK** |
| **Cloud** | GCP production verified (`BigQuery`, `Airflow`, `GCS`, `Pub/Sub`, `Cloud Functions`, `Vertex AI`) | Claiming AWS production experience (AWS is transferable only) | **BLOCK** |
| **Infrastructure** | Serverless / Cloud Composer / Docker (basic) | Claiming Kubernetes cluster administration or Spark production streaming | **BLOCK** |
| **Experience Type** | `Local RAG & Hybrid Retrieval` is a **Personal Project** | Moving Personal Project under Professional Experience (Cognizant) | **BLOCK** |
| **Tenure** | Candidate verified professional tenure: `1.9+ years` | Claiming `3+` or `4+` years of experience | **BLOCK** |

---

## 4. Sample CLI Execution Results

### Sample: AI Data Engineer Resume Generation (`01_ai_data_engineer.txt`)
```bash
python -m careerpilot.generators.generate_resume 01_ai_data_engineer.txt --strategy auto
```
```
============================================================
CAREERPILOT RESUME GENERATOR
============================================================
Job Description:   01_ai_data_engineer.txt
Strategy Option:   AUTO

------------------------------------------------------------
Selected Strategy: AI_DATA_ENGINEER
Target Role:       AI Data Engineer
Truth Status:      PASS
ATS Precheck:      100.0 / 100
------------------------------------------------------------

Generated Artifacts in Directory:
  data/generated/resumes/resume_38a02ea5
  - resume.md
  - resume.docx
  - resume_audit.json
  - truth_report.md
  - strategy.json

============================================================
RESUME GENERATION COMPLETED SUCCESSFULLY
============================================================
```

---

## 5. Negative Test Suite Results

Explicit negative tests verify that the Truth Guard actively blocks hallucinations:

1. **Inflated Metric Test (`25%` ➔ `40%`):**
   - Input: `"Optimized BigQuery query costs by 40% using advanced database tuning."`
   - Result: `[BLOCK] Unverified metric '40%' detected in text.`

2. **AWS Production Claim Test:**
   - Input: `"Served as Lead AWS Data Engineer in production managing AWS Glue pipelines."`
   - Result: `[BLOCK] AWS production experience is unverified. Candidate only has GCP production experience.`

3. **Kubernetes Cluster Administration Test:**
   - Input: `"Managed high-availability Kubernetes production cluster deploying real-time streaming pods."`
   - Result: `[BLOCK] Kubernetes cluster administration in production is unverified.`

4. **Experience Tenure Exaggeration Test:**
   - Input: `"Senior Data Engineer with 4+ years of professional experience."`
   - Result: `[BLOCK] Candidate total experience is 1.9+ years, cannot claim 3+ years.`

5. **Personal Project in Professional Experience Test:**
   - Input: `"Engineered Local RAG Sandbox using FAISS and BM25 for enterprise client production."`
   - Result: `[BLOCK] Personal projects must never be placed inside the Professional Work Experience section.`

---

## 6. Test Suite Verification

All **58 automated unit and integration tests** across all milestones pass with 100% success rate:
```bash
pytest -v tests/
======================== 58 passed, 1 warning in 3.77s ========================
```

---

## 7. Known Limitations
- **Format Form Factors:** Currently outputs ATS-optimized single-column Markdown and DOCX. PDF rendering from DOCX can be integrated in subsequent milestones via system print utilities or headless LibreOffice.
- **Strict Read-Only Source Files:** All candidate files under `data/candidate/` remain 100% untouched.

---

## 8. Exact Next Recommended Milestone

**Milestone 5 — ATS Compatibility & Deep Scoring Engine**
- Build comprehensive ATS keyword density and taxonomy scoring.
- Implement ATS layout simulation (detecting formatting risks, column traps, header/footer parsing errors).
- Generate ATS optimization suggestions for interview readiness.
- Prepare the foundation for Milestone 6 (Interview Prep Engine).
