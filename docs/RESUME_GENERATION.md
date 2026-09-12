# CareerPilot AI — Tailored ATS-Friendly Resume Generation & Artifact Architecture

**Document:** `docs/RESUME_GENERATION.md`  
**Purpose:** End-to-end technical documentation of the evidence-grounded resume tailoring, Truth Guard validation, ATS compatibility evaluation, decoupled `ResumeArtifact` architecture, and dual format export (DOCX + PDF).

---

## 1. Architectural Overview & Workflow

CareerPilot AI generates strategy-aligned, ATS-optimized resumes strictly grounded in verified candidate evidence.

```
                      Job Description (JD)
                                │
                                ▼
                   [Job Analysis & Fit Scoring]
                                │
                                ▼
                    [Resume Strategy Selection]
         (AI_DATA_ENGINEER, DATA_ENGINEER, GENAI_ENGINEER, GCP_DATA_ENGINEER)
                                │
                                ▼
                  [Candidate Evidence Retrieval]
                 (Dual-Store ChromaDB + BM25 RAG)
                                │
                                ▼
                    [Tailored Resume Drafting]
             (Summary + Skills + Experience + Projects + Education)
                                │
                                ▼
                       [Truth Guard Audit]
                 (Deterministic Anti-Hallucination Gate)
                   ├── IF BLOCK ──► Halt artifact generation
                   └── IF PASS  ──► Proceed to ATS & Artifact Generation
                                      │
                                      ▼
                        [ATS Compatibility Evaluation]
                        (7-Component Explainable Scoring)
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │   TailoredResume (Domain) │
                        └─────────────┬─────────────┘
                                      │
               ┌──────────────────────┴──────────────────────┐
               ▼                                             ▼
       [DocxResumeExporter]                          [PDFResumeExporter]
               │                                             │
               ▼                                             ▼
       ResumeArtifact (.docx)                        ResumeArtifact (.pdf)
               │                                             │
               └──────────────────────┬──────────────────────┘
                                      ▼
                            [ResumeArtifactBundle]
                                      │
                                      ▼
                        Streamlit UI Download Buttons
                 (Direct binary streaming with validation)
```

---

## 2. Decoupled Domain Model vs. Artifact Architecture

A foundational design principle of CareerPilot AI is the strict separation between domain content and filesystem I/O:

- **`TailoredResume` represents RESUME CONTENT:**
  Pure domain model containing structured candidate data (`header`, `summary`, `skills_categories`, `experiences`, `projects`, `education`, `certifications`, `truth_report`, `ats_precheck`). It contains **no** required filesystem path fields or runtime I/O logic.
- **`ResumeArtifact` represents GENERATED FILES:**
  Dedicated artifact model encapsulating generated outputs (`artifact_type`, `file_name`, `file_path`, `content_type`, `file_bytes`, `resume_id`, `is_valid`, `validation_message`).
  Implements `os.PathLike`, `get_bytes()`, `read_bytes()`, `read_text()`, and `exists()`.
- **`ResumeArtifactBundle` represents ALL GENERATED ARTIFACTS:**
  A container holding `pdf: Optional[ResumeArtifact]`, `docx: Optional[ResumeArtifact]`, and `markdown: Optional[ResumeArtifact]`.

---

## 3. Exporter Contracts

Each format exporter takes a `TailoredResume` and optional target path, and returns a validated `ResumeArtifact`:

```python
# PDF Exporter (ReportLab)
pdf_artifact: ResumeArtifact = PDFResumeExporter.export_pdf(
    resume=tailored_resume,
    output_path="data/generated/resumes/{id}/resume.pdf",
    company="CognitiveScale Labs",
)

# DOCX Exporter (python-docx)
docx_artifact: ResumeArtifact = DocxResumeExporter.export_docx(
    resume=tailored_resume,
    output_path="data/generated/resumes/{id}/resume.docx",
    company="CognitiveScale Labs",
)

# Markdown Exporter
md_artifact: ResumeArtifact = MarkdownResumeExporter.export_markdown(
    resume=tailored_resume,
    output_path="data/generated/resumes/{id}/resume.md",
    company="CognitiveScale Labs",
)
```

---

## 4. Role Strategy & Tailoring Approach

The resume tailoring engine does **not** alter the candidate's historical employment record or fabricate unverified tools. Instead, it dynamically reconfigures emphasis, bullet ordering, project selection, and skill categorization based on the target role:

- **`AI_DATA_ENGINEER` Strategy:**
  - **Summary Emphasis:** Bridges production data pipelines (ETL/ELT, Airflow, BigQuery) with Generative AI / RAG workflows.
  - **Bullet Ordering:** Prioritizes validation frameworks, data quality monitoring, and automated pipeline orchestration.
  - **Project Priority:** Highlights Vertex AI Agentic Ticket Resolution and Hybrid RAG Sandbox.
- **`DATA_ENGINEER` Strategy:**
  - **Summary Emphasis:** Core high-throughput data engineering, SQL query optimization, partitioning, and automated DAG scheduling.
  - **Bullet Ordering:** Emphasizes BigQuery cost reductions (25%) and schema reconciliation.
- **`GENAI_ENGINEER` Strategy:**
  - **Summary Emphasis:** Vector retrieval, embeddings, chunking strategies, and LLM evaluation.
- **`GCP_DATA_ENGINEER` Strategy:**
  - **Summary Emphasis:** Native GCP stack (BigQuery, Cloud Storage, Pub/Sub, Cloud Functions).

---

## 5. Truth Guard Integration & Anti-Hallucination Standards

Before any DOCX or PDF file is generated, the resume draft is audited by the `TruthValidator`:

1. **Deterministic Claim Extraction:** Every bullet, project claim, and summary statement is scanned for numeric metrics, technology keywords, and tenure assertions.
2. **Ground Truth Matching:** Claims are matched against the candidate's immutable ground truth (`data/candidate/`).
3. **Hard Blocking Violations:**
   - Exaggerated metrics (e.g., claiming 50% instead of verified 25%).
   - Unsupported production technologies (e.g., claiming AWS EKS production management when candidate only has verified GCP experience).
   - Tenure inflation (e.g., claiming 5+ years of experience for a 1.9+ year candidate).
4. **Enforcement Gate:** If `truth_report.status == TruthValidationStatus.BLOCK`, the export node halts and **no** final PDF or DOCX resume is generated.

---

## 6. ATS-Friendly PDF Formatting Specifications

The PDF generator (`careerpilot/generators/resume_pdf.py`) uses ReportLab with strict ATS-compliant styling:

| Feature | ATS Requirement | CareerPilot Implementation |
| :--- | :--- | :--- |
| **Column Layout** | Single-column linear text flow | `SimpleDocTemplate` without columns or sidebars |
| **Typography** | Standard, universal fonts | `Helvetica`, `Helvetica-Bold`, `Helvetica-Oblique` (18pt Name, 11.5pt Headings, 9.5pt Body) |
| **Text Selectability** | 100% searchable / selectable text | TrueType / Type 1 vector text with ToUnicode CMaps |
| **Visual Elements** | Zero decorative graphics or images | Clean horizontal rule divider (`HRFlowable`), no canvas overlays |
| **Tables** | No multi-column tables for content | Linear paragraph flow with bullet indents (`leftIndent=14`, `firstLineIndent=-10`) |
| **Margins** | Conservative, printable bounds | 0.55 in (39.6 pt) margins on all four sides |
| **Filename** | Filesystem-safe, clean naming | `PDFResumeExporter.get_safe_filename()` sanitizing `/ \ : * ? " < > \|` |

---

## 7. Deterministic PDF Validation

The `PDFValidator` (`careerpilot/generators/pdf_validator.py`) inspects the generated binary using PyMuPDF (`fitz`):

1. **Extractability Check:** Verifies total character count (> 50 chars) and word count.
2. **Candidate Identity:** Confirms full candidate name is present in extracted text.
3. **Section Headings:** Audits required headings (`PROFESSIONAL SUMMARY`, `TECHNICAL SKILLS`, `PROFESSIONAL EXPERIENCE`, `KEY PROJECTS`, `EDUCATION`).
4. **Layout Check:** Verifies no overlapping side-by-side text blocks.
5. **Searchability Check:** Verifies that keywords (e.g. `Python`, `SQL`, `BigQuery`, `Airflow`, `GCP`) can be located via text search.

---

## 8. Streamlit Download Workflow

In `careerpilot/ui/pages/4_Resume_Builder.py`:
1. Candidate selects target application and tailoring strategy.
2. Clicks **✨ Generate Tailored Resume**.
3. Service executes LangGraph workflow $\rightarrow$ Truth Guard audit $\rightarrow$ ATS evaluation $\rightarrow$ builds `ResumeArtifactBundle`.
4. Stored cleanly in session state as `(resume, ats_report, artifacts)`.
5. Export tab presents direct download buttons powered by `artifact.get_bytes()`:
   - `⬇️ Download ATS Clean DOCX` (MIME: `application/vnd.openxmlformats-officedocument.wordprocessingml.document`)
   - `⬇️ Download ATS Clean PDF` (MIME: `application/pdf`)
6. Real-time validation badges confirm ATS compliance before download.
