import pytest
from pathlib import Path
from careerpilot.graphs.job_analysis_graph import analyze_job
from careerpilot.graphs.resume_graph import generate_tailored_resume
from careerpilot.interview.system_design import SystemDesignEngine


def test_system_design_generation_ai_data_engineer():
    eval_file = Path("data/jobs/evaluation/01_ai_data_engineer.txt")
    analysis = analyze_job(eval_file)
    resume = generate_tailored_resume(analysis)

    scenarios = SystemDesignEngine.generate_system_design_scenarios(analysis, resume)

    assert len(scenarios) >= 2

    for sc in scenarios:
        assert sc.title != ""
        assert len(sc.functional_requirements) > 0
        assert len(sc.non_functional_requirements) > 0
        assert len(sc.scale_assumptions) > 0
        assert len(sc.architecture_components) > 0
        assert len(sc.data_flow) > 0
        assert sc.storage != ""
        assert sc.processing != ""
        assert sc.orchestration != ""
        assert sc.failure_handling != ""
        assert len(sc.trade_offs) > 0
        assert len(sc.follow_up_questions) > 0
