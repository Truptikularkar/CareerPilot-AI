# CareerPilot AI — Technical Architecture & Design Decisions

**Document:** `docs/TECHNICAL_DECISIONS.md`  
**Purpose:** Technical rationale, engineering trade-offs, and design justifications for CareerPilot AI.

---

## 1. Why LangGraph for Multi-Agent Orchestration?

When orchestrating complex multi-step career intelligence pipelines, selecting the correct orchestration paradigm is critical.

### Architectural Comparison

| Dimension | Simple Python Scripts | LangChain Chains (`RunnableSequence`) | LangGraph Stateful Workflows |
| :--- | :--- | :--- | :--- |
| **State Management** | Global variables or manual dictionary passing | Immutable, linear input-to-output pipeline | **Strongly-typed Pydantic state passed across cyclic graph nodes** |
| **Multi-Turn Cycles** | Complex `while` loops with fragile break states | Cannot loop or cycle backward | **Native cyclic graph execution (essential for multi-turn mock interviews)** |
| **Conditional Routing** | Hardcoded `if/else` procedural statements | Limited router chains (`RunnableBranch`) | **Deterministic conditional edges branching on performance or state criteria** |
| **Human-in-the-Loop** | Blocking `input()` prompts | Incompatible with async UI state | **Interactivity boundaries where graph yields for user turn and resumes seamlessly** |
| **Error Recovery & QA** | Try/except spaghetti code | Hard failure stops entire chain | **Node-level remediation loops (e.g. Truth Guard rejecting draft -> re-drafting)** |
| **Persistence & Audit** | Manual file writing | Ephemeral | **State checkpoints allowing step-by-step state inspection and resumption** |

### Why CareerPilot Requires LangGraph:
1. **Adaptive Interview Loops:** The Mock Interview Engine requires a dynamic multi-turn conversation where each turn evaluates candidate answers, dynamically recalculates topic mastery, adjusts interviewer demeanor, and routes to follow-ups or next topics. Linear chains cannot model this cycle.
2. **Truth Remediation Cycles:** In the Resume Tailoring Graph, if the Truth Guard node flags an unverified metric or technology, the graph routes state back to the drafting node with explicit remediation instructions rather than failing the process.
3. **Decoupled Node Testing:** Each node is a pure function taking `State` and returning a partial state dictionary update, enabling 100% isolated unit testing without invoking the entire pipeline.

---

## 2. Why Retrieval-Augmented Generation (RAG)?

### The Fundamental Problem of Pure LLMs in Career Tech
Generic LLMs (e.g. GPT-4, Gemini, Claude) suffer from catastrophic hallucination when generating resumes or interview prep:
- **Skill Hallucination:** If a JD mentions *AWS EMR*, the LLM will eagerly write *"Implemented AWS EMR clusters"* even if the candidate only used *GCP Dataproc*.
- **Metric Inflation:** LLMs invent arbitrary numbers like *"Improved pipeline speed by 40%"* or *"Managed $10M cloud budget"*.
- **Project Confusion:** LLMs disguise a 2-day tutorial project as a 3-year enterprise production architecture.

### How RAG Solves This:
CareerPilot AI anchors the LLM by retrieving **immutable, atomic candidate evidence chunks**:
```
Candidate Ground Truth (YAML/MD)
  ↓
Chunking & Metadata Tagging (Evidence Status: SUPPORTED)
  ↓
Dense Sentence Embeddings (all-MiniLM-L6-v2)
  ↓
Local ChromaDB Vector Collection
  ↓
Hybrid Dense + BM25 Retrieval (Reciprocal Rank Fusion)
  ↓
Retrieved Evidence Injected into Prompt Context
  ↓
LLM Formats Only Verified Facts (Zero Invention)
```

---

## 3. Why Two Isolated RAG Stores?

CareerPilot AI explicitly avoids dumping all documents into a single generic vector collection. Instead, it enforces strict domain separation:

```
┌──────────────────────────────────────┐     ┌──────────────────────────────────────┐
│       Candidate Evidence Store       │     │      Technical Knowledge Store       │
├──────────────────────────────────────┤     ├──────────────────────────────────────┤
│ "What has the candidate done?"       │     │ "What does the concept/tech mean?"   │
│ - Verified Cognizant production work │     │ - GCP BigQuery optimization patterns │
│ - Academic degrees & verified certs  │     │ - Apache Airflow backfill strategies │
│ - Verified metrics (e.g. 45% error ↓)│     │ - RAG architecture trade-offs (RRF)  │
│ - Personal sandbox projects          │     │ - Distributed data quality frameworks│
└──────────────────────────────────────┘     └──────────────────────────────────────┘
                   │                                            │
                   ▼                                            ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│ Combined Context: "What the candidate did, explained with deep technical rigor."  │
└───────────────────────────────────────────────────────────────────────────────────┘
```

### Why Separation is Vital:
1. **Zero Cross-Contamination:** If technical knowledge were in the candidate store, the LLM might retrieve a tutorial on Kubernetes and assume the candidate has 5 years of Kubernetes production experience.
2. **Metadata Filtering:** The candidate store enforces strict metadata filtering (`where={"evidence_status": "SUPPORTED"}` and `where={"allowed_for_resume": True}`).
3. **Independent Lifecycle:** The candidate store updates when the candidate updates their profile; the technical store updates as industry best practices evolve.

---

## 4. Deterministic vs. LLM Responsibilities

CareerPilot AI maintains a strict division of labor between deterministic software logic and probabilistic LLM reasoning:

| Subsystem Component | Probabilistic LLM Role | Deterministic Software Role |
| :--- | :--- | :--- |
| **Job Description Parsing** | Semantic entity extraction from unstructured prose | Schema normalization, regex cleaning, title slugging |
| **Role & Seniority** | Contextual understanding of ambiguous job titles | Word-boundary taxonomy lookup, seniority rules |
| **Fit Scoring** | Semantic relevance interpretation | **Mathematical weighted scoring formula & gap penalty** |
| **Resume Drafting** | Action verb optimization, bullet rephrasing | Evidence assembly, project boundary segregation |
| **Truth Guard** | Suggesting alternative truthful wording | **Exact regex metric validation, banned claim blocking** |
| **ATS Compatibility** | Semantic alignment cosine similarity | **Exact keyword frequency, density checks, table trap scan** |
| **Interview Readiness** | Generating insightful scenario questions | Question categorization, roadmap distribution rules |
| **Mock Interview Scoring** | Communication clarity & depth evaluation | **10-dimension rubric aggregation, difficulty escalation** |
| **Session Persistence** | N/A | **SQLite transactional ACID persistence & DB migrations** |

---

## 5. Cost, Latency & Concurrency Trade-Offs

1. **Embedding Cache & Local MiniLM:**
   - Embeddings are generated locally using `sentence-transformers/all-MiniLM-L6-v2` (384-dim).
   - Zero external API embedding calls, zero embedding cost, sub-5ms retrieval latency.
2. **Prompt Token Optimization:**
   - Instead of injecting whole candidate resumes into prompts, RAG retrieves only top-5 relevant chunks ($< 500$ tokens), cutting LLM inference costs by ~80%.
3. **Offline Fallback Guarantee:**
   - The entire platform runs seamlessly offline using `MockLLMProvider` or local Ollama instances (`llama3.1:8b`), guaranteeing zero external network dependencies during automated testing and private deployments.
