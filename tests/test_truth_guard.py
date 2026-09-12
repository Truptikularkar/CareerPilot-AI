import pytest
from careerpilot.core.constants import TruthValidationStatus, ClaimType
from careerpilot.truth_guard.auditor import TruthAuditor
from careerpilot.truth_guard.classifier import ClaimClassifier


def test_truth_guard_pass_verified_metrics():
    text = (
        "Optimized BigQuery query processing costs by ~25% and reduced data quality incidents by ~35%. "
        "Engineered self-healing pipelines resolving ~75% of transient failures and reduced incident response time by ~60%."
    )
    report = TruthAuditor.audit_sections({"experience": text})
    assert report.status == TruthValidationStatus.PASS
    assert len(report.blocked_claims) == 0
    assert report.verified_claims_count >= 4


def test_truth_guard_negative_inflated_metric():
    # Attempting to inflate 25% -> 40%
    text = "Optimized BigQuery query costs by 40% using advanced database tuning."
    report = TruthAuditor.audit_sections({"experience": text})
    assert report.status == TruthValidationStatus.BLOCK
    assert any("40%" in c.claim_text for c in report.blocked_claims)


def test_truth_guard_negative_aws_production():
    # Attempting to claim AWS production experience
    text = "Served as Lead AWS Data Engineer in production managing AWS Glue pipelines and Redshift clusters."
    report = TruthAuditor.audit_sections({"experience": text})
    assert report.status == TruthValidationStatus.BLOCK
    assert any("AWS production" in c.violation_reason for c in report.blocked_claims)


def test_truth_guard_negative_kubernetes_production():
    # Attempting to claim Kubernetes cluster management
    text = "Managed high-availability Kubernetes production cluster deploying real-time streaming pods."
    report = TruthAuditor.audit_sections({"experience": text})
    assert report.status == TruthValidationStatus.BLOCK
    assert any("Kubernetes" in c.violation_reason for c in report.blocked_claims)


def test_truth_guard_negative_experience_years_fabrication():
    # Attempting to claim 4+ years of experience
    text = "Senior Data Engineer with 4+ years of professional experience in Python and cloud pipelines."
    report = TruthAuditor.audit_sections({"summary": text})
    assert report.status == TruthValidationStatus.BLOCK
    assert any("1.9+ years" in c.violation_reason for c in report.blocked_claims)


def test_truth_guard_negative_personal_project_in_experience():
    # Attempting to place personal RAG sandbox into professional experience section
    sections = {
        "experience": "Engineered Local RAG Sandbox using FAISS and BM25 for enterprise client production.",
        "projects": "AI AutoHeal Agent",
    }
    report = TruthAuditor.audit_sections(sections)
    assert report.status == TruthValidationStatus.BLOCK
    assert any("Personal projects" in c.violation_reason for c in report.blocked_claims)


def test_truth_guard_positive_personal_project_in_projects():
    # Legitimate personal project placed under projects section
    sections = {
        "experience": "Engineered automated ETL pipelines in Python and BigQuery at Cognizant.",
        "projects": "Built Local RAG & Hybrid Retrieval Sandbox implementing dense semantic embeddings (FAISS) and BM25.",
    }
    report = TruthAuditor.audit_sections(sections)
    assert report.status == TruthValidationStatus.PASS
    assert len(report.blocked_claims) == 0


def test_truth_guard_positive_vertex_ai_ticket_agent():
    # Verified innovation achievement at Cognizant
    text = "Built LLM-powered ticket resolution agent on Google Vertex AI and Gemini API resolving ~75% of transient errors."
    report = TruthAuditor.audit_sections({"experience": text})
    assert report.status == TruthValidationStatus.PASS
    assert len(report.blocked_claims) == 0
