# CareerPilot AI — Resume Export Real Data Flow

**Document:** `docs/RESUME_EXPORT_DATA_FLOW.md`  
**Purpose:** Precise documentation of the actual runtime data flow from Streamlit UI to service, graph, generators, and file downloads using real repository symbols.

---

## 1. End-to-End Runtime Data Flow

```
                      Streamlit UI
              (`4_Resume_Builder.py`)
                         │
        [User clicks ✨ Generate Tailored Resume]
                         │
                         ▼
             `CareerPilotService.generate_resume_for_application(app_id, strategy)`
                         │
                         ▼
        ┌────────────────────────────────────────────────────────┐
        │  `careerpilot.graphs.resume_graph.generate_tailored_resume()`
        │                                                        │
        │  1. `load_analysis_node`      ──► `JobAnalysisResult`  │
        │  2. `select_strategy_node`    ──► `ResumeStrategy`     │
        │  3. `assemble_and_draft_node` ──► `TailoredResume`     │
        │  4. `validate_truth_node`     ──► `TruthValidator`     │
        │  5. `qa_ats_check_node`       ──► `ATSEvaluator`       │
        │  6. `export_artifacts_node`   ──► `ResumeArtifactBundle`│
        └────────────────────────────────────────────────────────┘
                         │
                         ▼
             `CareerPilotService.get_or_generate_resume_artifacts(resume, company)`
                         │
          ┌──────────────┴──────────────┐
          ▼                             ▼
`PDFResumeExporter.export_pdf()`  `DocxResumeExporter.export_docx()`
  (ReportLab PDF Generator)          (python-docx Generator)
          │                             │
          ▼                             ▼
   `ResumeArtifact` (PDF)        `ResumeArtifact` (DOCX)
          │                             │
          └──────────────┬──────────────┘
                         ▼
              `ResumeArtifactBundle`
                         │
                         ▼
             Streamlit Download Buttons
      `st.download_button(data=artifact.get_bytes())`
```

---

## 2. Real Component Symbol Mapping

| Step | Component / Layer | Real File & Class / Function | Inputs | Outputs |
| :--- | :--- | :--- | :--- | :--- |
| **1. UI Trigger** | Streamlit UI | [`careerpilot/ui/pages/4_Resume_Builder.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/ui/pages/4_Resume_Builder.py) | User selections (`app_id`, `strategy`) | UI state updates |
| **2. Orchestration** | Service Layer | [`CareerPilotService.generate_resume_for_application`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/services/careerpilot_service.py) | `app_id: str`, `strategy: Optional[ResumeStrategyType]` | `Tuple[TailoredResume, ATSReport, Application]` |
| **3. Workflow Execution** | LangGraph Engine | [`careerpilot.graphs.resume_graph.generate_tailored_resume`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/graphs/resume_graph.py) | `JobAnalysisResult` or `job_input` | `TailoredResume` |
| **4. Truth Guard Audit** | Anti-Hallucination Gate | [`TruthValidator.validate_tailored_resume`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/truth_guard/validator.py) | `TailoredResume` | `TruthValidationReport` |
| **5. ATS Scoring** | Compatibility Evaluator | [`ATSEvaluator.evaluate_resume`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/ats/evaluator.py) | `TailoredResume`, `JobAnalysisResult` | `ATSReport` |
| **6. PDF Generation** | PDF Generator | [`PDFResumeExporter.export_pdf`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/generators/resume_pdf.py) | `TailoredResume`, `output_path`, `company` | `ResumeArtifact` (PDF) |
| **7. DOCX Generation** | Word Generator | [`DocxResumeExporter.export_docx`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/generators/resume_docx.py) | `TailoredResume`, `output_path`, `company` | `ResumeArtifact` (DOCX) |
| **8. Artifact Validation** | PDF Validator | [`PDFValidator.validate_pdf`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/generators/pdf_validator.py) | `file_path: Union[str, Path]`, `candidate_name` | `PDFValidationResult` |
| **9. Persistence** | SQLite Repository | [`ResumeRepository.save_resume_version`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/db/repository.py) | `ResumeVersionDB` | `ResumeVersionDB` |
| **10. UI Download** | Streamlit Direct Bytes | `st.download_button(data=artifact.get_bytes())` | Raw `bytes` from `ResumeArtifact` | Browser file download |

---

## 3. Data Model Contracts

### Content Model: `TailoredResume` ([`careerpilot/models/resume.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/models/resume.py))
- `id: str`
- `job_id: str`
- `candidate_id: str = "trupti_kularkar"`
- `strategy: ResumeStrategy`
- `header: ResumeHeader`
- `summary: ResumeSummary`
- `skills_categories: List[ResumeSkillCategory]`
- `experiences: List[ResumeExperienceEntry]`
- `projects: List[ResumeProjectEntry]`
- `education: List[ResumeEducationEntry]`
- `certifications: List[ResumeCertificationEntry]`
- `truth_report: Optional[TruthValidationReport]`
- `ats_precheck: Optional[ATSPrecheckResult]`
- `audit_metadata: Dict[str, Any]`

### Artifact Model: `ResumeArtifact` ([`careerpilot/models/artifact.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/models/artifact.py))
- `artifact_type: str` (`"pdf"`, `"docx"`, `"markdown"`)
- `file_name: str` (Sanitized filename e.g. `Trupti_Kularkar_AI_Data_Engineer_CognitiveScale_Labs_Resume.pdf`)
- `file_path: Optional[str]`
- `content_type: str` (e.g. `application/pdf`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`)
- `file_bytes: Optional[bytes]`
- `created_at: str`
- `resume_id: str`
- `is_valid: bool`
- `validation_message: Optional[str]`
- `get_bytes() -> bytes`
- `exists() -> bool`
- `stat() -> os.stat_result`
