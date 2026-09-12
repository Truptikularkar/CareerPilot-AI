# CareerPilot AI — Screenshot Catalog & Capture Guide

**Document:** `docs/SCREENSHOTS.md`  
**Purpose:** Guide for capturing clean, professional screenshots for GitHub READMEs, portfolio websites, and presentation decks.

---

## 1. Capture Guidelines
- **Mode:** Always run in `DEMO` mode (`CAREERPILOT_MODE=DEMO`) to display synthetic candidate **Alex Rivera**.
- **Browser Resolution:** 1920x1080 (1080p Full HD) or 2560x1440.
- **Theme:** Default dark theme with high-contrast UI cards.
- **Data Privacy Check:** Ensure no private candidate names, email addresses, phone numbers, or real company files are visible.

---

## 2. Screenshot Manifest

| # | Page / View | Recommended Image Name | Key Elements to Highlight |
| :--- | :--- | :--- | :--- |
| **01** | **Main Welcome & Health** | `01_dashboard_welcome.png` | System health badge (All green), Alex Rivera demo profile, quick stats. |
| **02** | **Job Description Input** | `02_job_analysis_input.png` | Benchmark selector, paste text area, secure PDF uploader. |
| **03** | **Job Fit & Reality Breakdown** | `03_job_analysis_results.png` | Role work distribution chart, 85.0% Fit Score, green **APPLY** badge. |
| **04** | **Applications Pipeline** | `04_applications_tracker.png` | Application status table, fit scores, next recommended actions. |
| **05** | **Resume Tailoring & Strategy** | `05_resume_tailoring.png` | Strategy dropdown (AI Data Engineer), Truth Guard pass report, DOCX button. |
| **06** | **ATS Compatibility Report** | `06_ats_scoring.png` | 96.7% ATS Score gauge, 7-component breakdown, keyword coverage matrix. |
| **07** | **Interview Prep & Roadmaps** | `07_interview_prep.png` | Multi-category tabs (Technical, System Design, STAR), 3-day roadmap table. |
| **08** | **Adaptive Mock Interview Turn** | `08_mock_interview_turn.png` | Interviewer persona badge, candidate answer area, adaptive follow-up probe. |
| **09** | **Final Interview Diagnostic** | `09_mock_final_report.png` | Overall interview score, 10-dimension rubric radar, weak topic recommendations. |
| **10** | **Skill Gaps & Trends** | `10_skill_gaps_trends.png` | Aggregated market skill demand chart, transferable learning priorities. |
| **11** | **About & Architecture** | `11_about_architecture.png` | End-to-end system architecture flowchart, zero-fabrication pledge. |

---

## 3. How to Capture Screenshots Locally

```bash
# 1. Start application in DEMO mode
export CAREERPILOT_MODE=DEMO
streamlit run careerpilot/ui/app.py

# 2. Open browser at http://localhost:8501
# 3. Use browser full-page screenshot or Windows Snipping Tool (Win + Shift + S)
# 4. Save screenshots to docs/images/ for inclusion in README or portfolio site
```
