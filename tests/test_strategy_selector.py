import pytest
from pathlib import Path
from careerpilot.core.constants import ResumeStrategyType, RoleCategory
from careerpilot.models.job import JobAnalysisResult, RoleClassification, RoleReality
from careerpilot.generators.strategy_selector import StrategySelector
from careerpilot.generators.strategy_engine import StrategyEngine
from careerpilot.parsers.jd_parser import JobDescriptionParser
from careerpilot.graphs.job_analysis_graph import analyze_job


def test_strategy_selector_ai_data_engineer():
    eval_file = Path("data/jobs/evaluation/01_ai_data_engineer.txt")
    analysis = analyze_job(eval_file)
    strategy = StrategySelector.select_strategy(analysis)

    assert strategy.strategy_type == ResumeStrategyType.AI_DATA_ENGINEER
    assert "Vertex AI" in strategy.emphasis_keywords or "RAG" in strategy.emphasis_keywords
    assert "AI-Driven Data Quality Monitoring" in strategy.project_priorities


def test_strategy_selector_data_engineer():
    eval_file = Path("data/jobs/evaluation/02_data_engineer_gcp.txt")
    analysis = analyze_job(eval_file)
    strategy = StrategySelector.select_strategy(analysis)

    assert strategy.strategy_type in (ResumeStrategyType.DATA_ENGINEER, ResumeStrategyType.GCP_DATA_ENGINEER)


def test_strategy_selector_genai_engineer():
    eval_file = Path("data/jobs/evaluation/03_genai_rag_engineer.txt")
    analysis = analyze_job(eval_file)
    strategy = StrategySelector.select_strategy(analysis)

    assert strategy.strategy_type == ResumeStrategyType.GENAI_ENGINEER
    assert "Local RAG & Hybrid Retrieval" in strategy.project_priorities


def test_strategy_selector_manual_override():
    eval_file = Path("data/jobs/evaluation/01_ai_data_engineer.txt")
    analysis = analyze_job(eval_file)

    # Force manual override to GCP_DATA_ENGINEER
    strategy = StrategySelector.select_strategy(analysis, override_strategy="gcp_data_engineer")
    assert strategy.strategy_type == ResumeStrategyType.GCP_DATA_ENGINEER
    assert "GCP" in strategy.target_role or "Google Cloud" in strategy.summary_tone
