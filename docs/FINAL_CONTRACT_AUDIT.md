# CareerPilot AI — Static Contract Audit Report

**Date:** 2026-08-31  
**Scope:** Exhaustive audit of critical property accessors, datetime operations, artifact generators, and model properties across the entire codebase.

---

## 1. Static Pattern Audit Matrix

| Pattern Searched | File & Line Context | Status | Evaluation & Resolution | Canonical Form |
| :--- | :--- | :--- | :--- | :--- |
| **`pdf_path`** | [`careerpilot/models/resume.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/models/resume.py#L168) | **VALID (Backward-Compatible Property)** | `TailoredResume.pdf_path` is exposed as a property reading from `self.audit_metadata.get("pdf_path")`. The core model does not require it in initial validation. | `ResumeArtifactBundle.pdf.file_path` |
| **`docx_path`** | [`careerpilot/models/resume.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/models/resume.py#L164) | **VALID (Backward-Compatible Property)** | `TailoredResume.docx_path` reads from `self.audit_metadata.get("docx_path")`. | `ResumeArtifactBundle.docx.file_path` |
| **`created_at[`** | *Global Search* | **ZERO OCCURRENCES** | All timestamp string slicing (`created_at[:16]`) has been removed. All presentation formatting passes through `careerpilot.ui.utils.formatters.format_datetime()`. | `format_datetime(v.created_at)` |
| **`updated_at[`** | *Global Search* | **ZERO OCCURRENCES** | No subscripting of `datetime` objects exists. | `format_datetime(obj.updated_at)` |
| **`estimated_level`** | [`careerpilot/models/job.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/models/job.py) | **VALID (Property Alias)** | `SeniorityDetection.estimated_level` returns `self.detected_seniority`. Guarantees UI and legacy tests function seamlessly. | `seniority_detection.detected_seniority` (or property `.estimated_level`) |
| **`keyword_alignment`** | [`careerpilot/models/ats.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/models/ats.py#L125)<br>[`careerpilot/ui/pages/4_Resume_Builder.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/ui/pages/4_Resume_Builder.py#L163) | **VALID (Component Property Alias)** | `ATSReport.keyword_alignment` returns `self.components.get("keyword_coverage")`. | `ats_report.components["keyword_coverage"]` or `.keyword_alignment` |
| **`keyword_score`** | [`careerpilot/models/ats.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/models/ats.py#L23) | **VALID (Component Score Alias)** | `ATSScoreComponent.keyword_score` returns `self.score`. | `comp.score` or `comp.keyword_score` |
| **`get_or_generate_resume_artifacts`** | [`careerpilot/services/careerpilot_service.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/services/careerpilot_service.py#L250)<br>[`careerpilot/ui/pages/4_Resume_Builder.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/ui/pages/4_Resume_Builder.py#L85) | **VALID (Canonical Service Method)** | First-class service method on `CareerPilotService` managing `ResumeArtifactBundle` creation for PDF, DOCX, and Markdown. | `CareerPilotService.get_or_generate_resume_artifacts(resume, company)` |

---

## 2. Structural Findings & Verification

1. **No Hidden Exceptions:** All exception handling in `CareerPilotService` logs descriptive error traces and throws typed exceptions rather than swallowing failures with `except Exception: pass`.
2. **Session State Isolation:** Streamlit session keys in `4_Resume_Builder.py` use namespaced keys (`active_resume_{app_id}`) to prevent cross-job state bleed when switching applications.
3. **Artifact Caching:** Re-running the Streamlit page retrieves the cached `ResumeArtifactBundle` without triggering redundant LLM calls or disk I/O.
