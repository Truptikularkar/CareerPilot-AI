# CareerPilot AI — UI Type & Presentation Contract Audit

**Document:** `docs/UI_TYPE_CONTRACT_AUDIT.md`  
**Purpose:** Comprehensive static and runtime audit of all type assumptions across the UI layer, verifying datetime handling, enum conversions, object vs. dictionary accesses, and collection contracts.

---

## 1. Type Audit Matrix

| UI File | Line / Context | Symbol / Object | Expected Type | Actual Type | Audit Status | Resolution / Guard |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| [`4_Resume_Builder.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/ui/pages/4_Resume_Builder.py#L38) | Version selector timestamp | `v.created_at` | `str` (sliced `[:16]`) | `datetime.datetime` (SQLAlchemy ORM) | **FIXED** | Formatted via `format_datetime(v.created_at)` |
| [`4_Resume_Builder.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/ui/pages/4_Resume_Builder.py#L37) | Version selector ATS score | `v.ats_score` | `float` | `Optional[float]` | **FIXED** | Safely checks for `None` -> `"N/A"` |
| [`3_Applications.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/ui/pages/3_Applications.py#L114) | Version table timestamp | `v.created_at` | `str` (sliced `[:16]`) | `Union[datetime, str]` | **FIXED** | Formatted via `format_datetime(v.created_at)` |
| [`1_Dashboard.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/ui/pages/1_Dashboard.py#L69) | Job created date | `j.created_at` | `datetime.datetime` | `Optional[datetime]` | **FIXED** | Formatted via `format_date(j.created_at)` |
| [`1_Dashboard.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/ui/pages/1_Dashboard.py#L100) | Mock session timestamp | `m.created_at` | `datetime.datetime` | `Optional[datetime]` | **FIXED** | Formatted via `format_datetime(m.created_at)` |
| [`2_Analyze_Job.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/ui/pages/2_Analyze_Job.py#L128) | Seniority detection level | `seniority_detection` | `SeniorityLevel` | `SeniorityDetection` object | **VERIFIED** | Reads `.detected_seniority.value` |
| [`5_ATS_Analysis.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/ui/pages/5_ATS_Analysis.py#L54) | Truth Guard status | `ats_report.truth_status` | `Enum` / `str` | `TruthValidationStatus` | **VERIFIED** | Handles both `.value` and `str()` |
| [`6_Interview_Prep.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/ui/pages/6_Interview_Prep.py#L51) | Readiness score | `readiness_score` | `float` | `Union[Dict, ReadinessScore, float]` | **VERIFIED** | Polymorphic type extraction |
| [`7_Mock_Interview.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/ui/pages/7_Mock_Interview.py#L69) | Mock turn retrieval | `turns` | `List[MockInterviewTurn]` | `List[MockInterviewTurn]` | **VERIFIED** | Typed Pydantic list |

---

## 2. Canonical Presentation Utilities ([`careerpilot/ui/utils/formatters.py`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/ui/utils/formatters.py))

```python
def format_datetime(
    val: Optional[Union[datetime, str]],
    fmt: str = "%Y-%m-%d %H:%M",
    fallback: str = "Unknown date",
) -> str: ...

def format_date(
    val: Optional[Union[datetime, str]],
    fmt: str = "%Y-%m-%d",
    fallback: str = "N/A",
) -> str: ...
```

---

## 3. Timezone Policy
- **Database & Services:** All datetimes are generated using `datetime.now(timezone.utc)` (UTC-aware or stored as ISO-8601 strings in SQLite).
- **Presentation:** Formatted via `format_datetime()` using standard `%Y-%m-%d %H:%M` for consistent readability across all platforms.
