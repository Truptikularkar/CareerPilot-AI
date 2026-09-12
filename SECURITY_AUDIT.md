# CareerPilot AI — Security & Privacy Audit Report

**Audit Date:** August 31, 2026  
**Auditor:** Automated Production Hardening Suite (Milestone 9)  
**Classification:** Public / Open-Source Architecture Review  
**System Version:** 1.0.0  

---

## 1. Executive Summary

CareerPilot AI is designed around a strict zero-fabrication and candidate privacy architecture. This document certifies that private candidate credentials, personally identifiable information (PII), and internal runtime state are decoupled from the public codebase and protected by deterministic validation layers.

---

## 2. PII & Ground-Truth Data Isolation

| Data Category | Storage Location | Public Git Exposure | Protection Mechanism |
| :--- | :--- | :--- | :--- |
| **Verified Candidate Data** | `data/candidate/`, `data/private/` | **NEVER (Excluded)** | Strictly gitignored via `.gitignore` rule: `data/private/`, `data/candidate/` |
| **Synthetic Demo Data** | `data/demo/` | **Public (Safe)** | 100% fictional candidate profile (Alex Rivera) with generic synthetic metrics |
| **Job Descriptions Uploaded** | `data/uploads/` | **NEVER (Excluded)** | Stored in isolated scratch directory, excluded from version control |
| **Generated Resumes (DOCX/MD)**| `data/generated/resumes/` | **NEVER (Excluded)** | Gitignored; ephemeral storage |
| **Mock Interview Recordings** | `data/generated/interview_sessions/` | **NEVER (Excluded)** | Gitignored; local SQLite persistence only |
| **Local Vector Embeddings** | `data/chroma_db/`, `data/demo/chroma_db/` | **NEVER (Excluded)** | Gitignored binary/JSON database files |
| **Relational Database** | `data/careerpilot.db` | **NEVER (Excluded)** | Excluded via `*.db`, `*.sqlite` rules |

---

## 3. Secret & Credential Management

1. **Environment Variables & Secrets:**
   - Secrets are loaded dynamically using `pydantic-settings` from `.env` or Streamlit Cloud `st.secrets`.
   - `.env` is explicitly gitignored. An sanitized `.env.example` is provided with all keys blank.
2. **API Key Masking:**
   - The UI and health diagnostics never print raw API keys. The helper property `settings.masked_gemini_key` formats keys as `AIza...****`.
3. **Offline Fallback Guarantee:**
   - If no `GEMINI_API_KEY` is provided, the application seamlessly defaults to deterministic offline heuristics and `MockLLMProvider` with zero network calls or crashes.

---

## 4. File Upload & Ingestion Security

- **File Type Restrictions:** Only `.txt` and `.pdf` extensions are accepted. Executables (`.exe`), scripts (`.py`, `.sh`), and arbitrary binary formats are blocked immediately.
- **Maximum File Size:** Enforced 5 MB hard limit (`settings.MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024`) preventing denial-of-service (DoS) or memory exhaustion.
- **Path Traversal Defenses:** Uploaded files are assigned cryptographically random UUID identifiers before persisting into `data/uploads/`.

---

## 5. Truth Guard & Anti-Fabrication Safeguards

- **Strict Source Verification:** Every bullet point on generated resumes and every factual claim in interview preparation is cross-referenced against the Candidate Evidence Store.
- **Project Boundary Enforcement:** Personal sandbox projects (e.g., local RAG engines) are prevented from being framed as enterprise client production experience.
- **Transferable Skill Framing:** Cross-cloud technologies (e.g., AWS Redshift when the candidate has verified GCP BigQuery experience) are explicitly tagged as *Transferable Conceptual Knowledge* rather than direct production tenure.

---

## 6. Audit Verdict

✅ **PASS — Production Hardening & Security Compliant**  
CareerPilot AI satisfies all open-source distribution, data isolation, and deployment security criteria.
