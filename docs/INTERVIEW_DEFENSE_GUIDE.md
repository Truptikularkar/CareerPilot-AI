# CareerPilot AI — Technical Interview Defense Guide & Architectural Q&A

**Document:** `docs/INTERVIEW_DEFENSE_GUIDE.md`  
**Purpose:** Comprehensive technical interview defense guide covering 30+ architectural questions across 19 technical categories.

---

## Table of Contents
1. [Architecture & System Design](#1-architecture--system-design)
2. [RAG & Vector Retrieval](#2-rag--vector-retrieval)
3. [LangGraph & Agent Orchestration](#3-langgraph--agent-orchestration)
4. [Truth Guard & Anti-Hallucination](#4-truth-guard--anti-hallucination)
5. [ATS & Document Processing](#5-ats--document-processing)
6. [Adaptive Mock Interview & Rubrics](#6-adaptive-mock-interview--rubrics)
7. [Persistence, Security & Cloud Scaling](#7-persistence-security--cloud-scaling)

---

## 1. Architecture & System Design

### Q1: Why did you build CareerPilot AI, and what problem does it solve?
- **Why Interviewer Asks:** Evaluates product thinking, problem identification, and engineering motivation.
- **Expected Answer:** Standard LLMs hallucinate candidate skills and exaggerate numbers when tailoring resumes. Candidates also face black-box ATS rejections and lack realistic, interactive technical interview preparation. CareerPilot AI solves this through an immutable evidence ledger, dual-store RAG, deterministic truth auditing, and stateful LangGraph agents.
- **CareerPilot Evidence:** The Truth Guard rejects claims not present in `data/candidate/`, and the ATS Engine provides transparent mathematical component scores.
- **Follow-up Probe:** *"Why not just write a carefully engineered prompt in ChatGPT?"* $\rightarrow$ Prompting alone suffers from instruction drift, lacks stateful interview loops, and cannot mathematically verify metrics against a database.

### Q2: Walk me through the high-level architecture of the system.
- **Why Interviewer Asks:** Tests system visualization and modular decomposition skills.
- **Expected Answer:** CareerPilot uses a layered architecture: Streamlit Presentation Layer $\rightarrow$ `CareerPilotService` Orchestrator $\rightarrow$ 4 LangGraph State Machines $\rightarrow$ Core Intelligence Layer (Role Classifier, Fit Scorer, Strategy Engine, Truth Guard, ATS Evaluator) $\rightarrow$ Dual-Store RAG Layer (ChromaDB) $\rightarrow$ Persistence Layer (SQLite & DOCX Generator).
- **CareerPilot Evidence:** See [`ARCHITECTURE_FINAL.md`](ARCHITECTURE_FINAL.md) for full flowchart and sequence diagram.

---

## 2. RAG & Vector Retrieval

### Q3: Why did you use RAG instead of fine-tuning a model on candidate data?
- **Why Interviewer Asks:** Tests knowledge of model customization trade-offs (RAG vs Fine-Tuning).
- **Expected Answer:** 
  1. **Dynamic Updates:** Candidate records, projects, and target JDs change constantly. RAG allows instant updates without expensive retraining.
  2. **Zero Training Cost & Privacy:** No proprietary candidate PII is baked into model weights.
  3. **Strict Grounding:** RAG provides traceable source attribution for every retrieved chunk.
- **CareerPilot Evidence:** `CandidateStore` indexes local Markdown/YAML files directly into local ChromaDB with sub-10ms query times.

### Q4: Why did you create two isolated RAG vector stores instead of one?
- **Why Interviewer Asks:** Evaluates domain isolation and retrieval pollution prevention.
- **Expected Answer:** Putting candidate records and technical interview concepts into one vector store causes retrieval cross-contamination. If a candidate searches for Kubernetes, a general knowledge chunk on Kubernetes architecture might be retrieved and incorrectly attributed as candidate work experience.
- **CareerPilot Evidence:** `CandidateStore` answers *"What did the candidate do?"* with metadata filters (`SUPPORTED`), while `InterviewStore` answers *"What does this technical concept mean?"*.

### Q5: How did you select your chunking strategy and embedding model?
- **Why Interviewer Asks:** Assesses practical RAG engineering decisions.
- **Expected Answer:** We chunk candidate files semantically by project, work experience role, and individual achievement bullet rather than arbitrary character splits. We chose `sentence-transformers/all-MiniLM-L6-v2` because it runs 100% locally with 384-dimensional dense vectors, zero API cost, and sub-5ms latency on CPU.
- **CareerPilot Evidence:** `CandidateStore.chunk_experience_data()` and `CandidateStore.chunk_project_data()` in `careerpilot/rag/candidate_store.py`.

### Q6: What is Reciprocal Rank Fusion (RRF) and why did you use hybrid retrieval?
- **Why Interviewer Asks:** Tests advanced retrieval techniques beyond basic vector search.
- **Expected Answer:** Dense semantic search can miss exact keyword matches (e.g. acronyms like *GCP*, *ETL*, *RRF*), while sparse BM25 misses semantic synonyms (e.g. *data warehousing* matching *BigQuery*). Hybrid retrieval computes both and combines their ranks using RRF: $RRF\_Score(d) = \sum_{m} \frac{1}{k + rank_m(d)}$ where $k=60$.
- **CareerPilot Evidence:** `Retriever.hybrid_search()` in `careerpilot/rag/retriever.py`.

---

## 3. LangGraph & Agent Orchestration

### Q7: Why did you choose LangGraph over standard LangChain chains or AutoGen?
- **Why Interviewer Asks:** Evaluates agent orchestration framework selection and trade-offs.
- **Expected Answer:** LangChain chains are strictly linear DAGs that cannot model multi-turn cyclic loops or conditional rollbacks. AutoGen is conversation-based and non-deterministic. LangGraph provides typed Pydantic state passed across cyclic graph nodes, native conditional routing, and clean human-in-the-loop state yields.
- **CareerPilot Evidence:** The Mock Interview Graph loops over user turns and dynamically routes to follow-ups or next topics, while the Resume Graph uses a remediation cycle if Truth Guard blocks a draft.

### Q8: How does state persistence work in your LangGraph implementation?
- **Why Interviewer Asks:** Tests understanding of state serialization and transactional integrity.
- **Expected Answer:** Each graph defines a typed state schema (e.g. `JobAnalysisState`, `ResumeTailoringState`, `MockInterviewState`). As nodes execute, they return dictionary updates that merge into the state. State checkpoints are persisted into SQLite relational tables (`applications`, `mock_interview_sessions`, `mock_turns`).
- **CareerPilot Evidence:** `careerpilot/graphs/mock_interview_graph.py` and `careerpilot/db/repository.py`.

---

## 4. Truth Guard & Anti-Hallucination

### Q9: How does Truth Guard work and why is it implemented outside the LLM?
- **Why Interviewer Asks:** Critical question on AI safety and guardrail engineering.
- **Expected Answer:** Asking an LLM to evaluate its own honesty fails because prompt optimization pressures cause instruction degradation. Truth Guard is a deterministic post-generation audit layer. It extracts technologies, metrics, and project names from the LLM output via regex and AST tokenizers, then verifies them against an immutable candidate evidence ledger.
- **CareerPilot Evidence:** `TruthValidator.audit_resume()` in `careerpilot/truth_guard/validator.py`.

### Q10: How do you handle unverified metrics and technologies required by a job?
- **Why Interviewer Asks:** Tests boundary handling between candidate gaps and honest application framing.
- **Expected Answer:** If a JD requires a missing technology (e.g. AWS Redshift when candidate only has GCP BigQuery):
  1. On the resume: The skill is strictly omitted from Experience bullets.
  2. In ATS reports: It is flagged as a GAP with zero score penalty on truth.
  3. In Interview Prep: It generates a *Transferable Conceptual Framing* answer rather than a false production claim.
- **CareerPilot Evidence:** `test_ats_truth_integration_aws_gap_truthful()` in `tests/test_ats_truth_integration.py`.

---

## 5. ATS & Document Processing

### Q11: Does your ATS Engine claim to predict commercial ATS passes?
- **Why Interviewer Asks:** Tests honesty, realistic product claims, and domain understanding.
- **Expected Answer:** No. Commercial ATS systems (Workday, Taleo, Greenhouse, iCIMS) use proprietary, divergent parsing heuristics. CareerPilot explicitly provides an *"ATS-Style Compatibility Analysis"* based on open formatting standards, keyword frequency distributions, semantic alignment, and parsing risk detection.
- **CareerPilot Evidence:** Disclaimers in UI and formal specification in `docs/LIMITATIONS.md`.

### Q12: How do you prevent ATS formatting traps during DOCX generation?
- **Why Interviewer Asks:** Evaluates practical document engineering knowledge.
- **Expected Answer:** Real ATS parsers fail when reading complex multi-column tables, text boxes, headers/footers, and non-standard fonts. CareerPilot uses `python-docx` to generate linear, single-column, table-free documents with standard semantic section headers (`Summary`, `Experience`, `Projects`, `Skills`, `Education`).
- **CareerPilot Evidence:** `ResumeDocxGenerator` in `careerpilot/generators/resume_docx.py` and test cases in `tests/test_docx_inspector.py`.

---

## 6. Adaptive Mock Interview & Rubrics

### Q13: How does the Adaptive Mock Interview Agent decide what question to ask next?
- **Why Interviewer Asks:** Tests understanding of adaptive state machines and dynamic routing.
- **Expected Answer:** The agent evaluates the candidate's previous response across 10 rubrics. If the score is $\ge 85\%$, it escalates difficulty or asks an advanced edge-case system design probe. If the score is $< 60\%$, it asks a clarification question or provides a coaching hint. If the topic is mastered, it transitions to the next category in the roadmap.
- **CareerPilot Evidence:** `AdaptiveRouter.route_next_action()` in `careerpilot/mock_interview/router.py`.

### Q14: How do interviewer personas affect the interview?
- **Why Interviewer Asks:** Tests prompt engineering and behavioral modeling.
- **Expected Answer:** Personas (Recruiter, Technical Engineer, Senior Engineer, Hiring Manager) adjust the tone, questioning depth, and focus areas (e.g. Senior Engineer probes failure modes, Recruiter probes culture fit) without altering candidate ground truth facts.
- **CareerPilot Evidence:** `InterviewerPersona` constants in `careerpilot/core/constants.py`.

---

## 7. Persistence, Security & Cloud Scaling

### Q15: How is candidate privacy protected in public deployments?
- **Why Interviewer Asks:** Critical security and compliance question.
- **Expected Answer:** The application implements two isolated modes: `DEMO` and `LOCAL_PRIVATE`. In `DEMO` mode, the app uses 100% synthetic candidate data (**Alex Rivera**) and an isolated demo database. Private candidate files (`data/candidate/`, `data/private/`, `.env`, `*.db`) are strictly excluded via `.gitignore`.
- **CareerPilot Evidence:** `SECURITY_AUDIT.md` and `careerpilot/health.py`.

### Q16: How would you scale CareerPilot AI to handle 10,000 concurrent users?
- **Why Interviewer Asks:** Tests distributed systems design and cloud migration capability.
- **Expected Answer:**
  1. **Web / Agent Layer:** Deploy containerized FastAPI / Streamlit pods on GCP Cloud Run or AWS ECS Fargate with auto-scaling.
  2. **Database:** Migrate SQLite to Google Cloud SQL (PostgreSQL) or AWS Aurora Serverless with connection pooling (PgBouncer).
  3. **Vector Database:** Replace local ChromaDB with Vertex AI Vector Search or AWS OpenSearch Serverless.
  4. **Async Task Queue:** Decouple heavy LangGraph runs using Celery / Google Cloud Tasks and Redis.
  5. **Caching:** Cache repeated JD taxonomy analyses in Redis to avoid redundant parsing.
- **CareerPilot Evidence:** Full blueprint in [`CLOUD_SCALING_DESIGN.md`](CLOUD_SCALING_DESIGN.md).
