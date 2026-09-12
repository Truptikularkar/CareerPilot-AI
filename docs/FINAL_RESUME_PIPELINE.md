# CareerPilot AI — Final Resume Pipeline Architecture

**Document Version:** 2.0  
**Scope:** Complete end-to-end architecture from Candidate Profile to ATS-safe PDF/DOCX generation.

---

## 1. End-to-End Pipeline Diagram

```mermaid
flowchart TD
    CP[Candidate Profile\n(Experience, Projects, Skills, Preferences)] -->|EvidenceExtractor.atomize()| VE[Verified Candidate Evidence\n(Atomic Claims & Verification Status)]
    VE -->|Upsert & Index| CRAG[Candidate RAG / Vector Store\n(ChromaDB Collection: candidate_evidence)]

    JD[Target Job Description\n(Text / PDF / Upload)] -->|JobAnalysisGraph| JA[Job Analysis Result\n(Role Class, Seniority, Fit Score, Risks)]

    CRAG -->|Retrieve Evidence Chunks| RS[Resume Strategy Selection\n(AI Data Eng, Data Eng, GenAI Eng)]
    JA --> RS

    RS -->|Bullet Assembly & Prioritization| TR[TailoredResume\n(Pure Content Domain Model)]

    TR -->|Anti-Hallucination Gate| TG[Truth Guard\n(Strict Claim & Metric Verification)]

    TG -->|Truth-Audited Resume| ATS[ATS Evaluator\n(Deterministic 6-Component Compatibility Score)]

    ATS -->|TailoredResume + ATSReport| RAS[Resume Artifact Service\n(CareerPilotService.get_or_generate_resume_artifacts)]

    RAS -->|PDFResumeExporter| PDF[PDF Artifact\n(Single-Column, ATS-Clean, Vector Searchable)]
    RAS -->|DocxResumeExporter| DOCX[DOCX Artifact\n(Tableless, Semantic Headings & Bullets)]

    PDF --> SD[Streamlit Download Boundary\n(st.download_button via ResumeArtifact.get_bytes())]
    DOCX --> SD
```

---

## 2. Step-by-Step Data Transformation Flow

### Step 1: Candidate Profile & Atomic Evidence
1. The candidate profile is managed through `CandidateProfile` in SQLite (`candidate_profiles`).
2. Any profile update (e.g. adding a personal project or verified skill) triggers `EvidenceExtractor.atomize_candidate_profile()`.
3. Every bullet, metric, and skill is atomized with an `evidence_level` (`PROFESSIONAL`, `PERSONAL_PROJECT`, `LEARNING_KNOWLEDGE`) and `evidence_status` (`VERIFIED`, `PARTIAL`).
4. Chunks are embedded and indexed into ChromaDB (`candidate_evidence` collection).

### Step 2: Job Description Parsing & Fit Analysis
1. The user inputs a JD into `2_Analyze_Job.py`.
2. `JobAnalysisGraph` detects seniority, classifies the real role category, maps cloud transferability (e.g., GCP $\rightarrow$ AWS), and scores candidate-job fit.
3. The result is saved to `job_analyses` and an `Application` record is created.

### Step 3: Strategy Selection & Resume Drafting
1. When the user requests a tailored resume in `4_Resume_Builder.py`, `ResumeGraph` triggers.
2. `StrategySelectorNode` chooses the optimal strategy (or respects manual override).
3. `CandidateStore` retrieves the most relevant verified evidence chunks for each target requirement.
4. `BulletSelectorNode` drafts the experience bullets, highlighting verified metrics (e.g. `~25% cost reduction`, `~35% incident reduction`).

### Step 4: Truth Guard Anti-Hallucination Gate
1. `TruthGuardNode` inspects every claim in the draft:
   - Verifies all numerical metrics against candidate ground truth.
   - Ensures technologies mentioned have verified evidence.
   - Enforces strict isolation: personal projects (`PERSONAL_PROJECT`) are never included under professional work experience (`PROFESSIONAL_EXPERIENCE`).
2. Generates a `TruthValidationReport` attached to `TailoredResume.truth_report`.

### Step 5: ATS Evaluation & Precheck
1. `ATSEvaluator.evaluate_resume()` scores the exact `TailoredResume` across 6 dimensions:
   - Keyword & Requirement Coverage (25%)
   - Skill Taxonomy Alignment (20%)
   - Semantic Role Alignment (20%)
   - Experience & Seniority Alignment (15%)
   - Resume Structure & Completeness (10%)
   - Formatting & Layout Compatibility (10%)
2. Produces an `ATSReport` with an overall score (0–100%) and requirement coverage matrix.

### Step 6: Decoupled Artifact Generation & Download
1. `CareerPilotService.get_or_generate_resume_artifacts()` takes the `TailoredResume` and renders:
   - **`resume.pdf`** via `PDFResumeExporter`: Single-column layout, standard margins, Helvetica typography, 100% selectable text.
   - **`resume.docx`** via `DocxResumeExporter`: Tableless Word document with standard paragraph styles.
   - **`resume.md`** via `MarkdownResumeExporter`: Plain text markdown version.
2. The artifacts are encapsulated in a `ResumeArtifactBundle` containing `ResumeArtifact` instances.
3. The UI presents clean, one-click download buttons using `ResumeArtifact.get_bytes()`.
