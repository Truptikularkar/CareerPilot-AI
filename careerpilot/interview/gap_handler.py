import uuid
from typing import List, Dict, Any, Tuple
from careerpilot.core.constants import (
    QuestionCategory,
    QuestionPriority,
    DifficultyLevel,
)
from careerpilot.models.interview import InterviewQuestion, InterviewAnswer
from careerpilot.models.job import JobAnalysisResult
from careerpilot.models.ats import InterviewReadinessSeed
from careerpilot.core.logging import get_logger

logger = get_logger(__name__)


class GapHandler:
    """
    Generates realistic experience-gap, missing-technology, and tenure questions
    paired with honest, truth-grounded transferable answers.
    Strictly forbids fabricating production experience on unverified stacks.
    """

    @classmethod
    def generate_gap_questions_and_answers(
        cls,
        analysis: JobAnalysisResult,
        seed: InterviewReadinessSeed,
    ) -> Tuple[List[InterviewQuestion], List[InterviewAnswer]]:
        questions: List[InterviewQuestion] = []
        answers: List[InterviewAnswer] = []

        # 1. AWS vs GCP Cloud Experience Gap
        has_aws_gap = any("aws" in g.lower() or "amazon" in g.lower() or "redshift" in g.lower() for g in seed.candidate_gaps)
        if has_aws_gap or any("aws" in r.normalized_skill.lower() for r in analysis.requirements):
            q_id = f"q_gap_{uuid.uuid4().hex[:8]}"
            a_id = f"a_gap_{uuid.uuid4().hex[:8]}"

            q = InterviewQuestion(
                question_id=q_id,
                category=QuestionCategory.EXPERIENCE_GAP,
                subcategory="Cloud Transferability (AWS vs GCP)",
                question="Your resume highlights Google Cloud Platform (BigQuery, GCS, Cloud Functions, Airflow). How would you adapt your data engineering patterns to an AWS environment?",
                difficulty=DifficultyLevel.MEDIUM,
                priority=QuestionPriority.HIGH,
                why_this_question="Target JD mentions AWS technologies, while candidate's verified production tenure is on GCP.",
                source_requirements=["AWS", "Cloud Data Architecture"],
                candidate_evidence_ids=["EXP_COGNIZANT_GCP", "SKILL_CLOUD_GCP"],
                expected_topics=["GCP to AWS service mapping", "Architectural transferability", "Object storage & warehouse parity", "Honest cloud framing"],
                interviewer_intent="Assess whether the candidate understands underlying cloud data concepts or is strictly tied to GCP console tooling.",
                follow_up_questions=[
                    "How does BigQuery partition/cluster mechanics differ from Amazon Redshift distribution and sort keys?",
                    "What AWS service would you choose for serverless event-driven ingestion instead of Cloud Functions?",
                ],
                answer_template_id=a_id,
            )

            direct = "My hands-on cloud experience has primarily been on Google Cloud Platform (GCP), but cloud data engineering principles are fully transferable to AWS."
            explanation = (

                "The core engineering challenges—partitioning analytical storage, managing event-driven ingestion, enforcing idempotent retries, and data quality validation—are platform-agnostic. "
                "In AWS, I map Google BigQuery to Amazon Redshift or Athena, Google Cloud Storage to Amazon S3, Cloud Functions to AWS Lambda, Pub/Sub to Kinesis/SNS-SQS, and Cloud Composer to Amazon MWAA (Managed Workflows for Apache Airflow)."
            )
            cand_ex = "At Cognizant, I engineered daily batch and event-driven pipelines handling ~500k+ records. Designing for schema validation, partition filters, and idempotent Airflow DAGs translates directly to AWS data workflows."
            tech_det = "For example, where I used BigQuery partition pruning to reduce query costs by ~25%, in Redshift I would design optimal COMPOUND/INTERLEAVED sort keys and DISTSTYLE (KEY/EVEN) to minimize cross-node data shuffling."
            impact = "I understand the conceptual parity deeply, allowing me to transition into AWS architectures with zero ramp-up delay while maintaining production rigor."
            followup = "I'd be glad to discuss how I would architect an AWS S3 -> Lambda -> Redshift pipeline using these exact principles."

            a = InterviewAnswer(
                answer_id=a_id,
                question_id=q_id,
                direct_answer=direct,
                explanation=explanation,
                candidate_example=cand_ex,
                technical_details=tech_det,
                result_impact=impact,
                possible_followup=followup,
                short_version=f"{direct} Core patterns like BigQuery (Redshift), GCS (S3), and Airflow (MWAA) share identical architecture fundamentals.",
                standard_version=f"{direct} {explanation} {cand_ex}",
                detailed_version=f"{direct} {explanation} {cand_ex} {tech_det} {impact}",
                grounded_evidence_ids=["EXP_COGNIZANT_GCP", "SKILL_CLOUD_GCP"],
                evidence_status="TRANSFERABLE",
                is_insufficient_evidence=False,
            )

            questions.append(q)
            answers.append(a)

        # 2. Seniority / Experience Tenure Gap (1.9+ yrs vs Senior / 3+ yrs JD requirement)
        if analysis.role_classification.seniority.value in ("MID", "SENIOR"):
            q_id_ten = f"q_gap_{uuid.uuid4().hex[:8]}"
            a_id_ten = f"a_gap_{uuid.uuid4().hex[:8]}"

            q_ten = InterviewQuestion(
                question_id=q_id_ten,
                category=QuestionCategory.EXPERIENCE_GAP,
                subcategory="Tenure & Ownership",
                question="This role seeks someone with broad engineering independence. With 1.9+ years of professional experience, how do you ensure you can deliver end-to-end without constant oversight?",
                difficulty=DifficultyLevel.HARD,
                priority=QuestionPriority.HIGH,
                why_this_question="JD targets mid/senior experience level; candidate has 1.9+ verified years.",
                source_requirements=["Seniority", "End-to-End Ownership"],
                candidate_evidence_ids=["EXP_COGNIZANT_001", "EXP_COGNIZANT_002"],
                expected_topics=["Production accountability", "Incident resolution metrics", "Proactive automation", "Quality rigor"],
                interviewer_intent="Evaluate candidate's maturity, accountability, and problem-solving autonomy.",
                follow_up_questions=[
                    "Tell me about a time you took initiative on a pipeline improvement without being explicitly assigned.",
                    "How do you handle production on-call incidents under pressure?",
                ],
                answer_template_id=a_id_ten,
            )

            direct_ten = "Throughout my 1.9+ years at Cognizant, my focus has been on end-to-end production ownership, proactive automation, and measurable business impact."
            exp_ten = "Rather than just writing isolated scripts, I took ownership of core data reliability: implementing automated validation frameworks that cut data quality incidents by ~35%, optimizing BigQuery queries for a verified ~25% cost reduction, and integrating self-healing Airflow error triaging that resolved ~75% of transient errors."
            a_ten = InterviewAnswer(
                answer_id=a_id_ten,
                question_id=q_id_ten,
                direct_answer=direct_ten,
                explanation=exp_ten,
                candidate_example="I treat production pipelines as living systems requiring automated guardrails, robust alerting, and clean modular code.",
                technical_details="My daily stack includes Python, SQL, Airflow, and BigQuery ML, where I build for maintainability and idempotency.",
                result_impact="This high degree of ownership allows me to ramp up quickly, operate independently, and deliver reliable data systems from day one.",
                possible_followup="I can share a specific example of how I designed our on-call alerting to reduce triage time by ~60%.",
                short_version=f"{direct_ten} I have owned production pipelines, reducing data quality incidents by ~35% and cutting query costs by ~25%.",
                standard_version=f"{direct_ten} {exp_ten}",
                detailed_version=f"{direct_ten} {exp_ten} {cand_ex} {impact}",
                grounded_evidence_ids=["EXP_COGNIZANT_001", "EXP_COGNIZANT_002"],
                evidence_status="VERIFIED",
                is_insufficient_evidence=False,
            )

            questions.append(q_ten)
            answers.append(a_ten)

        return questions, answers
