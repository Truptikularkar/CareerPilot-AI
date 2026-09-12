# CareerPilot AI — Resume Export Contract Audit

**Document:** `docs/RESUME_EXPORT_CONTRACT_AUDIT.md`  
**Purpose:** Comprehensive static contract audit verifying every UI consumer, service method, domain model, generator, and artifact across the resume export pipeline.

---

## Contract Matrix

| UI Consumer | Service Method | Producer / Engine | Domain Model | Generator | Output Artifact | Audit Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| [`4_Resume_Builder.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/ui/pages/4_Resume_Builder.py) | [`CareerPilotService.list_applications`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/services/careerpilot_service.py#L135) | `ApplicationRepository.list_applications` | `Application` | N/A | `List[Application]` | **VERIFIED** |
| [`4_Resume_Builder.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/ui/pages/4_Resume_Builder.py) | [`ResumeRepository.list_versions_for_job`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/db/repository.py) | `ResumeRepository` (SQLite) | `ResumeVersionDB` | N/A | `List[ResumeVersionDB]` | **VERIFIED** |
| [`4_Resume_Builder.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/ui/pages/4_Resume_Builder.py) | [`CareerPilotService.generate_resume_for_application`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/services/careerpilot_service.py#L168) | `careerpilot.graphs.resume_graph` | `TailoredResume`, `ATSReport`, `Application` | `PDFResumeExporter`, `DocxResumeExporter` | `Tuple[TailoredResume, ATSReport, Application]` | **VERIFIED** |
| [`4_Resume_Builder.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/ui/pages/4_Resume_Builder.py) | [`CareerPilotService.get_or_generate_resume_artifacts`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/services/careerpilot_service.py#L250) | Exporters | `TailoredResume` | `PDFResumeExporter`, `DocxResumeExporter`, `MarkdownResumeExporter` | `ResumeArtifactBundle` | **VERIFIED** |
| [`4_Resume_Builder.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/ui/pages/4_Resume_Builder.py) | `PDFValidator.validate_pdf` | `PDFValidator` (PyMuPDF) | N/A | N/A | `PDFValidationResult` | **VERIFIED** |
| [`4_Resume_Builder.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/ui/pages/4_Resume_Builder.py) | `st.download_button(data=artifact.get_bytes())` | `ResumeArtifact` | N/A | N/A | Binary stream (`bytes`) | **VERIFIED** |
| [`3_Applications.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/ui/pages/3_Applications.py) | `st.download_button(...)` | File on disk | `ResumeVersionRecord` | N/A | Binary stream (`bytes`) | **VERIFIED** |
| [`5_ATS_Analysis.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/ui/pages/5_ATS_Analysis.py) | [`CareerPilotService.evaluate_ats_for_application`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/services/careerpilot_service.py#L304) | `ATSEvaluator` | `ATSReport` | `ATSReportExporter` | `ATSReport` | **VERIFIED** |

---

## Detailed Model & Property Contracts

### 1. `TailoredResume` Properties Verified
- `resume.header`: `ResumeHeader` (`full_name`, `email`, `phone`, `location`, `linkedin_url`, `github_url`)
- `resume.summary`: `ResumeSummary` (`text`, `target_title`, `experience_years_stated`)
- `resume.skills_categories`: `List[ResumeSkillCategory]` (`category_name`, `skills`)
- `resume.experiences`: `List[ResumeExperienceEntry]` (`company`, `title`, `start_date`, `end_date`, `location`, `bullets`)
- `resume.projects`: `List[ResumeProjectEntry]` (`name`, `description`, `technologies`, `bullets`)
- `resume.education`: `List[ResumeEducationEntry]` (`institution`, `degree`, `field_of_study`, `graduation_year`)
- `resume.certifications`: `List[ResumeCertificationEntry]` (`name`, `issuer`, `year`)
- `resume.truth_validation` / `resume.truth_report`: `TruthValidationReport` (`status`, `verified_claims_count`, `blocked_claims_count`, `summary_reasoning`, `claims_evaluated`)

### 2. `ATSReport` Properties Verified
- `ats_report.overall_score`: `float`
- `ats_report.score_interpretation`: `str`
- `ats_report.keyword_alignment`: `ATSComponentScore` (`score`, `weighted_score`, `explanation`)
- `ats_report.semantic_alignment`: `ATSComponentScore` (`score`, `weighted_score`, `explanation`)
- `ats_report.truth_status`: `TruthValidationStatus`
- `ats_report.components`: `Dict[str, ATSComponentScore]`
- `ats_report.coverage_matrix`: `List[ATSCoverageItem]`

### 3. `ResumeArtifact` Properties & Methods Verified
- `artifact.artifact_type`: `str`
- `artifact.file_name`: `str`
- `artifact.file_path`: `Optional[str]`
- `artifact.content_type`: `str`
- `artifact.is_valid`: `bool`
- `artifact.validation_message`: `Optional[str]`
- `artifact.get_bytes()`: `bytes`
- `artifact.exists()`: `bool`
- `artifact.stat()`: `os.stat_result`
