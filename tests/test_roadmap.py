import pytest
from pathlib import Path
from careerpilot.graphs.job_analysis_graph import analyze_job
from careerpilot.graphs.resume_graph import generate_tailored_resume
from careerpilot.ats.evaluator import ATSEvaluator
from careerpilot.interview.roadmap import RoadmapGenerator
from careerpilot.interview.question_planner import QuestionPlanner
from careerpilot.interview.question_engine import QuestionEngine


def test_roadmap_generator_1_3_7_days():
    eval_file = Path("data/jobs/evaluation/01_ai_data_engineer.txt")
    analysis = analyze_job(eval_file)
    resume = generate_tailored_resume(analysis)
    ats_rep = ATSEvaluator.evaluate_resume(resume, analysis)
    seed = ats_rep.interview_seed
    quotas = QuestionPlanner.plan_question_distribution(analysis, seed, resume)
    questions = QuestionEngine.generate_interview_questions(analysis, resume, seed, quotas)

    # 1-day crash roadmap
    rm1 = RoadmapGenerator.generate_roadmap(analysis, resume, seed, questions, days_total=1)
    assert rm1.days_total == 1
    assert len(rm1.daily_schedule) == 1

    # 3-day fast-track roadmap
    rm3 = RoadmapGenerator.generate_roadmap(analysis, resume, seed, questions, days_total=3)
    assert rm3.days_total == 3
    assert len(rm3.daily_schedule) == 3

    # 7-day comprehensive roadmap
    rm7 = RoadmapGenerator.generate_roadmap(analysis, resume, seed, questions, days_total=7)
    assert rm7.days_total == 7
    assert len(rm7.daily_schedule) == 7
    for day in rm7.daily_schedule:
        assert day.title != ""
        assert len(day.focus_areas) > 0
        assert len(day.practice_drills) > 0
