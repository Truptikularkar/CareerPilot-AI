# CareerPilot AI — Phased Development Plan

## Overview
This development plan outlines the phased, test-driven roadmap for building CareerPilot AI. Each milestone focuses on a specific, self-contained subsystem with explicit verification criteria.

---

## Milestone Breakdown

### Milestone 1: Project Foundation & Baseline Data Models (Current Milestone)
- [x] Project architecture specification (`ARCHITECTURE.md`)
- [x] Phased roadmap definition (`DEVELOPMENT_PLAN.md`)
- [x] System documentation & setup guide (`README.md`)
- [x] Dependency specification (`requirements.txt`, `.env.example`)
- [x] Configuration subsystem with Pydantic BaseSettings (`careerpilot/core/config.py`)
- [x] Domain entities & Pydantic schemas (`careerpilot/models/`)
- [x] SQLite database schema & session setup (`careerpilot/db/`)
- [x] Sample verified candidate profile (`data/sample/sample_candidate_profile.json`)
- [x] Sample diverse JDs (`data/sample/sample_jds/`)
- [x] Baseline JD and Candidate Profile Parsers (`careerpilot/parsers/`)
- [x] Unit test suite skeleton (`tests/`)

### Milestone 2: Pluggable LLM Abstraction & Dual-Store RAG Engine
- [ ] LLM Provider Interface (`careerpilot/llm/base.py`)
- [ ] Google Gemini Provider with structured output schema support (`careerpilot/llm/gemini_provider.py`)
- [ ] Local Ollama / OpenAI-compatible provider (`careerpilot/llm/ollama_provider.py`)
- [ ] Mock LLM provider for zero-cost deterministic unit testing (`careerpilot/llm/mock_provider.py`)
- [ ] Embedding generation wrapper (`careerpilot/rag/embeddings.py`)
- [ ] Candidate Evidence Vector Store with metadata indexing (`careerpilot/rag/candidate_store.py`)
- [ ] Domain & Interview Knowledge Base Store (`careerpilot/rag/interview_store.py`)
- [ ] Pre-seeded technical interview knowledge chunks (Python, SQL, Spark, BigQuery, Airflow, RAG, LangChain, System Design, STAR behavioral)
- [ ] Hybrid Retriever with metadata filtering (`careerpilot/rag/retriever.py`)
- [ ] Verification: Unit tests for embedding, chunking, retrieval accuracy, and mock LLM calls.

### Milestone 3: Job Analysis Engine & LangGraph Agent
- [ ] Advanced JD parser with unstructured text cleanup & PDF extraction (`careerpilot/parsers/jd_parser.py`)
- [ ] Role, Seniority, and Category Classifier
- [ ] Requirement Extractor (Must-have vs Nice-to-have, Tech stack extraction)
- [ ] Candidate-Job Fit Scorer & Risk Factor Analyzer
- [ ] Decision Engine (Apply / Prepare / Skip with structured rationale)
- [ ] LangGraph Job Analysis State & Workflow graph (`careerpilot/graphs/job_analysis_graph.py`)
- [ ] Verification: End-to-end testing analyzing sample JDs with verified candidate profile.

### Milestone 4: Truth Guard & Explainable ATS Evaluation Engine
- [ ] Candidate Evidence Atomizer & Chunker (`careerpilot/parsers/evidence_extractor.py`)
- [ ] Evidence Classification Engine (`SUPPORTED`, `PARTIALLY_SUPPORTED`, `NOT_SUPPORTED`) (`careerpilot/truth_guard/classifier.py`)
- [ ] Truth Guard Auditor and claim verifier (`careerpilot/truth_guard/auditor.py`)
- [ ] Hallucination Sanitizer and skill gap logger (`careerpilot/truth_guard/sanitizer.py`)
- [ ] Rule-based and semantic ATS Scoring Engine (`careerpilot/ats/evaluator.py`)
- [ ] Formatting & Structure Rule Validator (`careerpilot/ats/formatting_rules.py`)
- [ ] Keyword Density & Anti-Stuffing Validator (`careerpilot/ats/keyword_matcher.py`)
- [ ] Verification: Automated regression tests ensuring fabricated skills are rejected 100% of the time.

### Milestone 5: Resume Tailoring, Strategies & ATS-Compliant DOCX Generator
- [ ] Multi-Role Strategy Engine (AI Engineer, Data Engineer, GenAI, Cloud Data Engineer) (`careerpilot/generators/strategy_engine.py`)
- [ ] Dynamic verified experience repositioning (without hallucinating separate histories)
- [ ] LangGraph Resume Tailoring Workflow with Self-Correction Loop (`careerpilot/graphs/resume_graph.py`)
- [ ] Clean, ATS-friendly DOCX Generator (`careerpilot/generators/resume_docx.py`)
- [ ] Verification: DOCX generation test, layout verification, and round-trip ATS scoring.

### Milestone 6: Interview Preparation & Multi-Day Roadmap Engine
- [ ] Multi-Category Question Generator (Recruiter, Resume Deep-Dive, Tech Concept, Implementation, Scenario, Production, System Design, STAR Behavioral) (`careerpilot/generators/interview_engine.py`)
- [ ] Multi-Level Answer Generator (Short, Medium, Deep-Dive, STAR) grounded in candidate evidence
- [ ] Topic-specific question matrices (Concept, Implementation, Debugging, Optimization, Production, Architecture)
- [ ] Preparation Roadmap Engine (1-day, 3-day, 7-day, 14-day study schedules) (`careerpilot/generators/roadmap_engine.py`)
- [ ] LangGraph Interview Preparation Workflow (`careerpilot/graphs/interview_prep_graph.py`)
- [ ] Verification: Question quality, answer grounding verification, and roadmap generation tests.

### Milestone 7: Turn-Based Adaptive Mock Interview Agent
- [ ] Mock Interview Session State Machine (`careerpilot/graphs/mock_interview_graph.py`)
- [ ] Turn-based question selection based on target role & previous answer scores
- [ ] Real-time Answer Evaluator (Clarity, Technical Depth, STAR Structure, Evidence Grounding)
- [ ] Adaptive Difficulty Scaler (Beginner -> Intermediate -> Advanced)
- [ ] Weakness Diagnostic & Final Readiness Score Report
- [ ] Verification: Simulated multi-turn mock interview unit tests.

### Milestone 8: Full Streamlit Web UI & Aggregated Career Memory
- [ ] Streamlit application shell & theme setup (`careerpilot/ui/app.py`)
- [ ] Dashboard Page (`1_Dashboard.py`): KPIs, active applications, top missing skills
- [ ] Job Analysis Page (`2_Analyze_Job.py`): JD paste/upload, interactive fit breakdown, action triggers
- [ ] Applications Tracker Page (`3_Applications.py`): Saved jobs, status tracking, resume versions
- [ ] Resume Builder Page (`4_Resume_Builder.py`): Strategy selector, live truth audit, DOCX download
- [ ] Interview Preparation Page (`5_Interview_Prep.py`): Question bank, tiered answers, study roadmaps
- [ ] Mock Interview Page (`6_Mock_Interview.py`): Interactive turn-based session with real-time feedback
- [ ] Skill Gaps & Trends Page (`7_Skill_Gaps.py`): Cross-job aggregate analysis & learning recommendations
- [ ] Settings Page (`8_Settings.py`): Provider configuration, API keys, database management
- [ ] Application Memory queries (recurring skills, best matching roles, resume version performance)
- [ ] Verification: Comprehensive manual testing across all pages and workflows.

---

## Testing & Quality Assurance Protocol
1. **Zero Hallucination Guarantee**: All tests assert that generated resume claims map 1:1 with candidate evidence chunks.
2. **Deterministic Mocking**: All LangGraph workflows will have mock-backed integration tests so CI/CD runs with zero API costs.
3. **Pydantic Type Safety**: Every LLM extraction must conform to strict Pydantic schemas.
