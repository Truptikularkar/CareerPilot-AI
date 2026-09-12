import pytest
from pathlib import Path
from careerpilot.models.interview import InterviewPlan
from careerpilot.graphs.interview_prep_graph import prepare_interview


def test_interview_prep_graph_end_to_end():
    eval_file = Path("data/jobs/evaluation/01_ai_data_engineer.txt")

    plan = prepare_interview(job_input=eval_file, strategy="auto", days=7)

    assert plan is not None
    assert isinstance(plan, InterviewPlan)
    assert plan.prep_id.startswith("prep_")
    assert plan.job_id != ""
    assert plan.target_role != ""

    # Verify questions
    assert len(plan.questions) >= 20
    # Verify answers
    assert len(plan.answers) >= 15
    # Verify STAR answers
    assert len(plan.star_answers) >= 3
    # Verify System Designs
    assert len(plan.system_designs) >= 1
    # Verify Roadmap
    assert plan.roadmap.days_total == 7
    assert len(plan.roadmap.daily_schedule) == 7
    # Verify Readiness Score
    assert plan.readiness_score.overall_readiness >= 75.0
    # Verify Truth Report
    assert plan.truth_report is not None
    assert str(plan.truth_report.get("status")) in ("PASS", "TruthValidationStatus.PASS")

