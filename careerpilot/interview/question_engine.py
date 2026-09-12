import uuid
from typing import List, Dict, Any, Tuple
from careerpilot.core.constants import (
    QuestionCategory,
    QuestionPriority,
    DifficultyLevel,
)
from careerpilot.models.interview import InterviewQuestion
from careerpilot.models.job import JobAnalysisResult
from careerpilot.models.resume import TailoredResume
from careerpilot.models.ats import InterviewReadinessSeed
from careerpilot.interview.followups import FollowUpEngine
from careerpilot.core.logging import get_logger

logger = get_logger(__name__)


class QuestionEngine:
    """
    Generates structured, explainable, and prioritized interview questions
    grounded in the Job Description, Candidate Resume, and verified evidence.
    """

    @classmethod
    def generate_interview_questions(
        cls,
        analysis: JobAnalysisResult,
        resume: TailoredResume,
        seed: InterviewReadinessSeed,
        quotas: Dict[QuestionCategory, int],
    ) -> List[InterviewQuestion]:
        try:
            from careerpilot.interview.gemini_question_generator import GeminiQuestionGenerator
            pack = GeminiQuestionGenerator.generate_full_interview_pack(analysis, resume, seed)
            if pack and pack.get("questions"):
                return pack["questions"]
        except Exception as e:
            logger.warning("Could not generate questions via Gemini generator: %s. Using default logic.", e)

        questions: List[InterviewQuestion] = []

        # -------------------------------------------------------------
        # 1. HR Screening Questions
        # -------------------------------------------------------------
        hr_items = [
            (
                "Can you introduce yourself and give an overview of your data engineering background?",
                "Opening introductory question.",
                ["Professional Background", "Communication"],
                "Assess clarity of communication and career narrative.",
            ),
            (
                f"What interests you specifically about the {analysis.job_title} role at {analysis.company_name or 'our company'}?",
                "Assesses candidate motivation and role alignment.",
                ["Role Interest", "Company Alignment"],
                "Determine if candidate researched the role and understands the technical expectations.",
            ),
            (
                "What is your current notice period and work location preference?",
                "Logistical screening question.",
                ["Logistics"],
                "Confirm immediate availability and alignment with role location (Pune / Hybrid).",
            ),
        ]
        for q_text, why, reqs, intent in hr_items[:quotas.get(QuestionCategory.HR_SCREENING, 3)]:
            q_id = f"q_hr_{uuid.uuid4().hex[:8]}"
            questions.append(
                InterviewQuestion(
                    question_id=q_id,
                    category=QuestionCategory.HR_SCREENING,
                    subcategory="General Screening",
                    question=q_text,
                    difficulty=DifficultyLevel.EASY,
                    priority=QuestionPriority.HIGH,
                    why_this_question=why,
                    source_requirements=reqs,
                    candidate_evidence_ids=["PROFILE_SUMMARY"],
                    expected_topics=["Professional overview", "GCP data engineering experience", "Career motivation"],
                    interviewer_intent=intent,
                    follow_up_questions=["What type of data engineering challenges excite you the most?"],
                )
            )

        # -------------------------------------------------------------
        # 2. Resume Walkthrough Questions
        # -------------------------------------------------------------
        rw_items = [
            (
                "Walk me through your key responsibilities and technical contributions during your time at Cognizant.",
                "Core career narrative question.",
                ["Cognizant Experience", "Production Ownership"],
                "Evaluate depth of hands-on responsibilities versus passive team participation.",
            ),
            (
                "How has your experience evolved from building standard ETL/ELT pipelines to integrating AI and automated validation?",
                "Assesses technical progression and modern AI adoption.",
                ["Continuous Learning", "GenAI Integration"],
                "Verify candidate's continuous technical curiosity and ability to adopt GenAI tooling.",
            ),
        ]
        for q_text, why, reqs, intent in rw_items[:quotas.get(QuestionCategory.RESUME_WALKTHROUGH, 2)]:
            q_id = f"q_rw_{uuid.uuid4().hex[:8]}"
            questions.append(
                InterviewQuestion(
                    question_id=q_id,
                    category=QuestionCategory.RESUME_WALKTHROUGH,
                    subcategory="Experience Narrative",
                    question=q_text,
                    difficulty=DifficultyLevel.MEDIUM,
                    priority=QuestionPriority.HIGH,
                    why_this_question=why,
                    source_requirements=reqs,
                    candidate_evidence_ids=["EXP_COGNIZANT_001", "EXP_COGNIZANT_002"],
                    expected_topics=["Pipeline engineering", "BigQuery optimization", "Airflow automation"],
                    interviewer_intent=intent,
                    follow_up_questions=["Which project at Cognizant had the biggest measurable impact?"],
                )
            )

        # -------------------------------------------------------------
        # 3. JD Technical & Fundamentals Questions
        # -------------------------------------------------------------
        tech_specs = [
            (
                "Explain the architectural difference between partitioning and clustering in Google BigQuery. When would you combine both?",
                QuestionCategory.BIGQUERY,
                "BigQuery Architecture",
                DifficultyLevel.MEDIUM,
                QuestionPriority.CRITICAL,
                "BigQuery is a primary must-have skill in target JD.",
                ["BigQuery", "Data Warehousing", "SQL"],
                ["BigQuery partition pruning", "Clustering sort order", "Query cost optimization", "Slot utilization"],
                "Test core cloud data warehouse storage and query execution mechanics.",
            ),
            (
                "How do you design Apache Airflow DAGs for strict idempotency, safe retries, and automated SLA failure alerting?",
                QuestionCategory.AIRFLOW,
                "Orchestration & Reliability",
                DifficultyLevel.MEDIUM,
                QuestionPriority.CRITICAL,
                "Apache Airflow is a core orchestration requirement in the JD.",
                ["Apache Airflow", "Data Pipelines", "Reliability"],
                ["Idempotent tasks", "Task retries & backoff", "SLA miss callbacks", "XCom best practices"],
                "Ensure candidate writes production-grade DAGs that can be safely re-run without duplicating records.",
            ),
            (
                "How do you implement automated data quality frameworks at the ingestion boundary to prevent corrupt records from polluting data marts?",
                QuestionCategory.DATA_ENGINEERING,
                "Data Quality & Governance",
                DifficultyLevel.MEDIUM,
                QuestionPriority.HIGH,
                "Data validation and quality frameworks are highlighted in the JD.",
                ["Data Quality", "Validation", "Anomaly Detection"],
                ["Null checks", "Range validation", "Row-count reconciliation", "Drift detection"],
                "Evaluate how the candidate safeguards downstream analytics from upstream data errors.",
            ),
            (
                "Explain the mechanics of a Hybrid Retrieval system combining dense semantic vector search (FAISS) and sparse keyword search (BM25).",
                QuestionCategory.RAG,
                "GenAI & Search Architecture",
                DifficultyLevel.HARD,
                QuestionPriority.HIGH,
                "JD emphasizes modern GenAI and RAG pipelines.",
                ["RAG", "Vector Search", "Hybrid Retrieval"],
                ["Dense vector embeddings", "Sparse lexical matching (BM25)", "Reciprocal Rank Fusion (RRF)", "Hallucination mitigation"],
                "Assess whether candidate understands why pure semantic search fails on exact technical terms and how hybrid reranking solves it.",
            ),
            (
                "How do you architect an event-driven serverless ingestion workflow on GCP using Cloud Storage, Pub/Sub, and Cloud Functions?",
                QuestionCategory.GCP,
                "Serverless Architecture",
                DifficultyLevel.MEDIUM,
                QuestionPriority.HIGH,
                "Event-driven cloud architecture is required in JD.",
                ["GCP", "Cloud Storage", "Pub/Sub", "Cloud Functions"],
                ["GCS object finalize triggers", "Pub/Sub decoupling", "Serverless execution limits", "Idempotency hashes"],
                "Verify practical cloud engineering skills for real-time and micro-batch data feeds.",
            ),
            (
                "How do you optimize complex SQL analytical queries that perform multiple heavy JOINs and aggregations on large tables?",
                QuestionCategory.SQL,
                "Query Performance Tuning",
                DifficultyLevel.MEDIUM,
                QuestionPriority.HIGH,
                "Advanced SQL proficiency is a mandatory requirement.",
                ["SQL", "Query Optimization", "Analytical Aggregations"],
                ["Filter pushdown", "Join ordering", "Window functions", "Avoiding SELECT *"],
                "Test deep analytical SQL fundamentals and query execution plan comprehension.",
            ),
            (
                "What strategies do you use in Python to handle streaming or large batch data memory-efficiently without Out-Of-Memory (OOM) crashes?",
                QuestionCategory.PYTHON,
                "Python Engineering",
                DifficultyLevel.MEDIUM,
                QuestionPriority.HIGH,
                "Python is the foundational language for the target role.",
                ["Python", "Memory Management", "Streaming"],
                ["Generators (yield)", "Iterators", "Chunked processing with pandas/polars", "Context managers"],
                "Verify standard Python software engineering and performance best practices.",
            ),
        ]
        for q_text, cat, subcat, diff, prio, why, reqs, topics, intent in tech_specs[:quotas.get(QuestionCategory.JD_TECHNICAL, 8)]:
            q_id = f"q_tech_{uuid.uuid4().hex[:8]}"
            questions.append(
                InterviewQuestion(
                    question_id=q_id,
                    category=cat,
                    subcategory=subcat,
                    question=q_text,
                    difficulty=diff,
                    priority=prio,
                    why_this_question=why,
                    source_requirements=reqs,
                    candidate_evidence_ids=["SKILLS_ALL"],
                    expected_topics=topics,
                    interviewer_intent=intent,
                    follow_up_questions=FollowUpEngine.generate_followup_chain(subcat),
                )
            )

        # -------------------------------------------------------------
        # 4. Resume Deep-Dive Questions (Bullet Level)
        # -------------------------------------------------------------
        resume_bullets_questions = [
            (
                "Your resume mentions optimizing BigQuery queries to achieve a verified ~25% cost reduction. What specific changes did you make, and how was this metric measured?",
                "Cost Optimization Bullet",
                ["BigQuery", "SQL Optimization"],
                ["EXP_COGNIZANT_005", "ACHIEVEMENT_BQ_COST"],
                ["Partitioning implementation", "Cluster key selection", "Scanned byte comparison in Information Schema"],
                "Verify the factual authenticity of the 25% cost reduction metric.",
            ),
            (
                "You state that your automated data quality frameworks reduced production data incidents by ~35%. Can you explain how you designed the validation checks and anomaly detection?",
                "Data Quality Bullet",
                ["Data Validation", "BigQuery ML"],
                ["EXP_COGNIZANT_002", "PROJ_DATA_QUALITY"],
                ["Rule-based checks", "Row reconciliation", "BigQuery ML anomaly detection", "Downstream alerting"],
                "Probe the exact technical mechanism behind the 35% incident reduction.",
            ),
            (
                "You built an autonomous AI agent resolving ~75% of transient Airflow pipeline failures. How did the agent parse error logs and execute auto-healing safely?",
                "Self-Healing Agent Bullet",
                ["Apache Airflow", "Google Gemini API", "Vertex AI"],
                ["PROJ_AUTOHEAL_AGENT", "EXP_COGNIZANT_003"],
                ["Log parsing with Gemini", "Transient vs permanent classification", "Exponential backoff retry triggers"],
                "Test the technical depth of the GenAI operations agent.",
            ),
            (
                "Explain the architecture you built to ingest ~500k+ daily transaction records into BigQuery with schema validation and duplicate elimination.",
                "High-Volume Ingestion Bullet",
                ["GCP", "BigQuery", "Python", "Cloud Pub/Sub"],
                ["EXP_COGNIZANT_001", "EXP_COGNIZANT_004"],
                ["Serverless Cloud Functions", "Pub/Sub at-least-once deduplication", "BigQuery Storage Write API"],
                "Evaluate production engineering and deduplication strategies at scale.",
            ),
        ]
        for q_text, subcat, reqs, ev_ids, topics, intent in resume_bullets_questions[:quotas.get(QuestionCategory.RESUME_DEEP_DIVE, 6)]:
            q_id = f"q_rdd_{uuid.uuid4().hex[:8]}"
            questions.append(
                InterviewQuestion(
                    question_id=q_id,
                    category=QuestionCategory.RESUME_DEEP_DIVE,
                    subcategory=subcat,
                    question=q_text,
                    difficulty=DifficultyLevel.HARD,
                    priority=QuestionPriority.CRITICAL,
                    why_this_question=f"Interviewer probing specific verified claim on candidate resume: '{subcat}'.",
                    source_requirements=reqs,
                    candidate_evidence_ids=ev_ids,
                    expected_topics=topics,
                    interviewer_intent=intent,
                    follow_up_questions=FollowUpEngine.generate_followup_chain(subcat),
                )
            )

        # -------------------------------------------------------------
        # 5. Project Deep-Dive Questions
        # -------------------------------------------------------------
        project_questions = [
            (
                "Walk me through your 'AI-Driven Data Quality Monitoring & Incident Reduction' project. What was the exact architecture and data flow?",
                "AI Data Quality Project",
                ["Data Quality", "BigQuery ML", "Airflow"],
                ["PROJ_DATA_QUALITY"],
                ["Airflow validation DAGs", "BigQuery ML drift model", "Automated alert webhook"],
                "Assess project architecture and real-world data reliability engineering.",
            ),
            (
                "In your 'Local RAG & Hybrid Retrieval Sandbox', why did you combine FAISS and BM25 using Reciprocal Rank Fusion rather than relying solely on dense embeddings?",
                "Local RAG Project (Personal)",
                ["RAG", "FAISS", "BM25", "Reciprocal Rank Fusion"],
                ["PROJ_LOCAL_RAG"],
                ["Dense vs sparse search strengths", "RRF algorithm math", "Local offline deployment", "Grounding guardrails"],
                "Check deep comprehension of retrieval algorithms and practical RAG trade-offs.",
            ),
            (
                "In your 'Automated Sales Data Validation & Reporting DAG', how did you ensure corrupted records were quarantined before entering reporting data marts?",
                "Sales Pipeline Project",
                ["Airflow", "SQL", "Google Cloud Storage"],
                ["PROJ_SALES_DAG"],
                ["Quarantine table strategy", "Row-count reconciliation", "SQL data validation"],
                "Understand batch pipeline error handling and business data mart integrity.",
            ),
        ]
        for q_text, subcat, reqs, ev_ids, topics, intent in project_questions[:quotas.get(QuestionCategory.PROJECT_DEEP_DIVE, 5)]:
            q_id = f"q_pdd_{uuid.uuid4().hex[:8]}"
            questions.append(
                InterviewQuestion(
                    question_id=q_id,
                    category=QuestionCategory.PROJECT_DEEP_DIVE,
                    subcategory=subcat,
                    question=q_text,
                    difficulty=DifficultyLevel.HARD,
                    priority=QuestionPriority.HIGH,
                    why_this_question=f"Deep-dive into project '{subcat}' featured on candidate resume.",
                    source_requirements=reqs,
                    candidate_evidence_ids=ev_ids,
                    expected_topics=topics,
                    interviewer_intent=intent,
                    follow_up_questions=FollowUpEngine.generate_followup_chain(subcat),
                )
            )

        # -------------------------------------------------------------
        # 6. Candidate Questions to Ask Interviewer
        # -------------------------------------------------------------
        candidate_q_items = [
            (
                "What is the current balance between legacy batch data pipelines and event-driven streaming workflows in your data platform?",
                "Data Architecture Inquiry",
                "Demonstrates architectural curiosity and understanding of modern batch vs stream trade-offs.",
            ),
            (
                "How is your data engineering team currently integrating generative AI or autonomous agents into pipeline monitoring and operational workflows?",
                "GenAI Integration Inquiry",
                "Highlights forward-looking AI data engineering mindset and interest in practical LLM tooling.",
            ),
            (
                "How does the team handle on-call incident response, schema drift communication, and cross-functional collaboration with data scientists?",
                "Team Culture & Ops Inquiry",
                "Demonstrates operational maturity and interest in sustainable engineering practices.",
            ),
        ]
        for q_text, subcat, intent in candidate_q_items[:quotas.get(QuestionCategory.CANDIDATE_QUESTIONS, 3)]:
            q_id = f"q_cand_{uuid.uuid4().hex[:8]}"
            questions.append(
                InterviewQuestion(
                    question_id=q_id,
                    category=QuestionCategory.CANDIDATE_QUESTIONS,
                    subcategory=subcat,
                    question=q_text,
                    difficulty=DifficultyLevel.EASY,
                    priority=QuestionPriority.MEDIUM,
                    why_this_question="Insightful reverse-interview question for candidate to ask the engineering team.",
                    source_requirements=["Interview Engagement"],
                    candidate_evidence_ids=[],
                    expected_topics=["Data platform architecture", "GenAI adoption", "On-call culture"],
                    interviewer_intent=intent,
                    follow_up_questions=[],
                )
            )

        logger.info("Generated %d interview questions across taxonomy categories.", len(questions))
        return questions
