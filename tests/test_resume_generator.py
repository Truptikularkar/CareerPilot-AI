import pytest
from pathlib import Path
from careerpilot.core.constants import ResumeStrategyType
from careerpilot.generators.strategy_engine import StrategyEngine
from careerpilot.generators.bullet_selector import BulletSelector
from careerpilot.ats.evaluator import ATSEvaluator
from careerpilot.graphs.job_analysis_graph import analyze_job


def test_bullet_selector_experience_assembly():
    eval_file = Path("data/jobs/evaluation/01_ai_data_engineer.txt")
    analysis = analyze_job(eval_file)
    strategy = StrategyEngine.get_strategy(ResumeStrategyType.AI_DATA_ENGINEER)

    experiences = BulletSelector.assemble_experience(strategy, analysis)
    assert len(experiences) >= 1
    exp = experiences[0]
    assert "Cognizant" in exp.company
    assert exp.title == "Programmer Analyst"
    assert len(exp.bullets) >= 4
    # Ensure metrics are preserved
    assert any("25%" in b for b in exp.bullets)



def test_bullet_selector_project_isolation():
    eval_file = Path("data/jobs/evaluation/03_genai_rag_engineer.txt")
    analysis = analyze_job(eval_file)
    strategy = StrategyEngine.get_strategy(ResumeStrategyType.GENAI_ENGINEER)

    projects = BulletSelector.assemble_projects(strategy, analysis)
    assert len(projects) >= 2
    # Ensure Local RAG sandbox is classified as personal project
    rag_proj = next((p for p in projects if "Local RAG" in p.name), None)
    assert rag_proj is not None
    assert rag_proj.is_personal_project is True


def test_bullet_selector_skills_prioritization():
    eval_file = Path("data/jobs/evaluation/01_ai_data_engineer.txt")
    analysis = analyze_job(eval_file)
    strategy = StrategyEngine.get_strategy(ResumeStrategyType.GENAI_ENGINEER)

    skills = BulletSelector.assemble_skills(strategy, analysis)
    assert len(skills) >= 4
    # Generative AI should be first for GENAI_ENGINEER strategy
    assert "Generative AI" in skills[0].category_name
