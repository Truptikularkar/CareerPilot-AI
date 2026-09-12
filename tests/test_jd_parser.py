import pytest
from pathlib import Path
from careerpilot.parsers.jd_parser import JobDescriptionParser
from careerpilot.core.constants import RequirementImportance, TaxonomyCategory


def test_jd_parser_raw_text():
    sample_text = """
    Job Title: Senior Data Engineer
    Company: Acme Tech
    
    Responsibilities:
    - Build automated ETL pipelines using Python and BigQuery.
    - Author Airflow DAGs for batch validation.
    
    Requirements (Must Have):
    - 3+ years of Python and SQL.
    - Production experience with Google Cloud BigQuery.
    - Apache Airflow DAG management.
    
    Nice to Have:
    - Experience with RAG and LLM agents.
    """
    jd = JobDescriptionParser.parse_raw_text(sample_text)
    assert jd.company_name == "Acme Tech"
    assert "Data Engineer" in jd.job_title
    assert len(jd.responsibilities) >= 2
    assert len(jd.requirements) >= 3

    # Check must-have vs nice-to-have segmentation
    must_haves = [r for r in jd.requirements if r.importance == RequirementImportance.MUST_HAVE]
    nice_to_haves = [r for r in jd.requirements if r.importance == RequirementImportance.NICE_TO_HAVE]
    assert len(must_haves) >= 2
    assert len(nice_to_haves) >= 1

    # Check taxonomy categories
    python_req = next((r for r in jd.requirements if r.normalized_skill == "Python"), None)
    assert python_req is not None
    assert python_req.category == TaxonomyCategory.PROGRAMMING
    assert python_req.years_required == 3.0


def test_jd_parser_file_parsing():
    eval_dir = Path("data/jobs/evaluation")
    jd_path = eval_dir / "01_ai_data_engineer.txt"
    assert jd_path.exists()

    jd = JobDescriptionParser.parse_file(jd_path)
    assert jd.company_name == "CognitiveScale Labs"
    assert "AI Data Engineer" in jd.job_title
    assert "BigQuery" in jd.tech_stack
    assert "Apache Airflow" in jd.tech_stack
