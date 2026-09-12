import pytest
from pathlib import Path
from careerpilot.core.constants import HealthStatus, AppEnvironmentMode
from careerpilot.core.config import Settings, settings
from careerpilot.health import (
    check_configuration,
    check_candidate_data,
    check_knowledge_data,
    check_database,
    check_embedding_model,
    check_vector_store,
    check_llm_provider,
    get_system_health,
)


def test_system_health_checks():
    """Verify diagnostic health checks across all system components."""
    cfg_health = check_configuration()
    assert cfg_health.status in (HealthStatus.HEALTHY, HealthStatus.DEGRADED)
    assert "mode" in cfg_health.details

    cand_health = check_candidate_data()
    assert cand_health.status in (HealthStatus.HEALTHY, HealthStatus.DEGRADED)

    know_health = check_knowledge_data()
    assert know_health.status in (HealthStatus.HEALTHY, HealthStatus.DEGRADED)

    db_health = check_database()
    assert db_health.status == HealthStatus.HEALTHY
    assert db_health.details.get("tables_count", 0) > 0

    emb_health = check_embedding_model()
    assert emb_health.status == HealthStatus.HEALTHY
    assert emb_health.details.get("dimension") is not None

    vec_health = check_vector_store()
    assert vec_health.status == HealthStatus.HEALTHY
    assert "candidate_chunks" in vec_health.details

    llm_health = check_llm_provider()
    assert llm_health.status in (HealthStatus.HEALTHY, HealthStatus.DEGRADED)

    overall_health = get_system_health()
    assert overall_health.overall_status in (HealthStatus.HEALTHY, HealthStatus.DEGRADED)
    assert len(overall_health.components) == 7


def test_environment_mode_paths_and_masking():
    """Verify dynamic path resolution and secret masking in demo vs local private mode."""
    # Test Demo Mode
    demo_settings = Settings(CAREERPILOT_MODE=AppEnvironmentMode.DEMO)
    assert demo_settings.is_demo_mode is True
    assert demo_settings.active_candidate_id == "alex_rivera_demo"
    assert "demo" in str(demo_settings.active_candidate_dir).lower()

    # Test Masking
    masked = demo_settings.masked_gemini_key
    if demo_settings.GEMINI_API_KEY:
        assert "****" in masked or "..." in masked


def test_upload_security_rules():
    """Verify file upload extension restrictions and size constraints."""
    allowed_exts = settings.ALLOWED_UPLOAD_EXTENSIONS
    assert ".pdf" in allowed_exts
    assert ".txt" in allowed_exts
    assert ".exe" not in allowed_exts
    assert ".py" not in allowed_exts

    assert settings.MAX_UPLOAD_SIZE_BYTES == 5 * 1024 * 1024  # 5 MB
