import pytest
from careerpilot.core.constants import MatchLevel, KeywordDensityRisk
from careerpilot.ats.keyword_matcher import KeywordTaxonomyMatcher


def test_keyword_matcher_exact_match():
    text = "Engineered automated data pipelines in Python and SQL using Google BigQuery."
    match_level, explanation = KeywordTaxonomyMatcher.match_term_in_text("Python", text)
    assert match_level == MatchLevel.EXACT_MATCH
    assert "Exact match" in explanation


def test_keyword_matcher_synonym_match():
    text = "Developed enterprise GenAI workflows with LLM integration on GCP and Airflow."
    # 1. Generative AI -> GenAI
    m1, e1 = KeywordTaxonomyMatcher.match_term_in_text("Generative AI", text)
    assert m1 == MatchLevel.SYNONYM_MATCH

    # 2. Large Language Models -> LLM
    m2, e2 = KeywordTaxonomyMatcher.match_term_in_text("Large Language Models", text)
    assert m2 == MatchLevel.SYNONYM_MATCH

    # 3. Google Cloud Platform -> GCP
    m3, e3 = KeywordTaxonomyMatcher.match_term_in_text("Google Cloud Platform", text)
    assert m3 == MatchLevel.SYNONYM_MATCH

    # 4. Apache Airflow -> Airflow
    m4, e4 = KeywordTaxonomyMatcher.match_term_in_text("Apache Airflow", text)
    assert m4 == MatchLevel.SYNONYM_MATCH


def test_keyword_matcher_semantic_match():
    text = "Designed and tuned analytical storage using Google BigQuery."
    match_level, explanation = KeywordTaxonomyMatcher.match_term_in_text("Cloud Data Warehouse", text)
    assert match_level == MatchLevel.SEMANTIC_MATCH
    assert "BigQuery" in explanation or "conceptually" in explanation


def test_keyword_matcher_gap():
    text = "Built serverless ETL pipelines using GCP Cloud Functions and BigQuery."
    match_level, explanation = KeywordTaxonomyMatcher.match_term_in_text("AWS Redshift", text)
    assert match_level == MatchLevel.GAP
    assert explanation is None


def test_keyword_density_and_stuffing():
    healthy_text = "Python is used for ETL pipelines, data validation, and Airflow orchestration with Python scripts."
    count, risk = KeywordTaxonomyMatcher.evaluate_keyword_density("python", healthy_text)
    assert count == 2
    assert risk == KeywordDensityRisk.HEALTHY

    stuffed_text = "Python Python Python Python Python Python Python and Python in data."
    count_s, risk_s = KeywordTaxonomyMatcher.evaluate_keyword_density("python", stuffed_text)
    assert count_s >= 7
    assert risk_s == KeywordDensityRisk.POTENTIAL_STUFFING
