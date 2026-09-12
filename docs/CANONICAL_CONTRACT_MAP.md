# CareerPilot AI — Canonical Contract Map

**Document Version:** 2.0  
**Scope:** Canonical data contracts, type signatures, producers, consumers, and serialization models across the CareerPilot system.

---

## 1. Core Principles of Data Ownership

1. **`CandidateProfile` & `CandidateEvidence`** own candidate ground truth. They represent verified facts from the candidate's career, education, and projects.
2. **`CandidateStore` (ChromaDB)** owns indexed vector embeddings and atomic evidence search.
3. **`JobDescription` & `JobAnalysisResult`** own JD parsing, required qualifications, role classification, and fit scores.
4. **`TailoredResume`** owns **RESUME CONTENT ONLY** (summary, bullet points, skills hierarchy, truth validation report). It does **NOT** own file paths, binary bytes, or UI download state.
5. **`ResumeArtifact` & `ResumeArtifactBundle`** own generated physical/in-memory file representations (PDF, DOCX, Markdown) and their validation metadata.
6. **`ATSReport`** owns ATS compatibility scoring, keyword coverage matrices, formatting risk evaluations, and interview seed generation.
7. **`ResumeVersion` / `ResumeVersionDB`** own version persistence, timestamps, and relational links to jobs and applications.
8. **UI Presentation Boundary** owns all visual formatting, datetime formatting, and Streamlit state management.

---

## 2. Canonical Model Catalog

### A. Candidate Domain Models ([`careerpilot.models.candidate`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/models/candidate.py))

| Model | Key Fields & Types | Producer | Consumers | Serialization |
| :--- | :--- | :--- | :--- | :--- |
| **`CandidateProfile`** | `id: str`<br>`full_name: str`<br>`email: Optional[str]`<br>`professional_summary: str`<br>`skills: List[Skill]`<br>`experiences: List[Experience]`<br>`projects: List[Project]`<br>`education: List[Education]`<br>`certifications: List[str]`<br>`achievements: List[Achievement]`<br>`preferences: CareerPreference`<br>`atomic_evidence: List[CandidateEvidence]` | `CandidateParser`<br>`CandidateRepository`<br>`CandidateService` | `CandidateStore`<br>`JobAnalysis`<br>`ResumeGraph`<br>`InterviewGraph`<br>`UI (9_Candidate_Profile.py)` | Pydantic JSON / SQLite `candidate_profiles` table |
| **`Skill`** | `name: str`<br>`category: SkillCategory`<br>`years_of_experience: float`<br>`proficiency_level: str`<br>`evidence_level: str` (`PROFESSIONAL`, `PERSONAL_PROJECT`, `LEARNING_KNOWLEDGE`)<br>`evidence_status: str` (`VERIFIED`, `PARTIAL`)<br>`context: Optional[str]` | `CandidateParser`<br>`CandidateService`<br>`ResumeImportService` | `EvidenceExtractor`<br>`FitScorer`<br>`ResumeBulletSelector` | Pydantic JSON |
| **`Experience`** | `company: str`<br>`title: str`<br>`start_date: str`<br>`end_date: str`<br>`responsibilities: List[str]`<br>`technologies_used: List[str]`<br>`verified_metrics: List[str]` | `CandidateParser`<br>`CandidateService` | `EvidenceExtractor`<br>`ResumeGraph`<br>`TruthGuard` | Pydantic JSON |
| **`Project`** | `name: str`<br>`project_type: str` (`PERSONAL_PROJECT`, `PROFESSIONAL_EXPERIENCE`, `OPEN_SOURCE`, `RESEARCH`)<br>`description: str`<br>`technologies: List[str]`<br>`responsibilities: List[str]`<br>`architecture: Optional[str]`<br>`outcome: Optional[str]`<br>`metrics: List[str]`<br>`github_or_demo_url: Optional[str]` | `CandidateParser`<br>`CandidateService` | `EvidenceExtractor`<br>`ResumeGraph`<br>`TruthGuard` | Pydantic JSON |
| **`Achievement`** | `title: str`<br>`description: str`<br>`technologies: List[str]`<br>`metrics: Optional[str]` | `CandidateParser`<br>`CandidateService` | `EvidenceExtractor`<br>`ResumeGraph` | Pydantic JSON |
| **`CareerPreference`** | `target_roles: List[RoleCategory]`<br>`preferred_seniority: SeniorityLevel`<br>`work_modes: List[str]`<br>`target_locations: List[str]`<br>`min_desired_comp: Optional[str]`<br>`cloud_preferences: List[str]` | `CandidateParser`<br>`CandidateService` | `DecisionEngine`<br>`FitScorer` | Pydantic JSON |
| **`ProfileDiffItem`** | `section: str`<br>`change_type: str` (`ADDED`, `REMOVED`, `CHANGED`, `UNCHANGED`)<br>`item_name: str`<br>`old_value: Any`<br>`new_value: Any`<br>`approved: bool` | `ResumeImportService.compute_diff()` | `UI (9_Candidate_Profile.py)`<br>`ResumeImportService.apply_diff_items()` | Pydantic JSON |
| **`ProfileHealthSummary`** | `is_profile_configured: bool`<br>`has_verified_evidence: bool`<br>`is_rag_synchronized: bool`<br>`completeness_score_pct: float`<br>`evidence_coverage_pct: float`<br>`last_updated_timestamp: Optional[datetime]` | `CandidateService.get_profile_health()` | `UI Top Health Banner` | Pydantic Model |

---

### B. Job & Analysis Models ([`careerpilot.models.job`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/models/job.py))

| Model | Key Fields & Types | Producer | Consumers | Serialization |
| :--- | :--- | :--- | :--- | :--- |
| **`JobDescription`** | `id: str`<br>`company_name: str`<br>`job_title: str`<br>`raw_text: str`<br>`location: str`<br>`requirements: List[JobRequirement]` | `JobDescriptionParser`<br>`JobRepository` | `JobAnalysisGraph`<br>`ApplicationRepository` | Pydantic JSON / SQLite `job_descriptions` table |
| **`JobRequirement`** | `id: str`<br>`text: str`<br>`importance: RequirementImportance`<br>`category: TaxonomyCategory`<br>`skills: List[str]` | `JDParser`<br>`JobAnalysisGraph` | `FitScorer`<br>`ATSEvaluator`<br>`TruthGuard` | Pydantic JSON |
| **`SeniorityDetection`** | `detected_seniority: SeniorityLevel`<br>`explicit_years_required: Optional[float]`<br>`reasoning: str` | `SeniorityDetectorNode` | `FitScorer`<br>`UI (2_Analyze_Job.py)` | Pydantic JSON (`estimated_level` property accessor) |
| **`RoleClassification`** | `primary_role: RoleCategory`<br>`confidence: float`<br>`secondary_roles: List[RoleCategory]`<br>`work_distribution: Dict[str, float]` | `RoleClassifierNode` | `StrategySelector`<br>`FitScorer` | Pydantic JSON (`role_category` property accessor) |
| **`JobAnalysisResult`** | `job_id: str`<br>`company_name: str`<br>`job_title: str`<br>`role_classification: RoleClassification`<br>`seniority_detection: SeniorityDetection`<br>`fit_breakdown: FitScoreBreakdown`<br>`recommendation: DecisionRecommendation`<br>`cloud_transferability: CloudTransferability`<br>`risks: List[RiskItem]` | `JobAnalysisGraph.analyze_job()` | `ApplicationRepository`<br>`ResumeGraph`<br>`InterviewGraph`<br>`UI (2_Analyze_Job.py)` | Pydantic JSON / SQLite `job_analyses` table |

---

### C. Tailored Resume & Truth Guard Models ([`careerpilot.models.resume`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/models/resume.py))

| Model | Key Fields & Types | Producer | Consumers | Serialization |
| :--- | :--- | :--- | :--- | :--- |
| **`TailoredResume`** | `id: str`<br>`job_id: str`<br>`candidate_id: str`<br>`strategy: ResumeStrategy`<br>`header: ResumeHeader`<br>`summary: ResumeSummary`<br>`skills_categories: List[ResumeSkillCategory]`<br>`experiences: List[ResumeExperienceEntry]`<br>`projects: List[ResumeProjectEntry]`<br>`education: List[ResumeEducationEntry]`<br>`certifications: List[ResumeCertificationEntry]`<br>`truth_report: Optional[TruthValidationReport]`<br>`ats_precheck: Optional[ATSPrecheckResult]`<br>`audit_metadata: Dict[str, Any]` | `ResumeGraph.generate_tailored_resume()` | `ATSEvaluator`<br>`PDFResumeExporter`<br>`DocxResumeExporter`<br>`MarkdownResumeExporter`<br>`UI (4_Resume_Builder.py)` | Pydantic JSON / SQLite `resume_versions.tailored_resume_json` |
| **`TruthValidationReport`** | `status: TruthValidationStatus`<br>`verified_claims_count: int`<br>`flagged_claims: List[TruthClaimCheck]`<br>`blocked_claims: List[TruthClaimCheck]`<br>`metric_checks: List[TruthClaimCheck]`<br>`tech_checks: List[TruthClaimCheck]`<br>`experience_type_checks: List[TruthClaimCheck]`<br>`summary_reasoning: str` | `TruthGuardNode` | `TailoredResume`<br>`ATSEvaluator`<br>`UI Truth Tab` | Pydantic JSON |
| **`ResumeStrategy`** | `strategy_type: ResumeStrategyType`<br>`target_role: str`<br>`emphasis_keywords: List[str]`<br>`summary_tone: str`<br>`project_priorities: List[str]`<br>`skill_priorities: List[str]`<br>`reasoning: str` | `StrategySelectorNode` | `ResumeGraph`<br>`UI` | Pydantic JSON |

---

### D. Generated File Artifact Models ([`careerpilot.models.artifact`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/models/artifact.py))

| Model | Key Fields & Types | Producer | Consumers | Serialization |
| :--- | :--- | :--- | :--- | :--- |
| **`ResumeArtifact`** | `artifact_type: str` (`pdf`, `docx`, `markdown`)<br>`file_name: str`<br>`file_path: Optional[str]`<br>`content_type: str`<br>`file_bytes: Optional[bytes]`<br>`created_at: str`<br>`resume_id: str`<br>`is_valid: bool`<br>`validation_message: Optional[str]` | `PDFResumeExporter`<br>`DocxResumeExporter`<br>`MarkdownResumeExporter` | `CareerPilotService`<br>`ResumeRepository`<br>`Streamlit Download Buttons` | Pydantic JSON / Disk Filesystem (`data/generated/resumes/<id>/`) |
| **`ResumeArtifactBundle`** | `resume_id: str`<br>`pdf: Optional[ResumeArtifact]`<br>`docx: Optional[ResumeArtifact]`<br>`markdown: Optional[ResumeArtifact]` | `CareerPilotService.get_or_generate_resume_artifacts()` | `UI (4_Resume_Builder.py)` | Pydantic Model |

---

### E. ATS Models ([`careerpilot.models.ats`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/models/ats.py))

| Model | Key Fields & Types | Producer | Consumers | Serialization |
| :--- | :--- | :--- | :--- | :--- |
| **`ATSReport`** | `resume_id: str`<br>`job_id: str`<br>`job_title: str`<br>`company_name: Optional[str]`<br>`target_strategy: str`<br>`overall_score: float` (0.0 to 100.0)<br>`score_interpretation: str`<br>`components: Dict[str, ATSScoreComponent]`<br>`coverage_matrix: List[RequirementCoverageItem]`<br>`taxonomy_alignments: List[TaxonomyAlignmentItem]`<br>`formatting_risks: List[FormattingRiskItem]`<br>`missing_requirements: List[MissingRequirement]`<br>`suggestions: List[OptimizationSuggestion]`<br>`truth_status: TruthValidationStatus`<br>`interview_seed: Optional[InterviewReadinessSeed]` | `ATSEvaluator.evaluate_resume()` | `CareerPilotService`<br>`ResumeRepository`<br>`InterviewGraph`<br>`UI (4_Resume_Builder.py, 5_ATS_Analysis.py)` | Pydantic JSON / SQLite `resume_versions.ats_report_json` |
| **`ATSScoreComponent`** | `name: str`<br>`score: float`<br>`weight: float`<br>`weighted_score: float`<br>`explanation: str` | `ATSEvaluator` | `ATSReport`<br>`UI Metrics` (`keyword_alignment`, `semantic_alignment`, etc.) | Pydantic JSON |
| **`InterviewReadinessSeed`** | `job_id: str`<br>`target_role: str`<br>`high_priority_skills: List[str]`<br>`candidate_strengths: List[str]`<br>`candidate_gaps: List[str]`<br>`likely_interview_topics: List[str]`<br>`risky_requirements: List[str]`<br>`challenged_claims: List[str]` | `ATSEvaluator` | `InterviewPrepGraph`<br>`MockInterviewSession` | Pydantic JSON |

---

## 3. Boundary & Type Invariant Rules

1. **Datetime Invariant:** All database models store timestamps as standard Python `datetime` objects (`DateTime(timezone=True)`). No internal layer converts datetime to sliced strings (`[:16]`). String rendering is exclusively performed at presentation time using [`careerpilot.ui.utils.formatters.format_datetime()`](file:///c:/Users/DELL/OneDrive/Desktop/RAG/careerpilot/ui/utils/formatters.py).
2. **Resume Immutability:** `TailoredResume` is produced once per version. The identical instance is evaluated by `ATSEvaluator` and converted to PDF/DOCX by `PDFResumeExporter` and `DocxResumeExporter`.
3. **Artifact Decoupling:** `ResumeArtifact` handles file bytes, content types, and paths. `TailoredResume` remains pure business domain content.
