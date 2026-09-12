import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path

from careerpilot.ui.utils.formatters import format_datetime, format_date
from careerpilot.models.application import ResumeVersionRecord
from careerpilot.db.schema import ResumeVersionDB
from careerpilot.db.repository import ResumeRepository, JobRepository, ApplicationRepository
from careerpilot.services.careerpilot_service import CareerPilotService
from careerpilot.core.constants import ResumeStrategyType
from careerpilot.core.config import settings


def test_format_datetime_with_datetime_object():
    """Verify format_datetime correctly formats timezone-aware and naive datetime objects."""
    dt = datetime(2026, 8, 31, 21, 15, 30, tzinfo=timezone.utc)
    res = format_datetime(dt)
    assert res == "2026-08-31 21:15"

    naive_dt = datetime(2026, 8, 31, 14, 45)
    assert format_datetime(naive_dt) == "2026-08-31 14:45"


def test_format_datetime_with_iso_string():
    """Verify format_datetime correctly parses and formats ISO strings."""
    iso_str = "2026-08-31T21:15:30.123456+00:00"
    res = format_datetime(iso_str)
    assert res == "2026-08-31 21:15"

    z_iso_str = "2026-08-31T21:15:30Z"
    assert format_datetime(z_iso_str) == "2026-08-31 21:15"


def test_format_datetime_with_none_and_empty():
    """Verify format_datetime handles None and empty strings gracefully without crashing."""
    assert format_datetime(None) == "Unknown date"
    assert format_datetime(None, fallback="N/A") == "N/A"
    assert format_datetime("") == "Unknown date"
    assert format_datetime("   ") == "Unknown date"


def test_format_datetime_unparseable_string():
    """Verify format_datetime handles arbitrary string inputs gracefully."""
    assert format_datetime("invalid-date-string") == "invalid-date-str"



def test_format_date():
    """Verify format_date outputs YYYY-MM-DD format."""
    dt = datetime(2026, 8, 31, 21, 15, 30)
    assert format_date(dt) == "2026-08-31"
    assert format_date(None) == "N/A"


def test_resume_version_created_at_datetime():
    """
    Regression Test for Resume Builder TypeError:
    Verifies that ResumeVersionDB.created_at is a datetime and is safely formatted by the UI logic.
    """
    dt = datetime(2026, 8, 31, 22, 10, 0, tzinfo=timezone.utc)
    v_db = ResumeVersionDB(
        id="resume_test_dt",
        job_id="job_test_dt",
        candidate_id="trupti_kularkar",
        strategy_type="AI_DATA_ENGINEER",
        version_tag="v1.0",
        tailored_resume_json={},
        ats_score=96.7,
        created_at=dt,
    )

    # Replicate Resume Builder UI formatting logic
    ats_str = f"{v_db.ats_score:.1f}%" if getattr(v_db, "ats_score", None) is not None else "N/A"
    date_str = format_datetime(getattr(v_db, "created_at", None))
    choice_label = f"{v_db.version_tag} ({v_db.strategy_type}) — ATS: {ats_str} [{date_str}]"

    assert "v1.0 (AI_DATA_ENGINEER) — ATS: 96.7% [2026-08-31 22:10]" == choice_label


def test_resume_version_created_at_none_and_optional_ats():
    """
    Regression test for missing/None created_at or ats_score on resume versions.
    """
    v_db = ResumeVersionDB(
        id="resume_test_none",
        job_id="job_test_none",
        candidate_id="trupti_kularkar",
        strategy_type="DATA_ENGINEER",
        version_tag="v2.0",
        tailored_resume_json={},
        ats_score=None,
        created_at=None,
    )

    ats_str = f"{v_db.ats_score:.1f}%" if getattr(v_db, "ats_score", None) is not None else "N/A"
    date_str = format_datetime(getattr(v_db, "created_at", None))
    choice_label = f"{v_db.version_tag} ({v_db.strategy_type}) — ATS: {ats_str} [{date_str}]"

    assert "v2.0 (DATA_ENGINEER) — ATS: N/A [Unknown date]" == choice_label


def test_database_round_trip_created_at_type():
    """
    Database Round-Trip Test:
    Verifies that created_at is stored in SQLite and retrieved as a datetime.datetime object.
    """
    job_file = settings.EVALUATION_JOBS_DIR / "01_ai_data_engineer.txt"
    analysis, app = CareerPilotService.analyze_job(
        input_source=job_file,
        company_name="RoundTrip Corp",
        job_title="AI Data Engineer",
    )

    resume, ats_report, updated_app = CareerPilotService.generate_resume_for_application(
        app_id=app.application_id,
        strategy=ResumeStrategyType.AI_DATA_ENGINEER,
    )

    versions = ResumeRepository.list_versions_for_job(app.job_id)
    assert len(versions) >= 1

    latest = versions[0]
    assert isinstance(latest.created_at, datetime)
    assert latest.created_at.year >= 2026
    # Formatting works without TypeError
    display_str = format_datetime(latest.created_at)
    assert len(display_str) == 16


def test_multiple_resume_versions_display():
    """
    Verify multiple resume versions (v1.0, v2.0, v3.0) with different strategies
    are stored, retrieved, and formatted distinctively.
    """
    job_file = settings.EVALUATION_JOBS_DIR / "01_ai_data_engineer.txt"
    analysis, app = CareerPilotService.analyze_job(
        input_source=job_file,
        company_name="MultiVersion Corp",
        job_title="AI Data Engineer",
    )

    r1, ats1, _ = CareerPilotService.generate_resume_for_application(app.application_id, strategy=ResumeStrategyType.AI_DATA_ENGINEER)
    r2, ats2, _ = CareerPilotService.generate_resume_for_application(app.application_id, strategy=ResumeStrategyType.DATA_ENGINEER)
    r3, ats3, _ = CareerPilotService.generate_resume_for_application(app.application_id, strategy=ResumeStrategyType.GENAI_ENGINEER)

    versions = ResumeRepository.list_versions_for_job(app.job_id)
    assert len(versions) >= 3

    v_choices = {}
    for v in versions:
        ats_str = f"{v.ats_score:.1f}%" if getattr(v, "ats_score", None) is not None else "N/A"
        date_str = format_datetime(getattr(v, "created_at", None))
        label = f"{v.version_tag} ({v.strategy_type}) — ATS: {ats_str} [{date_str}]"
        v_choices[label] = v

    assert len(v_choices) >= 3
    tags = [v.version_tag for v in v_choices.values()]
    assert "v1.0" in tags
    assert "v2.0" in tags
    assert "v3.0" in tags
