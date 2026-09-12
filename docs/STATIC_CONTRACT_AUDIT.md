# CareerPilot AI — Static Contract & Field Audit

**Document:** `docs/STATIC_CONTRACT_AUDIT.md`  
**Purpose:** Comprehensive audit of all direct model attribute accesses, identified discrepancies, canonical resolutions, and current verification status across CareerPilot AI.

---

## Static Field Access Audit Table

| File | Line | Accessed Field / Pattern | Canonical Field / Resolution | Discrepancy Description | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `careerpilot/ui/pages/4_Resume_Builder.py` | 82 | `ats_report.keyword_alignment.keyword_score` | `ats_report.keyword_alignment.score` / `@property keyword_alignment` on `ATSReport` | `ATSReport` stored components in `Dict[str, ATSScoreComponent]`. Added type-safe component properties on `ATSReport`. | ✅ RESOLVED |
| `careerpilot/ui/pages/4_Resume_Builder.py` | 92 | `resume.summary.tailored_summary` | `resume.summary.text` | `ResumeSummary` uses `text`. Updated UI and added string conversion fallback. | ✅ RESOLVED |
| `careerpilot/ui/pages/4_Resume_Builder.py` | 98 | `b.bullet_text`, `b.evidence_id` | `b` (as `str`) | `ResumeExperienceEntry.bullets` is `List[str]`. Updated UI to render bullet strings. | ✅ RESOLVED |
| `careerpilot/ui/pages/4_Resume_Builder.py` | 104 | `b.bullet_text`, `b.evidence_id` | `b` (as `str`) | `ResumeProjectEntry.bullets` is `List[str]`. Updated UI to render project bullets. | ✅ RESOLVED |
| `careerpilot/ui/pages/4_Resume_Builder.py` | 125 | `claim.confidence` | `claim.violation_reason` | `TruthClaimCheck` fields are `claim_text`, `status`, `matched_evidence_id`, `violation_reason`. | ✅ RESOLVED |
| `careerpilot/ui/pages/2_Analyze_Job.py` | 125 | `analysis.role_classification.primary_role.value` | Formatted title string `AI Data Engineer` | UI displayed raw snake_case enum string `AI_DATA_ENGINEER`. Separated internal enum from human label. | ✅ RESOLVED |
| `careerpilot/ui/pages/2_Analyze_Job.py` | 127 | `analysis.seniority_detection.estimated_level.value` | `analysis.seniority_detection.detected_seniority.value` | `SeniorityDetection` defines `detected_seniority`. Added `@property estimated_level` and updated UI. | ✅ RESOLVED |
| `careerpilot/ui/pages/2_Analyze_Job.py` | 206 | `r.title` on `RiskItem` | `r.risk_type.value` / `@property title` on `RiskItem` | `RiskItem` defines `risk_type: RiskType`. Added `@property title` on `RiskItem` and updated UI. | ✅ RESOLVED |
| `careerpilot/ui/pages/2_Analyze_Job.py` | 213–217 | `cloud.primary_target_cloud`, `cloud.status` | `cloud.cloud_requested`, `cloud.transferability_status` | `CloudTransferability` fields were mapped to aliases. Added canonical accessors and updated UI. | ✅ RESOLVED |
| `careerpilot/ui/pages/6_Interview_Prep.py` | 100–104 | `ans.short_answer`, `ans.standard_answer`, `ans.detailed_answer` | `ans.short_version`, `ans.standard_version`, `ans.detailed_version` | `InterviewAnswer` defines `short_version`, etc. Added `@property short_answer`, etc. and updated UI. | ✅ RESOLVED |
| `careerpilot/ui/pages/6_Interview_Prep.py` | 112 | `star.competency`, `star.question` | Default fields on `STARAnswer` | Added default fields `competency` and `question` to `STARAnswer`. | ✅ RESOLVED |
| `careerpilot/ui/pages/6_Interview_Prep.py` | 126–132 | `sd.scenario_title`, `sd.storage_layer`, `sd.processing_layer` | `sd.title`, `sd.storage`, `sd.processing` | Added property aliases on `SystemDesignScenario` and updated UI. | ✅ RESOLVED |
| `careerpilot/ui/pages/6_Interview_Prep.py` | 153–156 | `roadmap.days`, `day.theme`, `day.tasks` | `roadmap.daily_schedule`, `day.title`, `day.practice_drills` | Added property aliases on `PreparationRoadmap` & `PreparationDayPlan` and updated UI. | ✅ RESOLVED |
| `careerpilot/models/resume.py` | 189 | `ATSReport = ATSPrecheckResult` | `from careerpilot.models.ats import ATSReport` | Legacy alias in `resume.py` masked the full `ATSReport` model. Re-exported canonical `ATSReport`. | ✅ RESOLVED |
| `careerpilot/models/job.py` | 152 | `FitScoreBreakdown.overall_score` | `@property overall_score -> total_weighted_score` | `FitScoreBreakdown` defines `total_weighted_score`. Added `@property overall_score`. | ✅ RESOLVED |

---

## Summary of Resolution Approach:
1. **Single Source of Truth:** Canonical Pydantic models are the authoritative contract.
2. **Backward-Compatible Property Accessors:** Added explicit `@property` helpers on models (e.g. `estimated_level`, `keyword_alignment`, `overall_score`) to guard against consumer variations without duplicating underlying data.
3. **Robust UI Renderers:** Streamlit pages verify attribute presence using standard `hasattr`/`getattr` fallbacks to eliminate unhandled `AttributeError` crashes completely.
