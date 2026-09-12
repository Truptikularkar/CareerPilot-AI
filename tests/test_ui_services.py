import pytest
from pathlib import Path
from careerpilot.services.careerpilot_service import CareerPilotService
from careerpilot.models.application import ApplicationFilter
from careerpilot.core.constants import ApplicationStatus, DecisionRecommendation


def test_ui_services_filters_and_aggregations():
    eval_file = Path("data/jobs/evaluation/01_ai_data_engineer.txt")
    _, app = CareerPilotService.analyze_job(eval_file, company_name="Meta Platforms", job_title="AI Data Platform Engineer")

    # 1. Test Filter Criteria
    apps_filtered = CareerPilotService.list_applications(
        ApplicationFilter(search_query="Meta")
    )
    assert len(apps_filtered) >= 1
    assert any(a.company == "Meta Platforms" for a in apps_filtered)

    # 2. Test Skill Gaps Summary
    skill_summary = CareerPilotService.get_skill_gaps_summary()
    assert len(skill_summary.priority_learning_topics) >= 1
    assert len(skill_summary.top_missing_skills) >= 1
    assert len(skill_summary.top_demanded_skills) >= 1

    # 3. Next Action Guidance Logic
    next_act = app.next_action
    assert next_act != ""
    assert isinstance(next_act, str)
