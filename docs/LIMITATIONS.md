# CareerPilot AI — System Limitations & Engineering Constraints

**Document:** `docs/LIMITATIONS.md`  
**Purpose:** Transparent documentation of technical boundaries, heuristic assumptions, and real-world system constraints.

---

## 1. ATS Scoring & Vendor Divergence
- **No Commercial ATS Predictability:** Proprietary Applicant Tracking Systems (Workday, Greenhouse, Taleo, iCIMS, Lever) use disparate, undisclosed parsing algorithms and configurable employer filters. CareerPilot AI explicitly provides an **"ATS-Style Compatibility Analysis"** based on open formatting standards, keyword frequencies, and semantic alignment. It does not and cannot guarantee resume passage through any third-party corporate portal.
- **Table & Multi-Column Limitations:** While CareerPilot generates single-column ATS-compliant `.docx` files, parsing third-party uploaded PDF resumes with complex graphic layouts or non-standard fonts may result in OCR or extraction artifacts.

---

## 2. Fit Scoring & Decision Heuristics
- **Heuristic Prioritization:** The Candidate-Job Fit Score (0–100) and recommendation engine (**APPLY / REVIEW / SKIP**) are deterministic heuristic tools designed to assist candidates in prioritizing their job search. They do not constitute an authoritative hiring prediction.
- **Weight Configuration:** Default scoring weights (35% must-haves, 20% experience, 15% role alignment, etc.) are heuristic approximations that may not reflect every individual recruiter's specific priorities.

---

## 3. Truth Guard & Evidence Ledger Boundaries
- **Dependency on Candidate Ground Truth:** Truth Guard verifies generated claims strictly against the candidate source-of-truth files in `data/candidate/` or `data/demo/`. If the candidate provides incomplete, outdated, or inaccurate source data, Truth Guard will treat that data as verified truth.
- **Regex & Entity Tokenizer Edge Cases:** Highly ambiguous, novel, or compound technical terms not present in the technology synonym taxonomy may occasionally require manual candidate review.

---

## 4. Local Database & Concurrency Constraints
- **SQLite Concurrency:** The local SQLite database utilizes file-level locking for write operations. While suitable for single-user local workflows and demonstration instances, it is not engineered for high-concurrency multi-tenant SaaS environments without upgrading to PostgreSQL.
- **Local ChromaDB Directory Storage:** In local mode, ChromaDB persists vector indexes to the local filesystem. Scaling beyond hundreds of thousands of candidate chunks requires a distributed managed vector database (e.g. Vertex AI Vector Search or Pinecone).

---

## 5. LLM Provider Dependencies & Latency
- **Probabilistic Generation:** While guarded by deterministic post-processing, underlying LLM outputs remain probabilistic and subject to external provider availability, rate limits, and latency spikes.
- **Offline Mock Fallback Trade-Off:** The offline `MockLLMProvider` enables deterministic, network-free testing, but generates synthesized structural responses rather than dynamic natural language explanations.
