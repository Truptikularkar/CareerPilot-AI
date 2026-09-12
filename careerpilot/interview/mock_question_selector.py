import uuid
from typing import List, Dict, Any, Optional
from careerpilot.core.constants import (
    MockInterviewMode,
    InterviewDifficulty,
    InterviewerPersona,
    QuestionCategory,
    DifficultyLevel,
    QuestionPriority,
)
from careerpilot.models.interview import InterviewQuestion
from careerpilot.models.mock_interview import MockInterviewTurn, AnswerEvaluation
from careerpilot.interview.followups import FollowUpEngine
from careerpilot.core.logging import get_logger

logger = get_logger(__name__)


class MockQuestionSelector:
    """
    Selects and adapts interview questions dynamically based on interview mode,
    candidate's previous answer evaluation, follow-up depth, and JD coverage requirements.
    """

    @classmethod
    def select_next_question(
        cls,
        available_questions: List[InterviewQuestion],
        previous_turns: List[MockInterviewTurn],
        mode: MockInterviewMode = MockInterviewMode.FULL_INTERVIEW,
        difficulty: InterviewDifficulty = InterviewDifficulty.ADAPTIVE,
        persona: InterviewerPersona = InterviewerPersona.SENIOR_ENGINEER,
        weakness_topics: Optional[List[str]] = None,
        total_questions_planned: int = 10,
    ) -> Tuple_Question_Depth:
        weakness_topics = weakness_topics or []
        asked_ids = {t.question_id for t in previous_turns}
        asked_texts = {t.question_text.lower() for t in previous_turns}

        last_turn = previous_turns[-1] if previous_turns else None
        last_eval = last_turn.evaluation if last_turn else None
        current_depth = last_turn.followup_depth if last_turn else 0

        # -------------------------------------------------------------
        # 1. Check for Follow-Up Opportunity on Previous Turn
        # -------------------------------------------------------------
        if last_turn and last_eval and not last_eval.is_i_dont_know:
            # If candidate gave a strong answer and we haven't exceeded depth 3
            if last_eval.overall_turn_score >= 70.0 and current_depth < 3:
                followup_text = last_eval.suggested_followup_question or "Can you walk through the step-by-step internal execution flow of that component?"
                if followup_text.lower() not in asked_texts:
                    q_id = f"q_followup_{uuid.uuid4().hex[:8]}"
                    followup_q = InterviewQuestion(
                        question_id=q_id,
                        category=QuestionCategory.FOLLOW_UP,
                        subcategory=last_turn.topic or "Technical Deep-Dive",
                        question=followup_text,
                        difficulty=DifficultyLevel.HARD if current_depth >= 1 else DifficultyLevel.MEDIUM,
                        priority=QuestionPriority.HIGH,
                        why_this_question=f"Deeper follow-up probe (Depth {current_depth + 1}) on {last_turn.topic}.",
                        source_requirements=[last_turn.topic],
                        candidate_evidence_ids=[],
                        expected_topics=[last_turn.topic, "Trade-offs", "Edge cases"],
                        interviewer_intent="Probe technical depth and verify candidate did not memorize surface-level buzzwords.",
                    )
                    return followup_q, current_depth + 1

            # If candidate struggled and needs conceptual clarification (Depth 1)
            elif last_eval.overall_turn_score < 55.0 and current_depth == 0 and last_eval.missing_concepts:
                clarify_text = f"Before moving forward, can you explain the fundamental purpose and mechanics of {last_eval.missing_concepts[0]}?"
                if clarify_text.lower() not in asked_texts:
                    q_id = f"q_clarify_{uuid.uuid4().hex[:8]}"
                    clarify_q = InterviewQuestion(
                        question_id=q_id,
                        category=QuestionCategory.FOLLOW_UP,
                        subcategory=last_turn.topic or "Conceptual Clarification",
                        question=clarify_text,
                        difficulty=DifficultyLevel.EASY,
                        priority=QuestionPriority.HIGH,
                        why_this_question=f"Conceptual clarification following omitted concepts in turn {len(previous_turns)}.",
                        source_requirements=[last_turn.topic],
                        candidate_evidence_ids=[],
                        expected_topics=[last_eval.missing_concepts[0]],
                        interviewer_intent="Give candidate an opportunity to demonstrate foundational understanding.",
                    )
                    return clarify_q, 1

        # -------------------------------------------------------------
        # 2. Filter Candidate Questions by Mode
        # -------------------------------------------------------------
        filtered_qs = [q for q in available_questions if q.question_id not in asked_ids and q.question.lower() not in asked_texts]

        if mode == MockInterviewMode.TECHNICAL_ONLY:
            filtered_qs = [q for q in filtered_qs if q.category in (QuestionCategory.JD_TECHNICAL, QuestionCategory.BIGQUERY, QuestionCategory.AIRFLOW, QuestionCategory.DATA_ENGINEERING, QuestionCategory.RAG, QuestionCategory.GCP, QuestionCategory.SQL, QuestionCategory.PYTHON)]
        elif mode == MockInterviewMode.RESUME_DEEP_DIVE:
            filtered_qs = [q for q in filtered_qs if q.category in (QuestionCategory.RESUME_DEEP_DIVE, QuestionCategory.RESUME_WALKTHROUGH)]
        elif mode == MockInterviewMode.PROJECT_DEEP_DIVE:
            filtered_qs = [q for q in filtered_qs if q.category == QuestionCategory.PROJECT_DEEP_DIVE]
        elif mode == MockInterviewMode.SYSTEM_DESIGN:
            filtered_qs = [q for q in filtered_qs if q.category == QuestionCategory.SYSTEM_DESIGN]
        elif mode == MockInterviewMode.BEHAVIORAL:
            filtered_qs = [q for q in filtered_qs if q.category == QuestionCategory.BEHAVIORAL]
        elif mode == MockInterviewMode.GENAI_RAG:
            filtered_qs = [q for q in filtered_qs if q.category in (QuestionCategory.RAG, QuestionCategory.GENAI) or "rag" in q.question.lower() or "gemini" in q.question.lower()]
        elif mode == MockInterviewMode.DATA_ENGINEERING:
            filtered_qs = [q for q in filtered_qs if q.category in (QuestionCategory.DATA_ENGINEERING, QuestionCategory.BIGQUERY, QuestionCategory.AIRFLOW, QuestionCategory.SQL)]
        elif mode == MockInterviewMode.GCP_CLOUD:
            filtered_qs = [q for q in filtered_qs if q.category in (QuestionCategory.GCP, QuestionCategory.BIGQUERY, QuestionCategory.EXPERIENCE_GAP)]
        elif mode == MockInterviewMode.WEAKNESS_FOCUS and weakness_topics:
            filtered_qs = [q for q in filtered_qs if any(w.lower() in q.question.lower() or w.lower() in q.subcategory.lower() for w in weakness_topics)]

        # If filtered list is empty, fallback to all unasked questions
        if not filtered_qs:
            filtered_qs = [q for q in available_questions if q.question_id not in asked_ids]
        if not filtered_qs:
            # Return final wrap-up candidate question if all exhausted
            q_id = f"q_final_{uuid.uuid4().hex[:8]}"
            return InterviewQuestion(
                question_id=q_id,
                category=QuestionCategory.CANDIDATE_QUESTIONS,
                subcategory="Wrap-up",
                question="We have covered all primary technical and architectural areas. Do you have any final questions for me about our data platform or engineering team?",
                difficulty=DifficultyLevel.EASY,
                priority=QuestionPriority.LOW,
                why_this_question="Final wrap-up turn.",
                source_requirements=["Wrap-up"],
                candidate_evidence_ids=[],
                expected_topics=["Candidate questions"],
                interviewer_intent="Evaluate candidate's curiosity and concluding questions.",
            ), 0

        # -------------------------------------------------------------
        # 3. Mode FULL_INTERVIEW Stage Progression
        # -------------------------------------------------------------
        if mode == MockInterviewMode.FULL_INTERVIEW:
            turn_idx = len(previous_turns)
            # Stage 1: HR / Walkthrough (Turns 0-1)
            if turn_idx == 0:
                target_stage_qs = [q for q in filtered_qs if q.category in (QuestionCategory.HR_SCREENING, QuestionCategory.RESUME_WALKTHROUGH)]
                if target_stage_qs:
                    return target_stage_qs[0], 0
            # Stage 2: Resume Deep Dives (Turns 1-2)
            elif turn_idx in (1, 2):
                target_stage_qs = [q for q in filtered_qs if q.category == QuestionCategory.RESUME_DEEP_DIVE]
                if target_stage_qs:
                    return target_stage_qs[0], 0
            # Stage 3: Technical Fundamentals & Data Warehousing (Turns 3-4)
            elif turn_idx in (3, 4):
                target_stage_qs = [q for q in filtered_qs if q.category in (QuestionCategory.BIGQUERY, QuestionCategory.AIRFLOW, QuestionCategory.JD_TECHNICAL)]
                if target_stage_qs:
                    return target_stage_qs[0], 0
            # Stage 4: Project Deep Dive & GenAI (Turn 5)
            elif turn_idx == 5:
                target_stage_qs = [q for q in filtered_qs if q.category in (QuestionCategory.PROJECT_DEEP_DIVE, QuestionCategory.RAG)]
                if target_stage_qs:
                    return target_stage_qs[0], 0
            # Stage 5: System Design / Cloud Gap (Turn 6)
            elif turn_idx == 6:
                target_stage_qs = [q for q in filtered_qs if q.category in (QuestionCategory.SYSTEM_DESIGN, QuestionCategory.EXPERIENCE_GAP)]
                if target_stage_qs:
                    return target_stage_qs[0], 0
            # Stage 6: Behavioral STAR (Turn 7)
            elif turn_idx == 7:
                target_stage_qs = [q for q in filtered_qs if q.category == QuestionCategory.BEHAVIORAL]
                if target_stage_qs:
                    return target_stage_qs[0], 0

        # Sort remaining by priority (CRITICAL -> HIGH -> MEDIUM)
        prio_order = {QuestionPriority.CRITICAL: 0, QuestionPriority.HIGH: 1, QuestionPriority.MEDIUM: 2, QuestionPriority.LOW: 3}
        sorted_qs = sorted(filtered_qs, key=lambda q: prio_order.get(q.priority, 2))

        selected = sorted_qs[0]
        return selected, 0


# Return type annotation helper
Tuple_Question_Depth = tuple[InterviewQuestion, int]
