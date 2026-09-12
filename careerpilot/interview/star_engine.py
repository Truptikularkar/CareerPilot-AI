import uuid
from typing import List, Dict, Any, Tuple
from careerpilot.core.constants import (
    QuestionCategory,
    QuestionPriority,
    DifficultyLevel,
)
from careerpilot.models.interview import InterviewQuestion, STARAnswer
from careerpilot.core.logging import get_logger

logger = get_logger(__name__)


class STAREngine:
    """
    Formulates evidence-grounded STAR behavioral interview answers.
    Enforces truth rules: if candidate evidence is lacking, returns INSUFFICIENT_EVIDENCE
    instead of inventing fictitious conflicts, people, or corporate events.
    """

    @classmethod
    def generate_star_questions_and_answers(cls) -> Tuple[List[InterviewQuestion], List[STARAnswer]]:
        questions: List[InterviewQuestion] = []
        star_answers: List[STARAnswer] = []

        # Story 1: Data Quality Incident & Performance Optimization (STAR)
        q1_id = f"q_star_{uuid.uuid4().hex[:8]}"
        s1_id = f"star_{uuid.uuid4().hex[:8]}"

        q1 = InterviewQuestion(
            question_id=q1_id,
            category=QuestionCategory.BEHAVIORAL,
            subcategory="Problem Solving & Data Quality",
            question="Tell me about a time you identified and resolved a recurring data quality issue in a production pipeline.",
            difficulty=DifficultyLevel.MEDIUM,
            priority=QuestionPriority.HIGH,
            why_this_question="Behavioral check on engineering rigor, data validation mindset, and proactive problem solving.",
            source_requirements=["Data Quality", "Production Operations", "Problem Solving"],
            candidate_evidence_ids=["EXP_COGNIZANT_002", "PROJ_DATA_QUALITY"],
            expected_topics=["Root cause identification", "Validation framework implementation", "Measurable quality improvement"],
            interviewer_intent="Evaluate how the candidate handles corrupt data upstream and prevents bad data from reaching downstream consumers.",
            follow_up_questions=[
                "How did you establish anomaly thresholds without overwhelming the on-call team with false positives?",
                "What did you learn about schema drift communication with upstream source teams?",
            ],
            answer_template_id=s1_id,
        )

        star1 = STARAnswer(
            star_id=s1_id,
            question_id=q1_id,
            situation="At Cognizant, downstream analytics reports were intermittently impacted by null values, unexpected schema shifts, and duplicated records from source ingestion feeds.",
            task="I needed to build an automated validation mechanism to catch anomalies at ingestion rather than waiting for business users to report data errors.",
            action=(
                "I designed and deployed automated data quality validation DAGs in Apache Airflow executing post-ingestion rule checks (null checks, range validation, row-count reconciliation) across BigQuery tables. "
                "Additionally, I integrated BigQuery ML statistical anomaly detection to flag distribution drifts before data entered reporting data marts."
            ),
            result="Achieved a verified ~35% reduction in production data quality incidents and eliminated bad data from reaching executive reporting dashboards.",
            key_takeaway="Proactive automated validation at the ingestion boundary is significantly cheaper and more reliable than reactive post-production fixes.",
            is_insufficient_evidence=False,
            grounded_evidence_ids=["EXP_COGNIZANT_002", "PROJ_DATA_QUALITY"],
        )
        questions.append(q1)
        star_answers.append(star1)

        # Story 2: Pipeline Failure & Root Cause Triage (STAR)
        q2_id = f"q_star_{uuid.uuid4().hex[:8]}"
        s2_id = f"star_{uuid.uuid4().hex[:8]}"

        q2 = InterviewQuestion(
            question_id=q2_id,
            category=QuestionCategory.BEHAVIORAL,
            subcategory="Incident Management & Innovation",
            question="Tell me about a production pipeline failure you faced and how you handled the recovery.",
            difficulty=DifficultyLevel.HARD,
            priority=QuestionPriority.CRITICAL,
            why_this_question="Evaluates candidate's incident triage, calm execution under failure, and long-term automation mindset.",
            source_requirements=["Airflow", "Incident Response", "AI Automation"],
            candidate_evidence_ids=["PROJ_AUTOHEAL_AGENT", "EXP_COGNIZANT_003"],
            expected_topics=["Failure diagnosis", "Temporary workaround vs permanent fix", "GenAI automated error triage"],
            interviewer_intent="Observe whether the candidate panics or uses failures as opportunities to build resilient automation.",
            follow_up_questions=[
                "How did you prevent the self-healing agent from retrying permanent schema errors?",
                "What was the team's reaction to adopting an LLM-assisted triage workflow?",
            ],
            answer_template_id=s2_id,
        )

        star2 = STARAnswer(
            star_id=s2_id,
            question_id=q2_id,
            situation="Our daily Airflow batch pipelines experienced transient network timeouts and lock contention during peak hours, waking up on-call engineers for manual DAG restarts.",
            task="I wanted to automate the classification of transient vs permanent failures and reduce the mean time to recovery (MTTR).",
            action=(
                "I engineered an autonomous AI Root-Cause Analysis agent using Google Vertex AI / Gemini API. "
                "The agent parsed raw Airflow task execution logs upon failure, classified error patterns (e.g. transient connection timeout vs deterministic syntax error), and automatically triggered safe retries with exponential backoff for known transient conditions while alerting on-call engineers with a root-cause summary for genuine code bugs."
            ),
            result="The agent successfully auto-healed ~75% of transient failure incidents and reduced on-call incident response time by ~60%.",
            key_takeaway="Combining robust logging with intelligent classification turns reactive operational firefighting into self-healing infrastructure.",
            is_insufficient_evidence=False,
            grounded_evidence_ids=["PROJ_AUTOHEAL_AGENT", "EXP_COGNIZANT_003"],
        )
        questions.append(q2)
        star_answers.append(star2)

        # Story 3: Performance Optimization & Cost Reduction (STAR)
        q3_id = f"q_star_{uuid.uuid4().hex[:8]}"
        s3_id = f"star_{uuid.uuid4().hex[:8]}"

        q3 = InterviewQuestion(
            question_id=q3_id,
            category=QuestionCategory.BEHAVIORAL,
            subcategory="Cost Optimization & Performance",
            question="Describe a situation where you proactively improved pipeline performance or reduced cloud computing costs.",
            difficulty=DifficultyLevel.MEDIUM,
            priority=QuestionPriority.HIGH,
            why_this_question="Tests cloud financial awareness (FinOps) and technical depth in BigQuery database tuning.",
            source_requirements=["BigQuery", "SQL Optimization", "Cost Efficiency"],
            candidate_evidence_ids=["EXP_COGNIZANT_005", "ACHIEVEMENT_BQ_COST"],
            expected_topics=["Query profiling", "Partitioning vs clustering", "Verified cost savings metrics"],
            interviewer_intent="See if candidate writes queries blindly or actively profiles byte scans and slot utilization.",
            follow_up_questions=[
                "How did you determine the optimal clustering columns for your workload?",
                "How do you prevent other engineers from executing expensive SELECT * queries on partitioned tables?",
            ],
            answer_template_id=s3_id,
        )

        star3 = STARAnswer(
            star_id=s3_id,
            question_id=q3_id,
            situation="As daily transaction volume grew to ~500k+ records, frequent analytical queries across historical BigQuery tables were scanning terabytes of unneeded data, increasing GCP processing costs.",
            task="My objective was to optimize table structures and rewrite critical reporting queries to minimize scanned bytes without compromising query SLA.",
            action=(
                "I analyzed query execution execution plans in BigQuery Information Schema to identify high-cost scans. "
                "I implemented ingestion-time date partitioning and clustered tables on high-cardinality filter fields (such as customer_id and transaction_type). "
                "I also enforced partition pruning filters across all scheduled Airflow SQL operators."
            ),
            result="Reduced BigQuery query processing costs by a verified ~25% and accelerated daily dashboard generation times.",
            key_takeaway="Storage architecture decisions (partitioning + clustering) in cloud data warehouses directly determine compute economics.",
            is_insufficient_evidence=False,
            grounded_evidence_ids=["EXP_COGNIZANT_005", "ACHIEVEMENT_BQ_COST"],
        )
        questions.append(q3)
        star_answers.append(star3)

        # Story 4: Insufficient Evidence Example (Handling unevidenced executive/management scenarios)
        q4_id = f"q_star_{uuid.uuid4().hex[:8]}"
        s4_id = f"star_{uuid.uuid4().hex[:8]}"

        q4 = InterviewQuestion(
            question_id=q4_id,
            category=QuestionCategory.BEHAVIORAL,
            subcategory="Executive Negotiation",
            question="Tell me about a time you negotiated vendor contracts and SLA terms with an external SaaS data provider.",
            difficulty=DifficultyLevel.HARD,
            priority=QuestionPriority.LOW,
            why_this_question="Assesses executive commercial negotiation experience.",
            source_requirements=["Vendor Management"],
            candidate_evidence_ids=[],
            expected_topics=["Commercial negotiation", "Vendor SLAs"],
            interviewer_intent="Test senior leadership commercial exposure.",
            follow_up_questions=[],
            answer_template_id=s4_id,
        )

        star4 = STARAnswer(
            star_id=s4_id,
            question_id=q4_id,
            situation="INSUFFICIENT_EVIDENCE",
            task="",
            action="",
            result="",
            key_takeaway="",
            is_insufficient_evidence=True,
            insufficient_evidence_reason=(
                "Candidate has 1.9+ years as Programmer Analyst focused on hands-on data pipeline engineering. "
                "No verified record of executive vendor contract negotiations in candidate ground truth. "
                "Recommendation: Pivot to technical SLA definition with internal stakeholders."
            ),
            grounded_evidence_ids=[],
        )
        questions.append(q4)
        star_answers.append(star4)

        return questions, star_answers
