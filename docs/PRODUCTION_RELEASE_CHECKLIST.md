# CareerPilot AI — Production Release Checklist

This document tracks the authoritative production readiness audit for CareerPilot AI across all 27 critical release domains.

---

### Release Verification Status

- [x] **1. Authentication**
  - Email/password user registration and login enabled via `AuthService`.
  - Streamlit authentication gatekeeper (`AuthService.require_auth()`) protects `app.py` and all 12 pages in `careerpilot/ui/pages/`.
  - Multi-device login selector ("Laptop / Desktop" vs. "Mobile Phone").

- [x] **2. Authorization & Tenant Scoping**
  - All applications, resumes, candidate profiles, and external accounts are scoped strictly to `candidate_id` / `user_id`.
  - Unauthorized cross-user mutation or access raises `PermissionError`.

- [x] **3. Password Security**
  - RFC 9106 Argon2id password hashing implemented via `argon2-cffi` (`$argon2id$v=19$m=65536,t=3,p=4`).
  - Strict password strength enforcement (10+ chars, uppercase, lowercase, digit, special character).
  - Passwords are never logged, cached, or stored in plaintext.

- [x] **4. Session Security**
  - Cryptographic session tokens generated via `secrets.token_urlsafe(32)` (min 32 bytes entropy).
  - Stored exclusively as SHA-256 token hashes (`token_hash`) in `UserSessionDB`.
  - Concurrent multi-device sessions supported; single-device logout invalidates only the caller's session token; password changes support revoking all other sessions.

- [x] **5. Candidate Data Isolation**
  - Zero hardcoded candidate identities in production paths.
  - Dynamically resolves candidate profile and contact details from active SQLite store.

- [x] **6. Gemini Live Provider Architecture**
  - Leverages official `google.genai` SDK with `gemini-3.6-flash`.
  - Silent mock fallbacks strictly prohibited in `LOCAL_PRIVATE` and production modes (`RuntimeError` raised if provider unavailable).

- [x] **7. GitHub Security & Connector**
  - Uses Windows-compatible CA certificate verification bundle (`certifi.where()`).
  - Strict classification of ingested repositories as `PERSONAL_PROJECT` candidate evidence upon user approval.

- [x] **8. LinkedIn Compliance**
  - Zero-scraping architecture: automated web scraping of LinkedIn is strictly disabled to prevent Terms of Service violations and IP blocks.
  - Official manual CSV archive import parses verified profile history.

- [x] **9. Naukri Compliance**
  - Zero-scraping architecture: official manual formatted text parser ingests verified candidate profile data without scraping.

- [x] **10. Explainable Job Decisions & 0% Transparency**
  - Pure deterministic fact-to-explanation service (`careerpilot/services/explanation_service.py`).
  - Every analyzed job produces overall score, decision reason, matching skills, missing required skills, preferred gaps, experience comparison, cloud comparison, and next action.
  - Jobs scored 0% produce explicit `primary_skip_reason`, `blocking_requirements`, and `next_action`.

- [x] **11. Truth Guard Verification**
  - Anti-hallucination engine validates tailored resumes and AI explanations against verified candidate evidence.
  - Prohibits tenure exaggeration, unverified cloud claims (e.g. AWS production), and metric fabrication.
  - Safely falls back to deterministic templates if AI generation fails or violates verified ground truth.

- [x] **12. Resume Generation & Guaranteed 1-Page Engine**
  - Adaptive 3-pass layout engine with PyMuPDF verification guarantees 1-page PDF resumes for early-career profiles (<3 years).
  - DOCX, PDF, and Markdown formats generated dynamically with sanitized candidate filenames.

- [x] **13. ATS Compatibility Engine**
  - Simple, professional user terminology: "JD keyword match", "Missing important keywords", "Formatting & layout standards".
  - Keyword repetition within safe natural density limits (<3.5%).

- [x] **14. Interview Preparation**
  - Questions framed with "Why this question matters", "What the interviewer is checking", and "Relevant candidate experience".
  - Multi-length answer generation (Short 30-45s, Standard 60-90s, Detailed 2-3m).

- [x] **15. Adaptive Mock Interview**
  - Adaptive difficulty progression, real-time rubric scoring across technical accuracy, structure, and evidence grounding.
  - Final comprehensive performance report with actionable coaching tips.

- [x] **16. 17-Stage Application Lifecycle**
  - Authoritative `ApplicationStatus` recruitment lifecycle with user-friendly display labels (`Found`, `Analyzed`, `Saved`, `Applied`, `Employer responded`, `Screening`, `Online assessment`, `Technical interview`, `HR interview`, `Final interview`, `Offer`, `Accepted`, `Rejected`, `Withdrawn`, `On hold`, `No response`).

- [x] **17. Career Intelligence & Funnel Analytics**
  - Conversion rates, pipeline metrics, and market skill demand trends computed and scoped per candidate.

- [x] **18. RAG Persistence & Re-Hydration**
  - ChromaDB collections derived safely from canonical database evidence.
  - Automatic index rebuild from SQLite ground truth if Chroma vector directory is empty or clean.

- [x] **19. Database & Multi-Tenant Persistence**
  - SQLite supported for `LOCAL_PRIVATE`.
  - `HOSTED_PRIVATE` mode validates persistent storage (`DATABASE_URL` or `PERSISTENT_VOLUME_PATH`), preventing silent data loss on ephemeral container filesystems.

- [x] **20. Streamlit Deployment Readiness**
  - Clean entrypoint (`streamlit run careerpilot/ui/app.py`).
  - No local absolute Windows machine paths or OneDrive-specific path assumptions.
  - Responsive multi-device layout (tested on laptop and mobile viewports).

- [x] **21. Secrets Management**
  - Zero hardcoded credentials or API keys committed in repository.
  - `.env.example` provided with placeholder names only.

- [x] **22. Professional User-Facing Language & UI Polish**
  - Banned confusing AI/engineering jargon from normal user views (`Fit Score`, `Why this job matches`, `Missing required skills`, `Experience gap`, `Your strengths`, `Next step`).
  - Polished dashboard focusing on actionable search intelligence.

- [x] **23. Error Handling & State Feedback**
  - Raw Python exceptions intercepted in normal UI and replaced with polite, actionable user guidance.
  - Explicit loading spinners, success messages, and failure alerts on all primary actions.

- [x] **24. Logging & Diagnostics**
  - Structured logging via standard Python logging module with configurable `LOG_LEVEL`.
  - Detailed tracebacks logged to server diagnostics while remaining hidden from normal end-users.

- [x] **25. Backup & Recovery Strategy**
  - SQLite database backup via file copy or SQLAlchemy dump.
  - Canonical evidence ledger guarantees complete resume and RAG index reconstruction.

- [x] **26. Automated Test Suite & Regression**
  - Comprehensive unit, integration, and end-to-end tests across all system components.
  - 100% test pass rate with zero regressions.

- [x] **27. Documentation Integrity**
  - Updated architectural guides, milestone reports, and deployment instructions reflecting verified system capabilities.
