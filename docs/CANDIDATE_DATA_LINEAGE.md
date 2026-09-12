# CareerPilot AI — Candidate Data Lineage Specification

## 1. Executive Summary & Authoritative Principle

In CareerPilot AI, **the Candidate Profile stored in SQLite (`candidate_profiles`) is the sole, authoritative source of truth** for candidate biographical, educational, professional, and technical facts.

> [!IMPORTANT]
> The LLM and generative pipelines are **strictly forbidden** from inventing, modifying, estimating, or reinterpreting factual candidate details (college names, degrees, graduation years, employment dates, company names, job titles, project classifications, and verified metrics).

---

## 2. End-to-End Data Lineage Map

```
                    ┌───────────────────────────────────────┐
                    │ Candidate Profile UI                  │
                    │ (`careerpilot/ui/pages/9_Profile.py`) │
                    └───────────────────┬───────────────────┘
                                        │ (Direct user edits / merges)
                                        ▼
                    ┌───────────────────────────────────────┐
                    │ `CandidateProfile` (Pydantic Model)   │
                    │ (`careerpilot/models/candidate.py`)   │
                    └───────────────────┬───────────────────┘
                                        │ (Persistence & Versioning)
                                        ▼
                    ┌───────────────────────────────────────┐
                    │ `CandidateRepository` (SQLite DB)     │
                    │ `candidate_profiles` Table            │
                    └───────────────────┬───────────────────┘
                                        │
                    ┌───────────────────┴───────────────────┐
                    │                                       │
                    ▼                                       ▼
    ┌───────────────────────────────┐       ┌───────────────────────────────┐
    │ `EvidenceExtractor`           │       │ `BulletSelector` & Generator  │
    │ (Atomizes verified facts)     │       │ (Loads SQLite profile facts)  │
    └───────────────┬───────────────┘       └───────────────┬───────────────┘
                    │                                       │
                    ▼                                       ▼
    ┌───────────────────────────────┐       ┌───────────────────────────────┐
    │ `CandidateStore` (ChromaDB)   │       │ `TailoredResume` Model        │
    │ (Semantic vector retrieval)   │       │ (Pure content representation) │
    └───────────────┬───────────────┘       └───────────────┬───────────────┘
                    │                                       │
                    └───────────────────┬───────────────────┘
                                        │
                                        ▼
                    ┌───────────────────────────────────────┐
                    │ `TruthGuard` Anti-Hallucination Gate  │
                    │ (Validates against atomic evidence)   │
                    └───────────────────┬───────────────────┘
                                        │
                                        ▼
                    ┌───────────────────────────────────────┐
                    │ `ATSEvaluator` (Score & Coverage)     │
                    └───────────────────┬───────────────────┘
                                        │
                                        ▼
                    ┌───────────────────────────────────────┐
                    │ `ResumeArtifactService`               │
                    │ ├── `PDFResumeExporter` (1-Page ATS)  │
                    │ └── `DocxResumeExporter` (1-Page ATS) │
                    └───────────────────────────────────────┘
```

---

## 3. Comprehensive Field-by-Field Data Lineage Catalog

| Field | Canonical Source | Database Field (`candidate_profiles`) | Model Field (`CandidateProfile`) | Service Layer | RAG Ingestion | Resume Consumer | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **`full_name`** | Profile UI / `profile.yaml` | `full_name` | `full_name: str` | `CandidateService` | Embedded in header | `ResumeHeader.full_name` | ✅ **Exact** |
| **`email`** | Profile UI / `profile.yaml` | `email` | `email: Optional[str]` | `CandidateService` | Evidence metadata | `ResumeHeader.email` | ✅ **Exact** |
| **`phone`** | Profile UI / `profile.yaml` | `phone` | `phone: Optional[str]` | `CandidateService` | Evidence metadata | `ResumeHeader.phone` | ✅ **Exact** |
| **`location`** | Profile UI / `profile.yaml` | `location` | `location: Optional[str]` | `CandidateService` | Evidence metadata | `ResumeHeader.location` | ✅ **Exact** |
| **`linkedin_url`** | Profile UI / `profile.yaml` | `linkedin_url` | `linkedin_url: Optional[str]` | `CandidateService` | Evidence metadata | `ResumeHeader.linkedin_url` | ✅ **Exact** |
| **`github_url`** | Profile UI / `profile.yaml` | `github_url` | `github_url: Optional[str]` | `CandidateService` | Evidence metadata | `ResumeHeader.github_url` | ✅ **Exact** |
| **`degree`** | Profile UI / `profile.yaml` | `education_json` | `education[].degree` | `CandidateService` | Chunked in `cand_ev` | `ResumeEducationEntry.degree` | ✅ **Exact** |
| **`field_of_study`** | Profile UI / `profile.yaml` | `education_json` | `education[].field_of_study` | `CandidateService` | Chunked in `cand_ev` | `ResumeEducationEntry.field_of_study` | ✅ **Exact** |
| **`institution` (College)** | Profile UI / `profile.yaml` | `education_json` | `education[].institution` | `CandidateService` | Chunked in `cand_ev` | `ResumeEducationEntry.institution` | ✅ **Exact** |
| **`graduation_year`** | Profile UI / `profile.yaml` | `education_json` | `education[].graduation_year` | `CandidateService` | Chunked in `cand_ev` | `ResumeEducationEntry.graduation_year` | ✅ **Exact** |
| **`cgpa` / `honors`** | Profile UI / `profile.yaml` | `education_json` | `education[].gpa_or_honors` | `CandidateService` | Chunked in `cand_ev` | `ResumeEducationEntry.honors` | ✅ **Exact** |
| **`company`** | Profile UI / `experience.md` | `experiences_json` | `experiences[].company` | `CandidateService` | Chunked in `cand_ev` | `ResumeExperienceEntry.company` | ✅ **Exact** |
| **`job_title`** | Profile UI / `experience.md` | `experiences_json` | `experiences[].title` | `CandidateService` | Chunked in `cand_ev` | `ResumeExperienceEntry.title` | ✅ **Exact** |
| **`employment_start`** | Profile UI / `experience.md` | `experiences_json` | `experiences[].start_date` | `CandidateService` | Chunked in `cand_ev` | `ResumeExperienceEntry.start_date` | ✅ **Exact** |
| **`employment_end`** | Profile UI / `experience.md` | `experiences_json` | `experiences[].end_date` | `CandidateService` | Chunked in `cand_ev` | `ResumeExperienceEntry.end_date` | ✅ **Exact** |
| **`total_experience`** | Calculated from dates | Derived deterministically | `calculate_total_experience_years()` | `date_utils.py` | Metadata | `ResumeSummary.experience_years_stated` | ✅ **Deterministic** |
| **`projects`** | Profile UI / `projects.md` | `projects_json` | `projects[].*` | `CandidateService` | Atomized into chunks | `ResumeProjectEntry` (Top 2 for 1-page) | ✅ **Exact & Prioritized** |
| **`skills`** | Profile UI / `skills.md` | `skills_json` | `skills[].*` | `CandidateService` | Tagged with evidence levels | `ResumeSkillCategory` (Categorized) | ✅ **Exact & Categorized** |
| **`certifications`** | Profile UI / `profile.yaml` | `certifications_json` | `certifications: List[str]` | `CandidateService` | Chunked in `cand_ev` | `ResumeCertificationEntry` | ✅ **Exact** |
| **`achievements`** | Profile UI / `achievements.md`| `achievements_json` | `achievements[].*` | `CandidateService` | Chunked in `cand_ev` | `ResumeBullet` / Strategy anchor | ✅ **Exact** |

---

## 4. Precedence Hierarchy

1. **Approved Candidate Profile** (SQLite Database) — Highest Precedence.
2. **Atomic Candidate Evidence** (Verified ground truth chunks).
3. **Candidate Vector Store** (ChromaDB `candidate_evidence`).
4. **Target Job Description** (Filter & relevance ranker).
5. **LLM Phrasing Assistance** (Only permitted for grammatical refinement of verified claims; never for factual generation).
