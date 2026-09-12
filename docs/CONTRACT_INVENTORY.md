# CareerPilot AI — Canonical Contract Inventory

**Document:** `docs/CONTRACT_INVENTORY.md`  
**Purpose:** Comprehensive single-source-of-truth inventory of all Pydantic domain models, fields, types, producers, and consumers across CareerPilot AI.

---

## 1. Candidate Domain (`careerpilot/models/candidate.py` & `evidence.py`)

### `CandidateProfile`
- **File:** `careerpilot/models/candidate.py`
- **Fields:**
  - `id: str` (UUID)
  - `full_name: str`
  - `email: Optional[str]`
  - `phone: Optional[str]`
  - `linkedin_url: Optional[str]`
  - `github_url: Optional[str]`
  - `portfolio_url: Optional[str]`
  - `location: Optional[str]`
  - `professional_summary: str`
  - `skills: List[Skill]`
  - `experiences: List[Experience]`
  - `projects: List[Project]`
  - `education: List[Education]`
  - `certifications: List[str]`
  - `preferences: CareerPreference`
  - `atomic_evidence: List[CandidateEvidence]`
- **Producer:** `CandidateParser.parse_all()`
- **Consumers:** `Retriever`, `FitScorer`, `TruthValidator`, `StrategySelector`, UI Settings / Dashboard.

### `CandidateEvidence`
- **File:** `careerpilot/models/evidence.py`
- **Fields:**
  - `id: str` (UUID)
  - `candidate_id: str`
  - `evidence_type: EvidenceType` (`WORK_EXPERIENCE`, `PROJECT`, `SKILL`, `EDUCATION`, `CERTIFICATION`, `ACHIEVEMENT`)
  - `source_section: str`
  - `content: str`
  - `skill_tags: List[str]`
  - `technologies: List[str]`
  - `metrics: List[str]`
  - `confidence: float`
  - `status: EvidenceStatus` (`SUPPORTED`, `PARTIALLY_SUPPORTED`, `NOT_SUPPORTED`)
  - `metadata: Dict[str, Any]`
- **Producer:** `CandidateParser.extract_atomic_evidence()`
- **Consumers:** `ChromaDB Candidate Collection`, `DualStoreRetriever`, `TruthValidator`, `AnswerEngine`.

---

## 2. Job Analysis Domain (`careerpilot/models/job.py`)

### `JobRequirement`
- **File:** `careerpilot/models/job.py`
- **Fields:**
  - `requirement_id: str`
  - `skill_name: str`
  - `normalized_skill: str`
  - `category: TaxonomyCategory`
  - `importance: RequirementImportance` (`MUST_HAVE`, `NICE_TO_HAVE`, `UNKNOWN`)
  - `years_required: Optional[float]`
  - `experience_type: str`
  - `evidence_expected: Optional[str]`
  - `source_text: str`
  - `confidence: float`
- **Producer:** `RequirementExtractor.extract_requirements()`
- **Consumers:** `FitScorer`, `RequirementMatrixGenerator`, `RiskAnalyzer`.

### `SeniorityDetection`
- **File:** `careerpilot/models/job.py`
- **Fields:**
  - `detected_seniority: SeniorityLevel` (`INTERN`, `ENTRY`, `JUNIOR`, `MID`, `SENIOR`, `LEAD`, `UNKNOWN`)
  - `explicit_years_required: Optional[float]`
  - `reasoning: str`
  - `confidence: float`
- **Accessors:** `.estimated_level`, `.seniority`
- **Producer:** `SeniorityDetector.detect_seniority()`
- **Consumers:** `RoleClassifier`, `JobAnalysisResult`, UI Analyze Job (`2_Analyze_Job.py`).

### `RoleClassification`
- **File:** `careerpilot/models/job.py`
- **Fields:**
  - `primary_role: RoleCategory` (`DATA_ENGINEER`, `AI_DATA_ENGINEER`, `GENAI_ENGINEER`, `GCP_DATA_ENGINEER`, `SOFTWARE_ENGINEER`, etc.)
  - `secondary_role: Optional[RoleCategory]`
  - `role_family: str`
  - `seniority: SeniorityLevel`
  - `confidence: float`
  - `reasoning: str`
- **Producer:** `RoleClassifier.classify()`
- **Consumers:** `StrategySelector`, `FitScorer`, UI Analyze Job (`2_Analyze_Job.py`).

### `CloudTransferability`
- **File:** `careerpilot/models/job.py`
- **Fields:**
  - `cloud_requested: str` (e.g. "AWS", "GCP", "Azure")
  - `is_must_have: bool`
  - `is_nice_to_have: bool`
  - `centrality: str`
  - `candidate_cloud: str`
  - `transferability_status: CloudTransferabilityStatus` (`MATCH`, `TRANSFERABLE_HIGH`, `TRANSFERABLE_MODERATE`, `GAP_HIGH`)
  - `transferability_reasoning: str`
- **Accessors:** `.primary_target_cloud`, `.candidate_verified_cloud`, `.status`, `.explanation`, `.recommended_framing`
- **Producer:** `CloudTransferabilityAnalyzer.analyze()`
- **Consumers:** `DecisionEngine`, `GapHandler`, UI Analyze Job.

### `JobAnalysisResult`
- **File:** `careerpilot/models/job.py`
- **Fields:**
  - `id: str`
  - `job_id: str`
  - `job_title: str`
  - `company_name: str`
  - `role_classification: RoleClassification`
  - `role_reality: RoleReality`
  - `seniority_detection: SeniorityDetection`
  - `cloud_transferability: CloudTransferability`
  - `requirements: List[JobRequirement]`
  - `matches: List[RequirementMatch]`
  - `fit_score: FitScoreBreakdown`
  - `recommendation: DecisionRecommendation` (`APPLY`, `REVIEW`, `SKIP`, `PREPARE`)
  - `risks: List[RiskItem]`
  - `key_strengths: List[str]`
  - `key_gaps: List[str]`
  - `transferable_skills: List[str]`
  - `explainable_reasoning: str`
  - `metadata: Dict[str, Any]`
- **Producer:** `job_analysis_graph.invoke()`
- **Consumers:** `ResumeGraph`, `InterviewPrepGraph`, `CareerPilotService`, UI pages.

---

## 3. Tailored Resume & Truth Guard Domain (`careerpilot/models/resume.py`)

### `TailoredResume`
- **File:** `careerpilot/models/resume.py`
- **Fields:**
  - `id: str`
  - `job_id: str`
  - `candidate_id: str`
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
- **Accessors:** `.experience`, `.skills_sections`, `.truth_validation`, `.docx_path`, `.markdown_path`
- **Producer:** `resume_graph.invoke()`
- **Consumers:** `DocxGenerator`, `ATSEvaluator`, `ResumeRepository`, UI Resume Builder (`4_Resume_Builder.py`).

### `TruthValidationReport`
- **File:** `careerpilot/models/resume.py`
- **Fields:**
  - `status: TruthValidationStatus` (`PASS`, `FLAG`, `BLOCK`)
  - `verified_claims_count: int`
  - `flagged_claims: List[TruthClaimCheck]`
  - `blocked_claims: List[TruthClaimCheck]`
  - `metric_checks: List[TruthClaimCheck]`
  - `tech_checks: List[TruthClaimCheck]`
  - `experience_type_checks: List[TruthClaimCheck]`
  - `summary_reasoning: str`
- **Accessors:** `.claims_evaluated`, `.blocked_claims_count`, `.summary`
- **Producer:** `TruthValidator.validate_tailored_resume()`
- **Consumers:** `ResumeGraph`, `ResumeVersionDB`, UI Resume Builder.

---

## 4. ATS Compatibility Domain (`careerpilot/models/ats.py`)

### `ATSReport`
- **File:** `careerpilot/models/ats.py`
- **Fields:**
  - `resume_id: str`
  - `job_id: str`
  - `job_title: str`
  - `company_name: Optional[str]`
  - `target_strategy: str`
  - `overall_score: float` (0.0 to 100.0)
  - `score_interpretation: str`
  - `components: Dict[str, ATSScoreComponent]` (`keyword_coverage`, `skill_taxonomy`, `semantic_alignment`, `experience_alignment`, `structure`, `formatting`, `readability`)
  - `must_have_coverage_ratio: str`
  - `nice_to_have_coverage_ratio: str`
  - `coverage_matrix: List[RequirementCoverageItem]`
  - `taxonomy_alignments: List[TaxonomyAlignmentItem]`
  - `formatting_risks: List[FormattingRiskItem]`
  - `keyword_density_findings: List[str]`
  - `missing_requirements: List[MissingRequirement]`
  - `suggestions: List[OptimizationSuggestion]`
  - `truth_status: TruthValidationStatus`
  - `truth_violations_count: int`
  - `interview_seed: Optional[InterviewReadinessSeed]`
- **Accessors:** `.score`, `.keyword_coverage`, `.keyword_alignment`, `.skill_taxonomy`, `.semantic_alignment`, `.experience_alignment`, `.structure`, `.formatting`, `.readability`
- **Producer:** `ATSEvaluator.evaluate_resume()`
- **Consumers:** `CareerPilotService`, UI Resume Builder (`4_Resume_Builder.py`), UI ATS Analysis (`5_ATS_Analysis.py`).

---

## 5. Interview Preparation & Mock Agent Domain (`careerpilot/models/interview.py` & `mock_interview.py`)

### `InterviewPlan`
- **File:** `careerpilot/models/interview.py`
- **Fields:**
  - `prep_id: str`
  - `job_id: str`
  - `job_title: str`
  - `target_role: str`
  - `strategy: str`
  - `questions: List[InterviewQuestion]`
  - `answers: List[InterviewAnswer]`
  - `star_answers: List[STARAnswer]`
  - `system_designs: List[SystemDesignScenario]`
  - `roadmap: PreparationRoadmap`
  - `readiness_score: InterviewReadinessScore`
  - `truth_report: Optional[Dict[str, Any]]`
- **Producer:** `interview_prep_graph.invoke()`
- **Consumers:** `InterviewPrepRepository`, UI Interview Prep (`6_Interview_Prep.py`).

### `FinalInterviewReport`
- **File:** `careerpilot/models/mock_interview.py`
- **Fields:**
  - `session_id: str`
  - `job_id: str`
  - `target_role: str`
  - `mode: MockInterviewMode`
  - `persona: InterviewerPersona`
  - `total_turns: int`
  - `overall_score: float`
  - `technical_score: float`
  - `communication_score: float`
  - `resume_knowledge_score: float`
  - `project_score: float`
  - `system_design_score: float`
  - `behavioral_score: float`
  - `problem_solving_score: float`
  - `experience_accuracy_score: float`
  - `topic_mastery: Dict[str, TopicMastery]`
  - `strengths: List[StrengthItem]`
  - `weaknesses: List[WeaknessItem]`
  - `jd_coverage: List[JDCoverageItem]`
  - `unsupported_claims: List[TruthAuditItem]`
  - `recommended_study_topics: List[str]`
  - `executive_summary: str`
- **Producer:** `MockInterviewService.finish_session()`
- **Consumers:** `MockSessionRepository`, UI Mock Interview (`7_Mock_Interview.py`).

---

## 6. Application & Lifecycle Domain (`careerpilot/models/application.py`)

### `Application`
- **File:** `careerpilot/models/application.py`
- **Fields:**
  - `application_id: str`
  - `company: str`
  - `job_title: str`
  - `job_location: Optional[str]`
  - `job_url: Optional[str]`
  - `job_description: Optional[str]`
  - `job_id: str`
  - `job_analysis_id: Optional[str]`
  - `system_recommendation: DecisionRecommendation`
  - `user_decision: DecisionRecommendation`
  - `fit_score: float`
  - `selected_strategy: Optional[str]`
  - `resume_id: Optional[str]`
  - `ats_score: Optional[float]`
  - `interview_prep_id: Optional[str]`
  - `application_status: ApplicationStatus`
  - `date_added: str`
  - `date_applied: Optional[str]`
  - `interview_status: Optional[str]`
  - `notes: List[str]`
  - `resume_versions: List[ResumeVersionRecord]`
  - `next_action: str`
- **Producer:** `ApplicationRepository.create_application()`
- **Consumers:** All UI pages, Analytics, Session Store.
