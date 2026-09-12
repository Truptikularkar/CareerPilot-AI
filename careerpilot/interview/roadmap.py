import uuid
from typing import List, Dict, Any
from careerpilot.models.interview import PreparationRoadmap, PreparationDayPlan, InterviewQuestion
from careerpilot.models.job import JobAnalysisResult
from careerpilot.models.resume import TailoredResume
from careerpilot.models.ats import InterviewReadinessSeed
from careerpilot.core.logging import get_logger

logger = get_logger(__name__)


class RoadmapGenerator:
    """
    Generates configurable 1-day, 3-day, 7-day, and 14-day study roadmaps
    prioritizing actual JD gaps, verified metrics, and core system design challenges.
    """

    @classmethod
    def generate_roadmap(
        cls,
        analysis: JobAnalysisResult,
        resume: TailoredResume,
        seed: InterviewReadinessSeed,
        questions: List[InterviewQuestion],
        days_total: int = 7,
    ) -> PreparationRoadmap:
        roadmap_id = f"roadmap_{uuid.uuid4().hex[:8]}"
        schedule: List[PreparationDayPlan] = []

        if days_total == 1:
            # Intensive 1-day crash preparation
            schedule.append(
                PreparationDayPlan(
                    day_number=1,
                    title="Intensive High-Priority JD & Resume Alignment",
                    focus_areas=[
                        "Master 90-second Resume Walkthrough emphasizing verified Cognizant impact.",
                        "Rehearse BigQuery cost optimization (25%) and Airflow auto-heal (75%) metrics.",
                        "Review transferable cloud framing for unverified JD gaps (GCP -> AWS).",
                        "Practice 3 core STAR stories (Data Quality, Pipeline Failure, Cost Tuning).",
                    ],
                    target_question_ids=[q.question_id for q in questions[:10]],
                    practice_drills=[
                        "Record your 90-second career elevator pitch and ensure verified metrics flow naturally.",
                        "Draw the GCS -> Pub/Sub -> Cloud Functions -> BigQuery event-driven architecture on a whiteboard.",
                    ],
                )
            )
        elif days_total == 3:
            # 3-day fast-track roadmap
            schedule.extend([
                PreparationDayPlan(
                    day_number=1,
                    title="Core Fundamentals, Resume Deep-Dives & Metrics",
                    focus_areas=[
                        "Master opening HR screening and Cognizant career trajectory.",
                        "Defend verified ~25% BigQuery cost reduction and ~35% data quality incident reduction.",
                        "Explain BigQuery partition filters versus clustering column order.",
                    ],
                    target_question_ids=[q.question_id for q in questions if "resume" in q.category.value.lower() or "hr" in q.category.value.lower()][:6],
                    practice_drills=["Practice explaining the 25% cost reduction without relying on scripted notes."],
                ),
                PreparationDayPlan(
                    day_number=2,
                    title="Data Pipelines, GenAI / RAG & Cloud Architecture",
                    focus_areas=[
                        "Airflow DAG idempotency, task retry policies, and SLA miss callbacks.",
                        "Hybrid RAG mechanics: dense FAISS + sparse BM25 + Reciprocal Rank Fusion (RRF).",
                        "Event-driven serverless ingestion: Cloud Storage, Pub/Sub, Cloud Functions.",
                    ],
                    target_question_ids=[q.question_id for q in questions if "tech" in q.category.value.lower() or "rag" in q.category.value.lower()][:6],
                    practice_drills=["Step through the mathematical logic of Reciprocal Rank Fusion (RRF)."],
                ),
                PreparationDayPlan(
                    day_number=3,
                    title="System Design, Behavioral STAR & Cloud Gap Mastery",
                    focus_areas=[
                        "Walk through end-to-end System Design for 500k+ daily transactions.",
                        "Deliver 3 structured STAR behavioral answers.",
                        "Frame GCP to AWS cloud transferability with confidence.",
                    ],
                    target_question_ids=[q.question_id for q in questions if "star" in q.question_id or "gap" in q.question_id][:6],
                    practice_drills=["Simulate answering: 'Why should we hire you over candidates with AWS experience?'"],
                ),
            ])
        else:
            # Standard 7-day or 14-day comprehensive roadmap (default 7 days)
            schedule.extend([
                PreparationDayPlan(
                    day_number=1,
                    title="Day 1: Role Overview, Career Narrative & Resume Walkthrough",
                    focus_areas=[
                        "Refine 90-second elevator pitch connecting Cognizant background to target JD.",
                        "Review target job responsibilities and verify alignment with resume strategy.",
                        "Rehearse conversational answers for opening screening questions.",
                    ],
                    target_question_ids=[q.question_id for q in questions if q.category.value in ("HR_SCREENING", "RESUME_WALKTHROUGH")],
                    practice_drills=["Speak your resume walkthrough aloud 3 times, timing yourself under 90 seconds."],
                ),
                PreparationDayPlan(
                    day_number=2,
                    title="Day 2: Core Data Engineering & BigQuery Deep-Dives",
                    focus_areas=[
                        "BigQuery internal storage architecture: physical partitioning vs clustering.",
                        "Query profiling using BigQuery Information Schema.",
                        "Defending the verified ~25% query cost optimization metric.",
                    ],
                    target_question_ids=[q.question_id for q in questions if "bigquery" in q.question.lower() or "sql" in q.question.lower()][:5],
                    practice_drills=["Write a sample SQL query utilizing partition filters and window functions."],
                ),
                PreparationDayPlan(
                    day_number=3,
                    title="Day 3: Pipeline Orchestration & Self-Healing Workflows (Airflow)",
                    focus_areas=[
                        "Idempotent Airflow DAG engineering and backfill safety.",
                        "Failure triage: exponential backoff retries vs permanent error alerting.",
                        "GenAI Root-Cause Analysis Agent resolving ~75% of transient Airflow errors.",
                    ],
                    target_question_ids=[q.question_id for q in questions if "airflow" in q.question.lower()][:5],
                    practice_drills=["Trace the execution flow of the AI AutoHeal agent parsing worker logs."],
                ),
                PreparationDayPlan(
                    day_number=4,
                    title="Day 4: Generative AI, Hybrid RAG & Vector Search",
                    focus_areas=[
                        "Local RAG Sandbox architecture: FAISS dense vectors + BM25 sparse lexical search.",
                        "Reciprocal Rank Fusion (RRF) algorithm and reranking mechanics.",
                        "Anti-hallucination grounding guardrails and entity verification.",
                    ],
                    target_question_ids=[q.question_id for q in questions if "rag" in q.question.lower() or "hybrid" in q.question.lower()][:5],
                    practice_drills=["Explain why dense semantic vectors struggle on exact model numbers and how BM25 fixes it."],
                ),
                PreparationDayPlan(
                    day_number=5,
                    title="Day 5: Role-Specific System Design Scenarios",
                    focus_areas=[
                        "Event-driven ingestion architecture (GCS -> Pub/Sub -> Cloud Functions -> BigQuery).",
                        "Handling 500k+ daily records, deduplication hashes, and Dead-Letter Queues.",
                        "Non-functional requirements: latency, SLA, failure recovery, cost scaling to zero.",
                    ],
                    target_question_ids=[q.question_id for q in questions if q.category.value == "SYSTEM_DESIGN"][:4],
                    practice_drills=["Sketch the complete ingestion and validation data flow on paper in under 10 minutes."],
                ),
                PreparationDayPlan(
                    day_number=6,
                    title="Day 6: Behavioral Mastery (STAR) & Cloud Gap Navigation",
                    focus_areas=[
                        "Deliver STAR stories for Data Quality (~35% reduction), Failure Recovery (~75% auto-heal), and Cost Tuning (~25%).",
                        "GCP to AWS cloud service mapping and transferability framing.",
                        "Addressing 1.9+ years tenure with proven production delivery metrics.",
                    ],
                    target_question_ids=[q.question_id for q in questions if q.category.value in ("BEHAVIORAL", "EXPERIENCE_GAP")][:5],
                    practice_drills=["Practice answering: 'How would you build this on AWS instead of GCP?' with zero hesitation."],
                ),
                PreparationDayPlan(
                    day_number=7,
                    title="Day 7: Full Mock Simulation & Reverse Questions for Interviewer",
                    focus_areas=[
                        "Simulate an end-to-end 45-minute technical and behavioral mock interview.",
                        "Review follow-up challenge questions for edge cases.",
                        "Finalize 3 insightful questions to ask the hiring team.",
                    ],
                    target_question_ids=[q.question_id for q in questions if q.category.value == "CANDIDATE_QUESTIONS"],
                    practice_drills=["Review your final preparation notes and take a restful break before the real interview."],
                ),
            ])

        return PreparationRoadmap(
            roadmap_id=roadmap_id,
            days_total=days_total,
            target_role=resume.strategy.target_role,
            daily_schedule=schedule,
        )
