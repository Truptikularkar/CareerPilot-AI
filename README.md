# CareerPilot AI
### Autonomous Personal Job Intelligence, Truth-Guarded Resume Tailoring & Adaptive Mock Interview Copilot

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Tests Passing](https://img.shields.io/badge/tests-238%20passed-brightgreen.svg)]()
[![Orchestration: LangGraph](https://img.shields.io/badge/orchestration-LangGraph%20%7C%20LangChain-orange.svg)](https://github.com/langchain-ai/langgraph)
[![UI: Streamlit](https://img.shields.io/badge/ui-Streamlit-red.svg)](https://streamlit.io/)
[![Vector Store: ChromaDB](https://img.shields.io/badge/vector%20store-ChromaDB-blueviolet.svg)](https://www.trychroma.com/)
[![Zero Fabrication](https://img.shields.io/badge/anti--hallucination-Truth%20Guard-success.svg)]()

---

## Problem
In the modern technical job market, candidates face two major challenges:
1. **Opaque, Keyword-Heavy Screening:** Applicant Tracking Systems (ATS) reject qualified applicants due to formatting issues or unaligned terminology.
2. **The Generative AI "Hallucination Trap":** Standard LLM tools (e.g. basic ChatGPT prompts) aggressively invent unverified tech stacks (e.g., claiming Kubernetes or Kafka experience when a candidate has never used them) and inflate numeric metrics (e.g., turning 25% cost savings into 60%), leading to instant disqualification during technical interviews.

---

## Solution
**CareerPilot AI** is an evidence-grounded AI career copilot that strictly enforces an **immutable candidate source-of-truth grounding architecture**.

By combining **Dual-Store Local RAG**, **LangGraph multi-agent state machines**, and a **deterministic Truth Guard**, CareerPilot AI ensures that every resume bullet, ATS recommendation, technical Q&A, and adaptive mock interview question is 100% grounded in verified candidate records with zero unverified claims or invented metrics.

---

## Key Features
- **Explainable Job Analysis & Fit Scoring:** Clear natural-language rationale for every match decision (`APPLY`, `REVIEW`, `SKIP`). No more mysterious `0%` scores—explicitly breaks down must-have requirements, nice-to-have skills, verified experience tenure gaps, and cloud platform transferability (GCP $\leftrightarrow$ AWS).
- **Authoritative Professional Terminology:** Clean, accessible language across all user interfaces, eliminating confusing engineering and AI jargon.
- **Job Reality & Taxonomy Parsing:** Analyzes raw Job Descriptions (JDs) to extract true role classifications, seniority levels, and must-have vs. nice-to-have requirements.
- **Enterprise Multi-Device Security & Authentication:** RFC 9106 Argon2id password hashing, multi-device cryptographic session tokens, and strict candidate-level data isolation.
- **Truth-Guarded Resume Tailoring:** Repositions candidate experience across 4 strategic role tracks (Data Engineer, AI Data Engineer, GenAI Engineer, Cloud Data Engineer) with automatic rejection of unverified claims.
- **Dual-Format ATS Export (DOCX + PDF):** Exports single-column, table-free, header-safe, 100% searchable `.docx` and `.pdf` resumes.
- **Explainable ATS Compatibility Analysis:** Breaks down match scores across 7 transparent components (Keyword Coverage, Taxonomy, Semantic Alignment, Structure, Formatting, Readability, Anti-Stuffing).
- **Deep Interview Preparation:** Generates role-specific questions across 7 interview categories with tiered answers (Short, Standard, Deep Dive, STAR) and multi-day study roadmaps.
- **Multi-Turn Adaptive Mock Interviewer:** Simulates realistic technical interviews across 10 specialized modes and 7 interviewer personas with turn-by-turn rubric scoring.
- **17-Stage Recruitment Lifecycle:** End-to-end status tracking with friendly labels and state transitions.
- **Public/Private Data Isolation:** Seamless multi-environment switching (`LOCAL_PRIVATE` vs `HOSTED_PRIVATE`) with safe demo mode.


---

## Architecture

```
┌─────────────────┐       ┌────────────────────────┐       ┌───────────────────────┐
│ Job Description │ ────> │ Job Analysis & Fit RAG │ ────> │ Apply / Review / Skip │
└─────────────────┘       └────────────────────────┘       └───────────────────────┘
                                                                       │
                                                                       ▼
┌─────────────────┐       ┌────────────────────────┐       ┌───────────────────────┐
│ ATS Analysis    │ <──── │ Resume Tailoring Graph │ <──── │ Strategy Selection    │
└─────────────────┘       └────────────────────────┘       └───────────────────────┘
        │
        ▼
┌─────────────────────────┐       ┌────────────────────────┐       ┌───────────────────────┐
│ Interview Prep Graph    │ ────> │ Adaptive Mock Agent    │ ────> │ Application Tracker   │
│ (Roadmap, Q&A, STAR)    │       │ (10 Modes, 7 Personas) │       │ (Kanban & History)    │
└─────────────────────────┘       └────────────────────────┘       └───────────────────────┘
```

See [docs/ARCHITECTURE_FINAL.md](docs/ARCHITECTURE_FINAL.md) for full Mermaid sequence diagrams and database schemas.

---

## Tech Stack
- **Agent Orchestration:** LangGraph, LangChain Core, Pydantic v2
- **Vector Storage & RAG:** ChromaDB, Sentence Transformers (`all-MiniLM-L6-v2`), BM25, Reciprocal Rank Fusion (RRF)
- **Relational Storage:** SQLite, SQLAlchemy 2.0 ORM
- **LLM Abstraction:** Google Gemini API (`gemini-1.5-flash`), Local Ollama (`llama3.1:8b`), Deterministic Mock Provider
- **Document Processing:** PyMuPDF, python-docx
- **UI & Presentation:** Streamlit, Plotly, Pandas
- **Testing & Quality:** PyTest (238 passing tests), Component Health Diagnostics

---

## RAG Architecture
CareerPilot AI separates knowledge into **Two Isolated Local ChromaDB Stores**:
1. **Candidate Evidence Store:** Indexes verified employment history, project highlights, metrics, and skills. Enforces metadata filters (`evidence_status == 'SUPPORTED'`).
2. **Technical Knowledge Store:** Indexes engineering concepts, system design architectures, and interview best practices.

*Why separation matters:* It prevents cross-contamination where general technical explanations could be misattributed as candidate work experience.

---

## LangGraph Workflows
The platform orchestrates 4 discrete state machine graphs:
1. **Job Analysis Graph:** Parses JD text $\rightarrow$ Classifies role taxonomy $\rightarrow$ Extracts requirements $\rightarrow$ Retrieves evidence $\rightarrow$ Computes fit score $\rightarrow$ Analyzes risks $\rightarrow$ Emits decision (**APPLY / REVIEW / SKIP**).
2. **Resume Tailoring Graph:** Ingests target job analysis $\rightarrow$ Selects strategy $\rightarrow$ Retrieves verified bullets $\rightarrow$ Drafts resume $\rightarrow$ Truth Guard audit $\rightarrow$ ATS precheck $\rightarrow$ DOCX export.
3. **Interview Preparation Graph:** Builds readiness seed $\rightarrow$ Dual-store retrieval $\rightarrow$ Generates 7 question categories $\rightarrow$ Assembles tiered & STAR answers $\rightarrow$ Builds study roadmap.
4. **Adaptive Mock Interview Graph:** Initializes session $\rightarrow$ Selects question $\rightarrow$ Yields for candidate response $\rightarrow$ Evaluates turn across 10 rubrics $\rightarrow$ Routes adaptively (escalates difficulty / probes / reinforces) $\rightarrow$ Emits diagnostic scorecard.

---

## Truth Guard
The **Truth Guard** is an independent verification layer implemented outside the LLM's own self-judgment:
- **3-Tier Evidence Taxonomy:**
  - `SUPPORTED`: Verified in candidate records; permitted on resumes and interview claims.
  - `PARTIALLY_SUPPORTED`: Conceptual / transferable knowledge; permitted ONLY in interview answers.
  - `NOT_SUPPORTED`: Unverified claims; strictly BLOCKED from resumes and flagged as gaps in ATS reports.
- **Deterministic Regex & Tokenizer Audit:** Extracts numbers, technologies, and project names from LLM drafts and matches them against the evidence ledger, auto-rejecting fabricated claims.

See [docs/TRUTH_GUARD.md](docs/TRUTH_GUARD.md) for full audit specifications.

---

## ATS Engine
Provides transparent **"ATS-Style Compatibility Analysis"** based on open industry heuristics:
- **Keyword Coverage Matrix:** Exact and semantic matching for must-haves and nice-to-haves.
- **Parsing Trap Detection:** Audits resumes against tables, multi-column layouts, text boxes, and non-standard headers.
- **Anti-Stuffing Analysis:** Penalizes unnatural keyword repetition lacking narrative context.

---

## Resume Generation
- Tailors resumes across 4 strategic tracks: **Data Engineer**, **AI Data Engineer**, **GenAI Engineer**, and **Cloud Data Engineer**.
- Enforces strict project boundary isolation: personal sandbox projects are kept in `Projects` and never disguised as enterprise production experience.
- Generates clean, table-free ATS `.docx` resumes using `python-docx`.

---

## Interview Preparation
- Generates role-specific questions across 7 categories: *Recruiter*, *Resume Deep Dive*, *Technical Concept*, *Implementation*, *System Design*, *Production Scenario*, and *STAR Behavioral*.
- Provides tiered answer models: *Short (30s)*, *Standard (90s)*, *Deep Dive (3min)*, and *STAR Narratives*.
- Compiles customized 1-day, 3-day, 7-day, and 14-day study roadmaps.

---

## Adaptive Mock Interview
- Conducts turn-by-turn conversational practice across **10 specialized modes** (System Design, Behavioral, GenAI, Data Eng, GCP Cloud, Weakness Focus).
- Simulates **7 interviewer personas** (Recruiter, Technical Engineer, Senior Engineer, AI Engineer, Data Engineer, Cloud Engineer, Hiring Manager).
- Scores responses across **10 standardized rubrics** (Correctness, Relevance, Depth, Evidence Grounding, Structure, etc.) with adaptive difficulty escalation.

---

## Demo
An 8-step live walkthrough script is available in [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md).
- **Public Demo Mode:** Operates safely on synthetic candidate **Alex Rivera** with zero private data exposure.

---

## Screenshots
A catalog of recommended screenshots for all 10 pages is documented in [docs/SCREENSHOTS.md](docs/SCREENSHOTS.md).

---

## Project Structure
```
careerpilot/
├── ats/               # Explainable ATS scoring & formatting validator
├── core/              # Configuration, constants, logging, exception handlers
├── db/                # SQLite database schema, session & repository layer
├── generators/        # Strategy selector, ATS DOCX generator, study roadmap
├── graphs/            # LangGraph stateful multi-step pipelines
├── health.py          # 7-vector system diagnostics & health check engine
├── interview/         # Readiness seed extractor & answer generation
├── llm/               # Pluggable LLM factory (Gemini, Ollama, Mock)
├── mock_interview/    # Adaptive mock interviewer, scoring rubrics & followups
├── models/            # Pydantic schemas across all entities
├── parsers/           # JD & candidate parsers, evidence atomizer
├── rag/               # Dual-store vector collections, embeddings & retriever
├── services/          # CareerPilotService unified orchestration layer
├── truth_guard/       # Evidence classifier, validator, and sanitizer
└── ui/                # Streamlit multi-page interface & dashboard
    ├── app.py
    └── pages/         # 10 dedicated workflow pages
data/
├── demo/              # Synthetic demo candidate (Alex Rivera - Safe for Public)
├── evaluation/        # Benchmark job descriptions & test suites
├── generated/         # Output resumes & mock interview logs (gitignored)
└── knowledge/         # Technical interview knowledge base files
docs/                  # Complete architectural & interview defense documentation
tests/                 # 115 comprehensive unit & integration tests
```

---

## Installation

```bash
# 1. Clone repository
git clone https://github.com/your-username/careerpilot-ai.git
cd careerpilot-ai

# 2. Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Configuration

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Configure settings:
```env
CAREERPILOT_MODE=DEMO
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_optional_gemini_api_key
GEMINI_MODEL=gemini-1.5-flash
```
*(Note: If `GEMINI_API_KEY` is left blank, CareerPilot operates 100% offline using deterministic heuristics and `MockLLMProvider`.)*

---

## Running Locally

```bash
streamlit run careerpilot/ui/app.py
```

---

## Running Tests

Execute the automated test suite (100% offline, zero network dependencies):
```bash
pytest -v tests/
```
**Results:** **238 / 238 PASSED (100% Success Rate)** across all 14 milestones.

---

## Streamlit Deployment
See [DEPLOYMENT.md](DEPLOYMENT.md) for full instructions on deploying to **Streamlit Community Cloud**, **Hugging Face Spaces**, or **Docker**.

---

## Security
- **Strict Data Isolation:** Private candidate records (`data/candidate/`, `data/private/`, `.env`, `*.db`) are strictly excluded via `.gitignore`.
- **API Key Masking:** Keys are never printed in plaintext in logs or UI diagnostics (`AIza...****`).
- **Upload Constraints:** File uploads are restricted to `.pdf` and `.txt` with an enforced 5 MB size limit.
- See [SECURITY_AUDIT.md](SECURITY_AUDIT.md) for complete compliance details.

---

## Limitations
- **ATS Disclaimers:** Commercial ATS systems use undisclosed, proprietary filters; CareerPilot provides heuristic ATS-style compatibility analysis, not guaranteed pass predictions.
- **Fit Scoring Heuristic:** Scores are prioritization indicators, not official hiring outcomes.
- **SQLite Concurrency:** Suitable for local and single-user demo deployments; multi-tenant SaaS requires PostgreSQL migration.
- See [docs/LIMITATIONS.md](docs/LIMITATIONS.md) for full engineering boundaries.

---

## Future Improvements
- Managed PostgreSQL migration with Alembic.
- Vertex AI Vector Search integration.
- Real-time voice mock interviews with WebRTC and speech analytics.
- Multi-tenant OAuth2 authentication.
- See [docs/FUTURE_ROADMAP.md](docs/FUTURE_ROADMAP.md) for the complete 10-phase roadmap.

---

## Author
**CareerPilot AI Engineering Team**  
*Engineered with Python, LangGraph, ChromaDB, and Streamlit.*
