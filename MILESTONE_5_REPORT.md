# Milestone 5 Report — ATS Compatibility & Deep Resume Scoring Engine

**Project:** CareerPilot AI  
**Milestone:** 5 (ATS Compatibility & Deep Resume Scoring Engine)  
**Status:** Completed & Validated  
**Date:** 2026-08-30  

---

## 1. Architecture & Design Principles

Milestone 5 implements a deterministic, explainable **ATS Compatibility and Resume Optimization Engine** for CareerPilot AI. Grounded strictly in candidate ground truth (`data/candidate/`), the system evaluates tailored resumes against job requirements across 7 distinct evaluation dimensions without hallucinatory skill additions or keyword stuffing.

### Terminology Standard
As required, the engine strictly adopts transparent and realistic terminology:
- **"ATS-Style Compatibility Score"**
- **"ATS Compatibility Analysis"**
- **"Resume Optimization Analysis"**

It avoids any claim of reproducing or guaranteeing exact behavior on proprietary closed-source ATS platforms (e.g. Workday, Taleo, Greenhouse).

```
==================================================================================================
                             CAREERPILOT ATS COMPATIBILITY ENGINE
==================================================================================================

  [JobDescription] + [JobAnalysisResult] + [TailoredResume] + [Candidate Evidence]
                               │
                               ▼
  ┌─────────────────────────────────────────────────────────────┐
  │                 RequirementMatrixGenerator                  │ ──▶ Builds Requirement Matrix
  │                                                             │     (JD vs Resume vs Truth)
  └──────────────┬──────────────────────────────────────────────┘
                 │
                 ▼
  ┌─────────────────────────────────────────────────────────────┐
  │                   Multi-Tier Evaluators                     │
  │  1. Keyword & Requirement Coverage (25%)                    │ ──▶ Exact / Synonym / Semantic
  │  2. Skill Taxonomy Alignment (20%)                          │ ──▶ Domain & Category Depth
  │  3. Semantic Role Alignment (15%)                           │ ──▶ Responsibilities vs Dist.
  │  4. Experience & Seniority Alignment (15%)                  │ ──▶ 1.9+ yrs vs JD Tenure
  │  5. Resume Structure & Completeness (10%)                   │ ──▶ 6 Standard ATS Sections
  │  6. Formatting & Layout Compatibility (10%)                 │ ──▶ DOCX & Code Rule Checks
  │  7. Readability & Keyword Density (5%)                      │ ──▶ Natural Flow & No Stuffing
  └──────────────┬──────────────────────────────────────────────┘
                 │
                 ▼
  ┌─────────────────────────────────────────────────────────────┐
  │              Truth Guard Integration & Penalty              │ ──▶ Blocks / Penalizes claims
  └──────────────┬──────────────────────────────────────────────┘     if ungrounded metrics/tech
                 │
                 ▼
  ┌─────────────────────────────────────────────────────────────┐
  │             Optimization Suggestions & Seed Engine          │
  │  • Actionable, truth-grounded suggestions                   │
  │  • InterviewReadinessSeed contract for Milestone 6          │
  └──────────────┬──────────────────────────────────────────────┘
                 │
                 ▼
  ┌─────────────────────────────────────────────────────────────┐
  │                    ATS Report Generation                    │ ──▶ ats_report.json
  └─────────────────────────────────────────────────────────────┘     ats_report.md
```

---

## 2. Configurable Scoring Formula

The overall ATS-style compatibility score is calculated deterministically through configurable weights in [`careerpilot/core/config.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/core/config.py):

$$\text{Overall ATS Score} = \sum_{i=1}^{7} (\text{Score}_i \times \text{Weight}_i) - \text{TruthPenalty}$$

| Component | Weight | Max Pts | Evaluator Focus |
| :--- | :---: | :---: | :--- |
| **Keyword & Requirement Coverage** | **25%** | 100 | Must-Have (75% sub-weight) & Nice-to-Have (25% sub-weight) matching tiers. |
| **Skill Taxonomy Alignment** | **20%** | 100 | Categorical technical coverage across Programming, Cloud, Data, and GenAI. |
| **Semantic Role Alignment** | **15%** | 100 | Role positioning mapped against JD work distribution percentages. |
| **Experience & Seniority Alignment**| **15%** | 100 | Candidate verified tenure (1.9+ yrs) evaluated against JD seniority level. |
| **Resume Structure & Completeness** | **10%** | 100 | Detection of Contact, Summary, Skills, Experience, Projects, Education. |
| **Formatting Compatibility** | **10%** | 100 | DOCX layout inspection (no tables, standard fonts, linear single column). |
| **Readability & Keyword Density** | **5%** | 100 | Word count conciseness and keyword stuffing detection. |
| **Total** | **100%** | **100** | **Deterministic Sum (0.0 to 100.0)** |

### Score Interpretation Scale
- **90–100:** Excellent ATS-Style Alignment
- **80–89:** Strong Alignment
- **70–79:** Good but Improvable
- **60–69:** Moderate Alignment
- **Below 60:** Weak Alignment

---

## 3. Keyword Taxonomy & Multi-Tier Matching

Implemented in [`careerpilot/ats/keyword_matcher.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/ats/keyword_matcher.py), matching operates across 3 granular tiers:

1. **`EXACT_MATCH` (100% credit):** Direct literal match in text (e.g. `Python` $\rightarrow$ `Python`, `BigQuery` $\rightarrow$ `BigQuery`).
2. **`SYNONYM_MATCH` (80% credit):** Controlled canonical synonym normalization:
   - `Generative AI` $\leftrightarrow$ `GenAI`
   - `Large Language Models` $\leftrightarrow$ `LLM`
   - `Google Cloud Platform` $\leftrightarrow$ `GCP`
   - `Apache Airflow` $\leftrightarrow$ `Airflow`
   - `Google Cloud Storage` $\leftrightarrow$ `GCS`
3. **`SEMANTIC_MATCH` (60% credit):** Conceptual alignment for generic technology categories:
   - `Cloud Data Warehouse` $\leftrightarrow$ `BigQuery`
   - `Vector Database` $\leftrightarrow$ `FAISS`
   - `Cloud Storage` $\leftrightarrow$ `GCS`
   - *Vendor Guardrail:* Proprietary vendor tools (e.g. `AWS Redshift`, `Snowflake`, `AWS Glue`) are never substituted as generic semantic matches for GCP tools, preventing false claim inflation.
4. **`GAP` (0% credit):** Skill is missing in the resume text.

---

## 4. DOCX & Layout Inspection

Implemented in [`careerpilot/ats/docx_inspector.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/ats/docx_inspector.py) and [`careerpilot/ats/formatting_rules.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/ats/formatting_rules.py):
- **Layout Tables:** Detects whether multi-cell tables exist in the document flow.
- **Header / Footer Traps:** Inspects `section.header` and `section.footer` to ensure contact info and skills are placed in the main body.
- **Typography Consistency:** Enforces standard ATS fonts (`Calibri`, `Arial`, `Times New Roman`).
- **Margins & Spacing:** Ensures margins $\ge 0.5\text{ in}$ to prevent physical rendering clipping.
- **Special Character Guard:** Flags non-standard bullets and excessive emoji symbols.

---

## 5. Candidate Truth Rule & Truth Guard Integration

The ATS engine strictly adheres to the candidate ground truth rules:
1. **Never Recommends Adding Unverified Skills:**
   - If a JD requires **AWS** or **Kubernetes** and the candidate has no verified production record, the recommendation says:  
     `"Do NOT add 'AWS' to your resume. If this is a cloud technology, emphasize strong production GCP experience with transferable data architecture patterns."`
2. **Truth Guard Block Penalty:**
   - If a candidate resume contains `BLOCK` level violations (e.g. inflated `40%` metric or fabricated AWS production claims), the ATS engine docks **35 points** from the overall score and issues a `CRITICAL` priority safety suggestion.

---

## 6. Interview Readiness Seed (Milestone 6 Contract)

Implemented in [`careerpilot/interview/readiness.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/interview/readiness.py), the engine outputs a structured `InterviewReadinessSeed` model bridging the tailored resume with the target JD to prepare for Milestone 6:
- **High-Priority Technical Topics:** Overlapping core technologies (Python, SQL, BigQuery, GCP, Airflow, RAG).
- **Candidate Strengths:** Verified achievements and pipeline implementations.
- **Candidate Gaps / Pivot Points:** Identified JD gaps to navigate during interviews.
- **Likely Deep-Dive Topics:** BigQuery partition/clustering mechanics, Airflow failure recovery, RRF ranking.
- **Likely Challenged Claims:** Specific metrics requiring evidence explanation (e.g. ~25% BigQuery cost savings, ~75% Airflow auto-heal).
- **Scenario & System Design Topics:** Real-time ingestion architecture, data quality drift mitigation.

---

## 7. Sample Generated ATS Report (`01_ai_data_engineer.txt`)

```markdown
# ATS Compatibility & Resume Optimization Report
**Resume ID:** `resume_4ac188e7` | **Job:** `AI Data Engineer` (CognitiveScale Labs)
**Target Strategy:** `AI_DATA_ENGINEER` | **Truth Status:** `PASS`

## 1. ATS-Style Compatibility Score
### **Overall Score: 96.7 / 100** (Excellent ATS-Style Alignment)

| Component | Score | Weight | Weighted Score | Details |
| :--- | :--- | :--- | :--- | :--- |
| **Keyword & Requirement Coverage** | 93.0/100 | 25% | 23.25 | Must-Have match: 10/10, Nice-to-Have match: 5/5. |
| **Skill Taxonomy Alignment** | 96.0/100 | 20% | 19.2 | Evaluated skill depth across 5 technical categories. |
| **Semantic Role Alignment** | 95.0/100 | 15% | 14.25 | Resume maps closely to primary JD work distribution. |
| **Experience & Seniority Alignment** | 100.0/100 | 15% | 15.0 | Candidate tenure (1.9+ yrs) evaluated against JUNIOR. |
| **Resume Structure & Completeness** | 100.0/100 | 10% | 10.0 | Detected 6 of 6 standard ATS sections. |
| **Formatting & Layout Compatibility** | 100.0/100 | 10% | 10.0 | Single-column linear layout verified. No tables. |
| **Readability & Keyword Density** | 100.0/100 | 5% | 5.0 | Natural professional language verified. |

## 2. Requirement Coverage Summary
- **Must-Have Coverage:** `10/10`
- **Nice-To-Have Coverage:** `5/5`
```

---

## 8. Automated Test Suite Results

All **72 automated tests** across all 5 milestones pass with 100% success rate:
```bash
pytest -v tests/
======================== 72 passed, 1 warning in 5.23s ========================
```

### Key Negative & Boundary Tests Verified
1. **AWS Gap Truthfulness:** `test_ats_truth_integration_aws_gap_truthful` verifies that missing AWS/Redshift requirements are flagged as gaps without recommending ungrounded skill additions.
2. **Blocked Claim Penalty:** `test_ats_truth_integration_blocked_claim_penalized` verifies that hallucinated metrics or technologies incur score penalties and critical safety recommendations.
3. **Table & Header Traps:** `test_docx_inspector_table_trap_detection` and `test_docx_inspector_header_trap_detection` verify that layout tables and hidden header text are flagged.
4. **Keyword Stuffing Detection:** `test_keyword_density_and_stuffing` verifies that unnatural term repetition is flagged as `POTENTIAL_STUFFING`.

---

## 9. Known ATS Compatibility Caveats
- **Proprietary Heuristic Variance:** Real-world ATS systems (Workday, iCIMS, Taleo) employ disparate third-party parsing libraries (Sovren/Textkernel) with varying OCR capabilities. The CareerPilot ATS engine simulates linear text extraction and standard semantic alignment heuristics.
- **Single-Page Target:** Length scoring assumes a standard 1-page format for candidates with $< 5$ years of experience.

---

## 10. Recommended Next Milestone

**Milestone 6 — Interview Preparation & Question Engine**
- Consume the `InterviewReadinessSeed` contract generated in Milestone 5.
- Generate role-specific technical deep-dive questions, behavioral STAR questions, and system design scenarios.
- Build evidence-grounded answer templates mapped to candidate experience.
