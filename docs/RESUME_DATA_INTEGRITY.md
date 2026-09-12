# CareerPilot AI — Resume Data Integrity & Anti-Hallucination Specification

## 1. Principles of Resume Grounding

CareerPilot is built on a strict **zero-hallucination, evidence-grounded contract**:

1. **No Factual Fabrication**: The LLM is never allowed to fabricate companies, titles, dates, colleges, degrees, GPA/honors, certifications, or production metrics.
2. **Deterministic Information Flow**: Factual data originates exclusively from the approved `CandidateProfile` in SQLite.
3. **Strict Isolation of Experience Tiers**: Personal projects (`PERSONAL_PROJECT`) are strictly segregated from professional client experience (`PROFESSIONAL_EXPERIENCE`).
4. **Truth Guard Gate**: Every tailored resume is subjected to the `TruthGuard` validator before being approved for ATS evaluation and PDF/DOCX compilation.

---

## 2. Canonical vs. Generative Boundaries

| Section | Canonical Factual Fields (Zero LLM Freedom) | Permitted Generative Refinement |
| :--- | :--- | :--- |
| **Header** | Full name, phone, email, location, LinkedIn URL, GitHub URL | None. Verbatim from active profile. |
| **Summary** | Stated experience duration (calculated from dates), candidate target title | Keyword alignment to target job description. |
| **Skills** | Technical skills, evidence levels (`PROFESSIONAL`, `PERSONAL_PROJECT`) | Category reordering based on target strategy. |
| **Experience** | Company name, job title, start/end dates, location | Bullet phrasing alignment to JD keywords (grounded in verified evidence). |
| **Projects** | Project name, classification, technologies, verified metrics | Selecting top 2 relevant projects; phrasing alignment. |
| **Education** | Institution, degree, field of study, graduation year, CGPA | None. Verbatim from active profile. |
| **Certifications** | Certification name, issuer, year | None. Verbatim from active profile. |

---

## 3. Truth Guard Validation Pipeline

```
┌────────────────────────────────┐
│ TailoredResume Content Object  │
└───────────────┬────────────────┘
                │
                ▼
┌────────────────────────────────┐
│ TruthValidator Validation Pass │
│ ├── Company & Title Check      │
│ ├── Education Fidelity Check   │
│ ├── Employment Date Verification│
│ ├── Metric Immutability Audit  │
│ └── Personal Project Isolation │
└───────────────┬────────────────┘
                │
        ┌───────┴───────┐
        ▼               ▼
    [ PASS ]        [ FAIL / VIOLATION ]
        │               │
        │               └──► Block Export & Generate Actionable Warnings
        ▼
┌────────────────────────────────┐
│ Approved Resume Artifacts      │
│ (1-Page PDF & ATS DOCX)        │
└────────────────────────────────┘
```
