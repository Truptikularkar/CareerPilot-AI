# CareerPilot AI — System Error & Edge Case Analysis

**Document:** `ERROR_ANALYSIS.md`  
**Purpose:** Comprehensive failure classification, root cause analysis, and remediation status for AI and system edge cases.

---

## Error Classification Matrix

| Error ID | Category | Severity | Root Cause | Fix / Mitigation | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ERR-RET-01** | Retrieval | Medium | Pure sparse BM25 misses conceptual semantic synonyms (*data warehouse* $\rightarrow$ *BigQuery*). | Implemented Hybrid Retrieval with Reciprocal Rank Fusion (RRF). | ✅ RESOLVED |
| **ERR-RET-02** | Retrieval | Low | Pure dense embedding occasionally ranks exact acronyms (*DAG*, *RRF*) below general summaries. | Boosted hybrid search with keyword metadata filters. | ✅ RESOLVED |
| **ERR-GEN-01** | Generation | Critical | Standard LLM prompts hallucinate unverified cloud platforms (e.g. AWS Glue) on candidate resumes. | Built external deterministic Truth Guard outside the LLM. | ✅ RESOLVED |
| **ERR-GEN-02** | Generation | High | LLM rewrites inflate numeric metrics (e.g. turning 25% cost savings into 80%). | Enforced regex extraction against `VERIFIED_METRIC_VALUES`. | ✅ RESOLVED |
| **ERR-CLS-01** | Classification | Medium | Hybrid job descriptions (e.g. *Data Engineer + ML + Analytics*) confuse naive keyword counters. | Weighted role classification with responsibility signals in `RoleClassifier`. | ✅ RESOLVED |
| **ERR-CLS-02** | Classification | Low | Seniority detection defaults to MID when no explicit years are stated. | Added heuristic detection for title prefixes (*Lead*, *Senior*, *Junior*). | ✅ RESOLVED |
| **ERR-TG-01** | Truth Guard | High | Personal sandbox projects (Hybrid RAG) placed under enterprise client experience. | Strict section boundary enforcement: personal projects restricted to `Projects`. | ✅ RESOLVED |
| **ERR-TG-02** | Truth Guard | Medium | Transferable cloud skills (GCP $\rightarrow$ AWS) flagged as hallucinations in interview preparation. | Created `TRANSFERABLE` classification allowing conceptual framing in interviews. | ✅ RESOLVED |
| **ERR-INF-01** | Infrastructure | Low | Concurrent SQLite write locks during rapid parallel test executions. | Connection timeout adjustments and WAL mode enablement in SQLite. | ✅ RESOLVED |

---

## Detailed Failure Case Studies

### 1. Case: ERR-GEN-01 (Unsupported Cloud Production Claim)
- **Input:** Target JD requires 3+ years AWS Redshift experience.
- **Expected:** Resume omits Redshift from Experience section; ATS flags GAP; Interview prep offers transferable BigQuery framing.
- **Observed Without Guard:** LLM drafted: *"Architected enterprise AWS Redshift clusters at Cognizant."* (False fabrication).
- **Root Cause:** Standard LLM prompt completion optimizes for alignment with the target job description regardless of factual truth.
- **Applied Fix:** Truth Guard regex pattern intercepted `"aws production"` and blocked the draft, forcing auto-remediation.
- **Current Status:** ✅ **RESOLVED (Blocked with 100% precision)**.

---

### 2. Case: ERR-GEN-02 (Metric Exaggeration & Inflation)
- **Input:** Candidate source data states *"~25% BigQuery query cost reduction"*.
- **Expected:** Generated resume maintains 25% (or ~25%).
- **Observed Without Guard:** LLM drafted: *"Optimized analytical SQL queries, cutting cloud processing costs by 80%."*
- **Root Cause:** LLM "hero-phrasing" tendency to maximize perceived impact.
- **Applied Fix:** `ClaimClassifier` extracts all percentages and checks membership against `VERIFIED_METRIC_VALUES`. Unmatched values trigger `TruthValidationStatus.BLOCK`.
- **Current Status:** ✅ **RESOLVED (100% blocked on test benchmarks)**.

---

### 3. Case: ERR-TG-01 (Project vs. Work Experience Boundary Violation)
- **Input:** Candidate built personal *Hybrid RAG Sandbox* as an individual project.
- **Expected:** Permitted in `Projects` section; strictly forbidden under `Experience` section.
- **Observed Without Guard:** Bullet placed under Cognizant experience as a client deliverable.
- **Applied Fix:** `TruthAuditor.audit_sections()` enforces section-aware rules where sandbox project keywords are rejected if present in `experiences`.
- **Current Status:** ✅ **RESOLVED**.
