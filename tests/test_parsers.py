from pathlib import Path
from careerpilot.parsers.candidate_parser import CandidateParser
from careerpilot.parsers.jd_parser import JobDescriptionParser
from careerpilot.parsers.evidence_extractor import EvidenceExtractor
from careerpilot.core.constants import EvidenceStatus, RoleCategory, SeniorityLevel


def test_candidate_parser_and_evidence_extraction(sample_candidate_path: Path):
    candidate = CandidateParser.from_json_file(sample_candidate_path)
    assert candidate.full_name == "Alex Rivera"
    assert len(candidate.skills) >= 5
    assert len(candidate.experiences) == 2
    assert len(candidate.projects) == 2

    # Verify atomic evidence generation
    assert len(candidate.atomic_evidence) > 0
    
    # Check that every evidence item has status SUPPORTED
    for ev in candidate.atomic_evidence:
        assert ev.status == EvidenceStatus.SUPPORTED
        assert ev.candidate_id == candidate.id
        assert len(ev.content) > 0

    # Verify metrics extracted in evidence
    evidence_with_metrics = [ev for ev in candidate.atomic_evidence if ev.metrics]
    assert len(evidence_with_metrics) > 0


def test_jd_parser_ai_engineer(sample_ai_jd_path: Path):
    jd = JobDescriptionParser.parse_file(sample_ai_jd_path)
    assert jd.company_name == "TechFlow AI"
    assert "Senior AI" in jd.job_title
    assert jd.extracted_role in [RoleCategory.AI_ENGINEER, RoleCategory.GENAI_ENGINEER]
    assert jd.estimated_seniority == SeniorityLevel.SENIOR
    assert "Python" in jd.tech_stack
    assert "LangChain" in jd.tech_stack or "LangGraph" in jd.tech_stack
    assert len(jd.responsibilities) > 0
    assert len(jd.requirements) > 0


def test_jd_parser_data_engineer(sample_data_eng_jd_path: Path):
    jd = JobDescriptionParser.parse_file(sample_data_eng_jd_path)
    assert jd.company_name == "DataWave Global"
    assert jd.extracted_role == RoleCategory.DATA_ENGINEER
    assert "BigQuery" in jd.tech_stack
    assert "Apache Spark" in jd.tech_stack or "Spark" in jd.tech_stack
