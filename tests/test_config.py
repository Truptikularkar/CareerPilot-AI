from pathlib import Path
from careerpilot.core.config import settings, Settings
from careerpilot.core.constants import LLMProviderType


def test_settings_initialization():
    assert settings.APP_NAME == "CareerPilot AI"
    assert isinstance(settings.BASE_DIR, Path)
    assert settings.DATA_DIR.exists()
    assert settings.SAMPLE_DATA_DIR.exists()
    assert settings.OUTPUT_RESUMES_DIR.exists()


def test_llm_provider_enum():
    assert settings.LLM_PROVIDER in [LLMProviderType.GEMINI, LLMProviderType.OLLAMA, LLMProviderType.MOCK]
