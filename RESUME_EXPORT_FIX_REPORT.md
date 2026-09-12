# CareerPilot AI — Resume Export & Streamlit Download Architecture Fix Report

**Date:** 2026-08-31  
**Status:** **100% COMPLETE & VERIFIED (157 / 157 PyTest Tests Passing)**

---

## 1. Root Cause Analysis

### The Bug
During manual testing of the Streamlit Resume Builder (`careerpilot/ui/pages/4_Resume_Builder.py`), clicking into or rendering the export tab caused:
```
AttributeError: 'TailoredResume' object has no attribute 'pdf_path'
```

### Why `pdf_path` on `TailoredResume` Was an Architectural Antipattern
1. **Domain Model vs. System Artifact Confusion:**
   - `TailoredResume` represents **candidate resume content** (structured text, contact details, bullets, skills, projects, and truth audits).
   - Generated files (`.pdf`, `.docx`, `.md`) are **physical filesystem/binary artifacts**.
   - Forcing runtime filesystem paths (`resume.pdf_path`, `resume.docx_path`) into the content domain model created coupling between Pydantic content schemas and runtime disk I/O.
2. **State & Deserialization Fragility:**
   - When a `TailoredResume` was serialized to JSON, stored in SQLite (`ResumeVersionDB`), or passed across LangGraph nodes, accessing ad-hoc path properties led to `NoneType` errors or `AttributeError` when those metadata keys were absent.

---

## 2. Canonical Artifact Architecture

We established a clean architectural separation between domain content and generated artifacts:

```
             TailoredResume (Pure Domain Content)
                         │
             ┌───────────┴───────────┐
             ▼                       ▼
      [DocxResumeExporter]    [PDFResumeExporter]
             │                       │
             ▼                       ▼
      ResumeArtifact (DOCX)   ResumeArtifact (PDF)
             │                       │
             └───────────┬───────────┘
                         ▼
               [ResumeArtifactBundle]
                         │
                         ▼
             Streamlit UI & Download Buttons
```

### Models Introduced ([`careerpilot/models/artifact.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/models/artifact.py))

```python
class ResumeArtifact(BaseModel):
    """
    Represents a generated physical or in-memory resume file artifact.
    Decouples file/IO concerns from the core TailoredResume domain model.
    Implements os.PathLike, get_bytes(), exists(), and stat().
    """
    artifact_type: str  # "pdf", "docx", "markdown"
    file_name: str
    file_path: Optional[str] = None
    content_type: str
    file_bytes: Optional[bytes] = None
    created_at: str
    resume_id: str
    is_valid: bool = True
    validation_message: Optional[str] = None

    def get_bytes(self) -> bytes: ...
    def exists(self) -> bool: ...
    def stat(self) -> Any: ...


class ResumeArtifactBundle(BaseModel):
    """Container bundle of all exported file artifacts for a tailoring run."""
    resume_id: str
    pdf: Optional[ResumeArtifact] = None
    docx: Optional[ResumeArtifact] = None
    markdown: Optional[ResumeArtifact] = None
```

---

## 3. Files Changed & Implementation Details

| File | Change Type | Summary of Changes |
| :--- | :--- | :--- |
| [`careerpilot/models/artifact.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/models/artifact.py) | **NEW** | Defined `ResumeArtifact` and `ResumeArtifactBundle` models with `os.PathLike` and binary stream support. |
| [`careerpilot/models/resume.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/models/resume.py) | **MODIFIED** | Decoupled `TailoredResume` from required filesystem fields; re-exported artifact models. |
| [`careerpilot/models/__init__.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/models/__init__.py) | **MODIFIED** | Exported `ResumeArtifact` and `ResumeArtifactBundle`. |
| [`careerpilot/generators/resume_pdf.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/generators/resume_pdf.py) | **MODIFIED** | Updated `export_pdf` to return a validated `ResumeArtifact` object. |
| [`careerpilot/generators/resume_docx.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/generators/resume_docx.py) | **MODIFIED** | Updated `export_docx` to return a structured `ResumeArtifact` object. |
| [`careerpilot/generators/resume_markdown.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/generators/resume_markdown.py) | **MODIFIED** | Added `export_markdown` returning `ResumeArtifact`. |
| [`careerpilot/graphs/resume_graph.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/graphs/resume_graph.py) | **MODIFIED** | Updated `export_artifacts_node` to bundle artifacts into `ResumeArtifactBundle`. |
| [`careerpilot/services/careerpilot_service.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/services/careerpilot_service.py) | **MODIFIED** | Added `get_or_generate_resume_artifacts`, `generate_pdf_artifact`, and `generate_docx_artifact`. |
| [`careerpilot/ui/pages/4_Resume_Builder.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/ui/pages/4_Resume_Builder.py) | **MODIFIED** | Integrated `ResumeArtifact` pipeline, direct binary streaming to download buttons, and validation badges. |
| [`careerpilot/ui/pages/3_Applications.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/ui/pages/3_Applications.py) | **MODIFIED** | Updated application details to show DOCX and PDF download availability. |
| [`tests/test_resume_pdf.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/tests/test_resume_pdf.py) | **MODIFIED** | Added regression test for `TailoredResume` without `pdf_path`, artifact tests, and service tests. |
| [`tests/test_resume_pdf_e2e.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/tests/test_resume_pdf_e2e.py) | **MODIFIED** | Updated E2E tests to verify `ResumeArtifactBundle` and clean database persistence. |
| [`tests/test_docx_generator.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/tests/test_docx_generator.py) | **MODIFIED** | Verified DOCX generation with `ResumeArtifact`. |
| [`docs/RESUME_GENERATION.md`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/docs/RESUME_GENERATION.md) | **MODIFIED** | Updated architectural documentation with artifact contracts. |

---

## 4. Test Suite Execution & Verification

Full regression test run across the entire codebase:

```bash
============================= test session starts =============================
platform win32 -- Python 3.14.7, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\DELL\OneDrive\Desktop\RAG
plugins: anyio-4.14.2, langsmith-0.11.2, asyncio-1.4.0
collected 157 items

tests/test_resume_pdf.py::test_pdf_generation PASSED                     [ 68%]
tests/test_resume_pdf.py::test_resume_artifact_architecture PASSED       [ 68%]
tests/test_resume_pdf.py::test_tailored_resume_does_not_need_pdf_path PASSED [ 69%]
tests/test_resume_pdf.py::test_service_get_or_generate_resume_artifacts PASSED [ 70%]
tests/test_resume_pdf.py::test_pdf_validator_pass PASSED                 [ 70%]
tests/test_resume_pdf.py::test_pdf_contains_candidate_name PASSED        [ 71%]
tests/test_resume_pdf.py::test_pdf_contains_standard_sections PASSED     [ 71%]
tests/test_resume_pdf.py::test_pdf_searchability PASSED                  [ 72%]
tests/test_resume_pdf.py::test_docx_pdf_content_consistency PASSED       [ 73%]
tests/test_resume_pdf.py::test_safe_filename PASSED                      [ 73%]
tests/test_resume_pdf.py::test_metric_integrity PASSED                   [ 74%]
tests/test_resume_pdf.py::test_empty_resume_handling PASSED              [ 75%]
tests/test_resume_pdf.py::test_truth_guard_blocks_unsupported_claim PASSED [ 75%]
tests/test_resume_pdf.py::test_aws_negative_test PASSED                  [ 76%]
tests/test_resume_pdf.py::test_all_strategies_pdf_generation PASSED      [ 77%]
tests/test_resume_pdf_e2e.py::test_resume_pdf_end_to_end_pipeline PASSED [ 77%]
...
======================= 157 passed, 1 warning in 18.21s =======================
```

- **Previous Test Count:** 154
- **New Test Count:** 157
- **Passed:** 157
- **Failed:** 0
- **Skipped:** 0

---

## 5. Streamlit Download & Validation Behavior

1. **Direct Binary Streaming:** Download buttons now consume `artifact.get_bytes()` directly, preventing disk path desynchronization or race conditions during page reruns.
2. **Pre-Download Validation:** `PDFValidator` audits every PDF for:
   - File size > 0
   - Page count >= 1
   - Complete candidate name extraction
   - Standard section presence (`PROFESSIONAL SUMMARY`, `TECHNICAL SKILLS`, `EXPERIENCE`, `PROJECTS`, `EDUCATION`)
   - 100% single-column layout without sidebars
   - Keyword searchability (`Python`, `SQL`, `BigQuery`, `Airflow`, `GCP`)
3. **Graceful UI Errors:** If an artifact cannot be rendered or read, the UI displays a clean notification (`st.error("...")` or `st.warning("...")`) while logging the full traceback to developer logs.

---

## 6. Known Limitations

- **Commercial ATS Parsing Variance:** While the generated PDF strictly enforces consensus ATS typography (single-column, vector text, standard Helvetica fonts, no images or graphics), proprietary enterprise parsers (e.g. older versions of Taleo or proprietary Workday configurations) may evaluate documents according to internal heuristics. Providing both DOCX and PDF formats ensures candidate versatility.
