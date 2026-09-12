# CareerPilot AI — Resume Project Descriptions

**Document:** `docs/RESUME_PROJECT_DESCRIPTION.md`  
**Purpose:** Verified, high-impact resume bullet points tailored for different technical career tracks.

---

## 1. Tailored Version: AI Data Engineer / Platform Engineer

**CareerPilot AI — Evidence-Grounded Career Intelligence & Multi-Agent Platform**  
*Technologies: Python, LangGraph, ChromaDB, Sentence Transformers, SQLite, SQLAlchemy, Streamlit, PyTest*

- Architected an autonomous, evidence-grounded career intelligence platform using **LangGraph**, **ChromaDB**, and **Pydantic** to parse JDs, compute deterministic fit scores, and tailor resumes with zero hallucinations.
- Engineered a **Dual-Store RAG retrieval engine** separating candidate work evidence from technical domain knowledge, using dense `all-MiniLM-L6-v2` embeddings and Reciprocal Rank Fusion (RRF) reranking.
- Designed a deterministic **Truth Guard verification layer** that audits LLM-generated resume bullets and interview claims against an immutable evidence ledger, automatically rejecting unverified technologies and inflated metrics.
- Developed an **Explainable ATS Compatibility Engine** computing 7-component match scores across exact keyword frequencies, taxonomy hierarchies, and table/header parsing traps with automated DOCX generation.
- Implemented a stateful, multi-turn **Adaptive Mock Interview Agent** executing turn-by-turn evaluations across 10 rubrics, dynamic difficulty escalation, and 7 configurable interviewer personas.
- Built a comprehensive automated test suite of **115 unit and integration tests** achieving a **100% pass rate** with zero external API dependencies.

---

## 2. Tailored Version: Data Engineer / Data Platform Specialist

**CareerPilot AI — Data-Centric Career Intelligence Platform**  
*Technologies: Python, SQL, ChromaDB, SQLite, SQLAlchemy 2.0, python-docx, PyTest, Streamlit*

- Engineered an automated data intelligence pipeline parsing unstructured job descriptions and mapping requirement taxonomies against structured candidate data stored in **SQLite** and **ChromaDB**.
- Built an **immutable candidate evidence ledger** and vector store utilizing dense semantic search and metadata filtering (`SUPPORTED`, `PARTIALLY_SUPPORTED`, `NOT_SUPPORTED`) to guarantee data integrity.
- Created an explainable **ATS evaluation and scoring engine** calculating deterministic match percentages, skill gap matrices, and keyword density distributions.
- Automated generation of ATS-compliant, table-free `.docx` resumes using **python-docx** and structured data schemas.
- Developed persistent application tracking pipelines with relational **SQLAlchemy 2.0** ORM entities, session migrations, and diagnostic health check monitoring.
- Validated system robustness with **115 automated PyTest test cases** running 100% locally and offline.

---

## 3. Tailored Version: Generative AI / LLM Systems Engineer

**CareerPilot AI — Stateful Agentic RAG & Mock Interview Copilot**  
*Technologies: LangGraph, LangChain, Google Gemini API, Ollama, ChromaDB, Pydantic v2, Streamlit*

- Designed and orchestrated **4 stateful LangGraph multi-agent workflows** (Job Analysis, Resume Tailoring, Interview Prep, Adaptive Mock Interview) featuring cyclic feedback loops and conditional branching.
- Built a **Dual-Store RAG architecture** combining dense semantic embeddings with sparse keyword matching to ground generative outputs and eliminate LLM hallucinations.
- Engineered an independent **Truth Guard guardrail system** outside model reasoning to programmatically enforce factual boundaries on AI-generated claims.
- Developed a turn-based **Adaptive Mock Interview Agent** that tracks candidate topic mastery in graph state and dynamically selects follow-up probes based on multi-dimensional rubrics.
- Supported pluggable LLM backends (**Google Gemini**, **Ollama**, and **Deterministic Mock Provider**) with seamless offline fallbacks.
