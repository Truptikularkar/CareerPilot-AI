import json
import yaml
from pathlib import Path
import pytest


CANDIDATE_DIR = Path(__file__).resolve().parent.parent / "data" / "candidate"


def test_candidate_files_exist():
    expected_files = [
        "master_resume.pdf",
        "profile.yaml",
        "experience.md",
        "projects.md",
        "skills.md",
        "achievements.md",
        "preferences.yaml",
        "evidence.json",
        "VALIDATION_REPORT.md",
    ]
    for filename in expected_files:
        filepath = CANDIDATE_DIR / filename
        assert filepath.exists(), f"Expected candidate file missing: {filename}"
        assert filepath.stat().st_size > 0, f"Candidate file is empty: {filename}"


def test_candidate_profile_yaml_integrity():
    profile_path = CANDIDATE_DIR / "profile.yaml"
    with open(profile_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    cand = data.get("candidate", {})
    assert cand.get("name") == "Trupti Kularkar"
    assert cand.get("current_experience_years") == "1.9+"
    assert cand.get("current_role") == "Programmer Analyst"
    assert cand.get("current_company") == "Cognizant Technology Solutions"
    assert "AI Data Engineer" in cand.get("target_roles", [])


def test_candidate_preferences_integrity():
    pref_path = CANDIDATE_DIR / "preferences.yaml"
    with open(pref_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    prefs = data.get("career_preferences", {})
    assert "Pune" in prefs.get("location", {}).get("primary", [])
    assert "Nagpur" in prefs.get("location", {}).get("primary", [])
    assert prefs.get("compensation", {}).get("current_ctc_lpa") == 4.5
    assert prefs.get("compensation", {}).get("target_ctc_lpa", {}).get("minimum") == 9
    assert prefs.get("compensation", {}).get("target_ctc_lpa", {}).get("maximum") == 10


def test_candidate_evidence_truth_classification():
    evidence_path = CANDIDATE_DIR / "evidence.json"
    with open(evidence_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    evidences = data.get("evidence", [])
    assert len(evidences) >= 10

    # Ensure unsupported claims are strictly marked NOT_SUPPORTED
    for ev in evidences:
        if "AWS production" in ev.get("claim", ""):
            assert ev.get("status") == "NOT_SUPPORTED"
            assert ev.get("allowed_for_resume") is False
        if "Spark production" in ev.get("claim", ""):
            assert ev.get("status") == "NOT_SUPPORTED"
            assert ev.get("allowed_for_resume") is False
        if "Kubernetes production" in ev.get("claim", ""):
            assert ev.get("status") == "NOT_SUPPORTED"
            assert ev.get("allowed_for_resume") is False
        if "Python professional" in ev.get("claim", ""):
            assert ev.get("status") == "SUPPORTED"
            assert ev.get("allowed_for_resume") is True
        if "GCP professional" in ev.get("claim", ""):
            assert ev.get("status") == "SUPPORTED"
            assert ev.get("allowed_for_resume") is True
