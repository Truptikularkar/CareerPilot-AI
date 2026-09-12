# MILESTONE 6 — INTERVIEW PREPARATION & QUESTION ENGINE

**CareerPilot AI: Personal Job Intelligence, Resume Tailoring & Interview Preparation Agent**  
**Lead Architect & Senior AI Engineer**  
**Candidate:** Trupti Kularkar | **Verified Tenure:** 1.9+ Years (Cognizant) | **Cloud Stack:** Google Cloud Platform (GCP)

---

## 1. Executive Summary

Milestone 6 builds the evidence-grounded **Interview Preparation & Question Engine** for CareerPilot AI. This engine consumes the `InterviewReadinessSeed` generated in Milestone 5, candidate ground-truth evidence, and technical interview knowledge to produce an end-to-end, highly tailored interview preparation package.

Unlike generic question generators, every question, answer script, behavioral story, system design scenario, and follow-up chain is deterministically aligned with the target Job Description, the candidate's verified background at Cognizant, and identified skill transferability paths.

```
                    ┌───────────────────────────────────────────────┐
                    │    InterviewReadinessSeed (Milestone 5)       │
                    │   + TailoredResume + JobAnalysis + RAG Stores │
                    └───────────────────────┬───────────────────────┘
                                            │
                                            ▼
                    ┌───────────────────────────────────────────────┐
                    │           QuestionPlanner & Quotas            │
                    └───────────────────────┬───────────────────────┘
                                            │
        ┌───────────────────────────────────┼───────────────────────────────────┐
        ▼                                   ▼                                   ▼
┌───────────────────────┐       ┌───────────────────────┐       ┌───────────────────────┐
│ QuestionEngine        │       │ AnswerEngine          │       │ STAREngine            │
│ - HR Screening        │       │ - Short (30-45s)      │       │ - Situation, Task     │
│ - Resume Walkthrough  │       │ - Standard (60-90s)   │       │ - Action, Result      │
│ - Technical / GCP / BQ│       │ - Detailed (2-3 min)  │       │ - Insufficient Evid.  │
│ - Deep-Dives & Projs  │       │ - Verified Grounding  │       │   Guardrail           │
└───────────┬───────────┘       └───────────┬───────────┘       └───────────┬───────────┘
            │                               │                               │
            └───────────────────────────────┼───────────────────────────────┘
                                            │
        ┌───────────────────────────────────┼───────────────────────────────────┐
        ▼                                   ▼                                   ▼
┌───────────────────────┐       ┌───────────────────────┐       ┌───────────────────────┐
│ SystemDesignEngine    │       │ GapHandler & Transfer │       │ FollowUpEngine        │
│ - Role Architecture   │       │ - GCP -> AWS Parity   │       │ - 4-Tier Follow-up    │
│ - Ingestion & Stream  │       │ - Tenure Framing      │       │   Chains              │
│ - Scale & DLQ         │       │ - Zero Fabrication    │       │ - Edge Cases & "Why?" │
└───────────┬───────────┘       └───────────┬───────────┘       └───────────┬───────────┘
            │                               │                               │
            └───────────────────────────────┼───────────────────────────────┘
                                            │
                                            ▼
                    ┌───────────────────────────────────────────────┐
                    │   InterviewTruthValidator & ReadinessScorer   │
                    │   - Zero AWS Production Claims Check          │
                    │   - Metric Immutability Audit (25%, 35%, etc.)│
                    │   - Deterministic Multi-Dimensional Score     │
                    └───────────────────────┬───────────────────────┘
                                            │
                                            ▼
                    ┌───────────────────────────────────────────────┐
                    │      RoadmapGenerator (1, 3, 7, 14 Days)      │
                    │      + 10 JSON & Markdown Export Artifacts    │
                    │   data/generated/interview_prep/<prep_id>/    │
                    └───────────────────────────────────────────────┘
```

---

## 2. Core Architecture & Modules Implemented

| Component | File Path | Responsibilities |
| :--- | :--- | :--- |
| **Data Models** | `careerpilot/models/interview.py` | Pydantic schemas for `InterviewQuestion`, `InterviewAnswer`, `STARAnswer`, `SystemDesignScenario`, `PreparationRoadmap`, `InterviewReadinessScore`, `InterviewPlan`. |
| **Question Planner** | `careerpilot/interview/question_planner.py` | Allocates category quotas across 10 taxonomies based on role strategy and JD risk signals. |
| **Question Engine** | `careerpilot/interview/question_engine.py` | Generates prioritized questions with strategic rationale (`why_this_question`), interviewer intent, and expected topics. |
| **Answer Engine** | `careerpilot/interview/answer_engine.py` | Generates evidence-grounded answers formatted across 3 length modes (`short`, `standard`, `detailed`) with follow-up hooks. |
| **STAR Engine** | `careerpilot/interview/star_engine.py` | Formulates structured STAR behavioral answers for data quality, pipeline failures, and cost tuning; flags `INSUFFICIENT_EVIDENCE` when unevidenced. |
| **System Design Engine** | `careerpilot/interview/system_design.py` | Generates role-specific system design challenges complete with functional/non-functional requirements, scale assumptions, components, storage, processing, failure handling, cost, and trade-offs. |
| **Gap Handler** | `careerpilot/interview/gap_handler.py` | Manages technology gaps (e.g. AWS vs GCP) and tenure framing without fabricating unverified production claims. |
| **Follow-Up Engine** | `careerpilot/interview/followups.py` | Constructs 4-tier interviewer follow-up chains: Primary $\rightarrow$ Deeper Mechanics $\rightarrow$ Edge Cases $\rightarrow$ Trade-offs / "Why?". |
| **Readiness Scorer** | `careerpilot/interview/readiness_scorer.py` | Deterministically computes 6-component readiness scores (Technical, Resume, Project, Gap, System Design, Behavioral). |
| **Roadmap Generator** | `careerpilot/interview/roadmap.py` | Generates actionable study schedules for 1-day crash, 3-day fast-track, 7-day comprehensive, and 14-day mastery. |
| **Interview Truth Guard** | `careerpilot/interview/truth_validator.py` | Audits generated answers against candidate ground truth (`data/candidate/`), enforcing zero AWS production claims and metric immutability. |
| **Report Exporter** | `careerpilot/interview/report_exporter.py` | Exports 10 structured JSON and Markdown files into `data/generated/interview_prep/<prep_id>/`. |
| **LangGraph Workflow** | `careerpilot/graphs/interview_prep_graph.py` | Compiles state graph orchestrating input resolution, RAG retrieval, generation, truth validation, scoring, and exporting. |
| **CLI Runner** | `careerpilot/interview/prepare.py` | Terminal interface supporting `--job`, `--strategy`, `--difficulty`, `--questions`, and `--days`. |

---

## 3. Truth Guard Enforcement & Negative Test Results

The engine strictly enforces candidate truth constraints:
1. **Zero AWS Production Claims:** If an interviewer asks about AWS, the engine provides an honest, conceptual transferability response ("My hands-on cloud experience has primarily been on Google Cloud Platform (GCP), but cloud data engineering principles are fully transferable to AWS...").
2. **Metric Immutability:** Preserves verified candidate metrics (`~25%` BigQuery cost reduction, `~35%` data quality incident reduction, `~75%` Airflow auto-heal, `~60%` triage acceleration, `~500k+` daily transactions). Blocked any attempts at metric exaggeration.
3. **Personal Project Isolation:** The Local RAG Sandbox is explicitly framed as an offline personal engineering project, never as client enterprise experience.
4. **Insufficient Evidence Guardrails:** Unevidenced executive leadership questions return `is_insufficient_evidence=True` with honest guidance rather than hallucinating fake events.

---

## 4. Generated Artifacts

For each run, the pipeline generates 10 comprehensive files under `data/generated/interview_prep/<prep_id>/`:
- `interview_plan.json` & `interview_plan.md` — Executive plan overview and summary.
- `questions.json` & `questions.md` — Complete prioritized questions catalog with rationale and topics.
- `answers.json` & `answers.md` — Evidence-grounded answers across 3 length modes (Short, Standard, Detailed).
- `system_design.json` — End-to-end architecture scenarios with functional/non-functional requirements and trade-offs.
- `roadmap.json` — Structured day-by-day study schedule with practice drills.
- `readiness_report.md` — Multi-dimensional readiness score breakdowns and explanations.
- `truth_report.md` — Anti-hallucination verification audit report.

---

## 5. Test Suite Verification (100% Pass Rate Across All Milestones)

```bash
======================== 85 passed, 1 warning in 8.72s ========================
```

- **Milestone 1:** Candidate Data Integrity & Hierarchy (4 tests) — **PASS**
- **Milestone 2:** Local Dual-Store RAG Engine & Chunking (8 tests) — **PASS**
- **Milestone 3:** Job Analysis Engine & LangGraph Agent (14 tests) — **PASS**
- **Milestone 4:** Resume Tailoring & Strategy Engine (13 tests) — **PASS**
- **Milestone 5:** ATS Compatibility & Deep Scoring Engine (15 tests) — **PASS**
- **Milestone 6:** Interview Preparation & Question Engine (31 tests) — **PASS**
- **Total:** **85 / 85 tests passing (100%)**

---

## 6. Milestone 6 Completion Confirmation

Milestone 6 is fully completed, tested, and verified.
As instructed: **Stopping after Milestone 6.**
