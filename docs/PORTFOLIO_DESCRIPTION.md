# CareerPilot AI — Portfolio & LinkedIn Presentation Descriptions

**Document:** `docs/PORTFOLIO_DESCRIPTION.md`  
**Purpose:** Formats for sharing CareerPilot AI across LinkedIn, GitHub profiles, personal websites, and technical case studies.

---

## 1. Short Description (GitHub Bio & Portfolio Card — ~150 Characters)
> An evidence-grounded AI career intelligence platform built with LangGraph, Dual-Store RAG, and ChromaDB for truthful resume tailoring, ATS scoring, and adaptive mock interviews.

---

## 2. Medium Description (LinkedIn Post / Project Summary — ~1,000 Characters)
> 🚀 **CareerPilot AI: An Evidence-Grounded AI Career Intelligence Platform**
>
> Most AI resume and career tools are simple prompt wrappers that hallucinate nonexistent tech skills and inflate metrics to beat ATS algorithms. 
>
> I built **CareerPilot AI** to solve this through a **strict zero-fabrication architecture**:
> - **Dual-Store Local RAG (ChromaDB):** Strictly isolates verified candidate employment records from technical domain knowledge.
> - **Deterministic Truth Guard:** An independent audit layer outside the LLM that programmatically blocks unverified claims and inflated numbers.
> - **LangGraph Multi-Agent Orchestration:** Stateful, cyclic workflows for job analysis, resume strategy repositioning, and multi-turn adaptive mock interviews.
> - **Explainable ATS Scoring:** Transparent 7-component evaluation with clean, table-free DOCX generation.
> - **10-Dimension Mock Interviewer:** Simulates realistic technical interviews across 7 personas and dynamically adjusts follow-up questions.
>
> Built with Python, LangGraph, ChromaDB, SQLite, SQLAlchemy, Streamlit, and 115 passing tests. 100% local and offline-capable!

---

## 3. Detailed Case Study Description (Personal Portfolio / Case Study)

### Project Overview
**CareerPilot AI** is an autonomous career intelligence platform engineered to eliminate LLM hallucinations from job matching, resume tailoring, and technical interview preparation.

### The Problem
Generative AI models excel at phrasing and synthesis, but when tasked with resume customization or interview prep, they routinely invent technologies, inflate metrics, and blur the line between personal weekend projects and enterprise production experience. Furthermore, candidates struggle with opaque ATS rejections and lack realistic, adaptive technical interview practice.

### Key Architectural Solutions
1. **Immutable Evidence Ledger:** Candidate records (experience, projects, skills, achievements) are stored as atomic evidence units tagged with strict metadata statuses (`SUPPORTED`, `PARTIALLY_SUPPORTED`, `NOT_SUPPORTED`).
2. **Dual-Store RAG Retrieval:** Candidate history is indexed in an isolated ChromaDB vector collection separate from technical domain concepts. Dense `all-MiniLM-L6-v2` embeddings and BM25 sparse search are combined using Reciprocal Rank Fusion (RRF).
3. **Deterministic Truth Guard:** Every generated bullet point and interview claim is cross-checked against the evidence ledger via regex and AST tokenization. Claims lacking proof are rejected and auto-remediated.
4. **Stateful LangGraph Workflows:** Four cyclic state machines orchestrate Job Analysis, Resume Tailoring, Interview Preparation, and Adaptive Mock Interviews with human-in-the-loop interaction points.
5. **Adaptive Mock Interview Engine:** Evaluates candidate answers across 10 rubrics (Technical Correctness, Relevance, Depth, Evidence Grounding, Structure, etc.) and routes adaptively based on measured topic mastery.
6. **Production Hardening & Privacy Isolation:** Implements a strict separation between public demo data (**Alex Rivera**) and private local records, validated by an automated 115-test PyTest suite.
