import streamlit as st

st.set_page_config(page_title="About — CareerPilot AI", page_icon="ℹ️", layout="wide")

from careerpilot.services.auth_service import AuthService
from careerpilot.core.config import settings

if not settings.is_demo_mode:
    AuthService.require_auth()


st.title("ℹ️ About CareerPilot AI")
st.caption("Personal Job Intelligence, Resume Tailoring, and Adaptive Interview Preparation Agent.")

st.markdown("---")

# 1. Product Vision & Principles
col1, col2 = st.columns([3, 2])
with col1:
    st.markdown("### 🎯 Product Mission")
    st.markdown("""
    **CareerPilot AI** is an autonomous, evidence-grounded career assistant engineered to help technical professionals 
    navigate the modern job market with precision, efficiency, and zero fabrication.
    
    Instead of hallucinating generic claims or acting as a simple chatbot prompt wrapper, CareerPilot AI uses:
    1. **Strict Candidate Grounding:** Candidate experience, metrics, projects, and tenure are verified against an immutable source of truth.
    2. **Dual-Store RAG Architecture:** Candidate Evidence and Technical Interview Knowledge are indexed in isolated vector stores.
    3. **Deterministic Truth Guard:** Validates every resume bullet and interview answer before exporting or scoring.
    4. **Explainable Scoring:** Clear mathematical component weights and transparent reasoning for fit and ATS metrics.
    """)

with col2:
    st.markdown("### 🛡️ Core Guardrail Rules")
    st.info("""
    - **Zero Fabrication:** Never claims unverified technologies or inflated metrics.
    - **Project Isolation:** Personal sandbox projects are never presented as enterprise production experience.
    - **Cloud Transferability:** Accurately maps cross-cloud concepts (e.g. AWS Redshift to GCP BigQuery) without falsely claiming direct production tenure.
    - **Read-Only Safety:** Real candidate source files remain untouched.
    """)

st.markdown("---")

# 2. End-to-End System Architecture
st.subheader("🏗️ System Architecture & Workflow Pipeline")

st.markdown("""
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
""")

st.markdown("---")

# 3. Verified Technology Stack
st.subheader("💻 Verified Technology Stack")

t1, t2, t3, t4 = st.columns(4)

with t1:
    st.markdown("##### 🧠 Orchestration & Agents")
    st.markdown("""
    - **LangGraph**: Stateful multi-step graph pipelines
    - **LangChain Core**: Agent prompt execution & state modeling
    - **Pydantic v2**: Strict schema validation & contracts
    """)

with t2:
    st.markdown("##### 🔍 Retrieval-Augmented Gen")
    st.markdown("""
    - **ChromaDB**: Isolated vector collections
    - **Sentence Transformers**: `all-MiniLM-L6-v2` dense embeddings
    - **Dense + Sparse Search**: Reciprocal Rank Fusion
    """)

with t3:
    st.markdown("##### 💾 Storage & Data")
    st.markdown("""
    - **SQLite**: Local relational database
    - **SQLAlchemy 2.0**: Typed ORM and repository patterns
    - **python-docx**: ATS-friendly document generation
    """)

with t4:
    st.markdown("##### 🖥️ Presentation & LLMs")
    st.markdown("""
    - **Streamlit**: Multi-page local UI
    - **Google Gemini API**: `gemini-1.5-flash`
    - **Ollama / Mock LLM**: 100% offline fallback support
    """)

st.markdown("---")

# 4. Open-Source & GitHub Readiness
st.markdown("### 📦 Public Repository & Security Model")
st.markdown("""
CareerPilot AI is architected with strict separation between public code and private user data:
- **Public Demo Mode (`DEMO`):** Runs on synthetic candidate **Alex Rivera** for safe demonstrations without exposing personal data.
- **Local Private Mode (`LOCAL_PRIVATE`):** Runs locally against private ground-truth files and local SQLite databases.
- **Protected Secrets:** No API keys, credentials, or private candidate history are committed to version control.
""")
