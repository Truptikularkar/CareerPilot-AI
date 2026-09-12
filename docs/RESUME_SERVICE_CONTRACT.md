# CareerPilot AI — Resume Service Contract

**Document Version:** 2.0  
**Scope:** Canonical specification of all resume generation, versioning, evaluation, and artifact export service methods on `CareerPilotService`.

---

## 1. Service Method Matrix

### A. `CareerPilotService.generate_resume_for_application`
```python
@classmethod
def generate_resume_for_application(
    cls,
    app_id: str,
    strategy: Optional[Union[str, ResumeStrategyType]] = None,
) -> Tuple[TailoredResume, ATSReport, Application]:
```
- **Inputs:**
  - `app_id: str` — Application ID tracked in SQLite database.
  - `strategy: Optional[Union[str, ResumeStrategyType]]` — Specific resume tailoring strategy override or `None`/`"AUTO"` for automated strategy selection.
- **Outputs:**
  - `Tuple[TailoredResume, ATSReport, Application]`
    1. `TailoredResume` — The newly compiled, truth-audited tailored resume.
    2. `ATSReport` — ATS compatibility score and breakdown against the application's JD.
    3. `Application` — Updated Application record with the new resume version linked.
- **Side Effects:**
  - Generates PDF, DOCX, and Markdown artifacts in `data/generated/resumes/<resume_id>/`.
  - Persists a new `ResumeVersionDB` record (tagged as `v1.0`, `v2.0`, etc.) in SQLite.
  - Appends `ResumeVersionRecord` to `Application.resume_versions` list.
- **Exceptions Raised:**
  - `ValueError` if `app_id` is invalid or required `JobDescription` cannot be resolved.
- **Primary Callers:**
  - `careerpilot/ui/pages/4_Resume_Builder.py` (Generate Resume button).
  - Integration and evaluation test suites.

---

### B. `CareerPilotService.get_or_generate_resume_artifacts`
```python
@classmethod
def get_or_generate_resume_artifacts(
    cls,
    resume: TailoredResume,
    company: Optional[str] = None,
) -> ResumeArtifactBundle:
```
- **Inputs:**
  - `resume: TailoredResume` — The domain model representing resume content.
  - `company: Optional[str]` — Optional company name for sanitized filename formatting.
- **Outputs:**
  - `ResumeArtifactBundle` containing:
    - `pdf: ResumeArtifact` — ATS-clean single-column PDF artifact.
    - `docx: ResumeArtifact` — Standard tableless Word document artifact.
    - `markdown: ResumeArtifact` — Clean markdown representation.
- **Side Effects:**
  - Ensures directory `data/generated/resumes/<resume.id>/` exists.
  - Writes `resume.pdf`, `resume.docx`, and `resume.md` to disk if not already generated.
- **Exceptions Raised:**
  - `RuntimeError` if rendering or file writing fails.
- **Primary Callers:**
  - `careerpilot/ui/pages/4_Resume_Builder.py` (Download tab & Regenerate button).
  - `CareerPilotService.generate_resume_for_application()`.

---

### C. `CareerPilotService.generate_pdf_artifact`
```python
@classmethod
def generate_pdf_artifact(
    cls,
    resume: TailoredResume,
    company: Optional[str] = None,
) -> ResumeArtifact:
```
- **Inputs:**
  - `resume: TailoredResume` — Tailored resume domain instance.
  - `company: Optional[str]` — Company name for filename sanitization.
- **Outputs:**
  - `ResumeArtifact` for the PDF file with `content_type="application/pdf"`.
- **Side Effects:**
  - Renders ReportLab document and writes `.pdf` file.
- **Primary Callers:**
  - `PDFResumeExporter` unit tests.

---

### D. `CareerPilotService.generate_docx_artifact`
```python
@classmethod
def generate_docx_artifact(
    cls,
    resume: TailoredResume,
    company: Optional[str] = None,
) -> ResumeArtifact:
```
- **Inputs:**
  - `resume: TailoredResume` — Tailored resume domain instance.
  - `company: Optional[str]` — Company name for filename sanitization.
- **Outputs:**
  - `ResumeArtifact` for the DOCX file with `content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"`.
- **Side Effects:**
  - Renders `python-docx` document and writes `.docx` file.
- **Primary Callers:**
  - `DocxResumeExporter` unit tests.

---

### E. `ResumeRepository.list_versions_for_job`
```python
@classmethod
def list_versions_for_job(cls, job_id: str) -> List[ResumeVersionDB]:
```
- **Inputs:**
  - `job_id: str` — The target job identifier.
- **Outputs:**
  - `List[ResumeVersionDB]` ordered chronologically by `created_at`.
- **Side Effects:** None (read-only query).
- **Primary Callers:**
  - `careerpilot/ui/pages/4_Resume_Builder.py` (Version history dropdown).
