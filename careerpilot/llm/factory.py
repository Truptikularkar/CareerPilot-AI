from typing import Optional, Dict, Any
from careerpilot.core.config import settings
from careerpilot.core.constants import LLMProviderType, AppEnvironmentMode
from careerpilot.llm.base import BaseLLMProvider
from careerpilot.llm.mock_provider import MockLLMProvider
from careerpilot.llm.gemini_provider import GeminiProvider
from careerpilot.core.logging import get_logger

logger = get_logger("careerpilot.llm.factory")

_cached_provider: Optional[BaseLLMProvider] = None


def get_llm_provider(provider_type: Optional[LLMProviderType] = None, force_refresh: bool = False) -> BaseLLMProvider:
    """
    Factory function returning the configured or requested LLM provider.
    In DEMO mode, returns MockLLMProvider for offline deterministic behavior.
    In LOCAL_PRIVATE mode with GEMINI, returns GeminiProvider.
    Never silently falls back to MockLLMProvider in LOCAL_PRIVATE mode if Gemini fails.
    """
    global _cached_provider
    target = provider_type or settings.LLM_PROVIDER

    if target == LLMProviderType.MOCK:
        return MockLLMProvider()

    if target == LLMProviderType.GEMINI or settings.GEMINI_API_KEY:
        if not settings.GEMINI_API_KEY:
            if settings.CAREERPILOT_MODE == AppEnvironmentMode.LOCAL_PRIVATE:
                raise RuntimeError(
                    "GEMINI UNAVAILABLE: GEMINI_API_KEY is not configured in .env or settings for LOCAL_PRIVATE mode."
                )
            logger.warning("GEMINI_API_KEY not configured. Falling back to MockLLMProvider.")
            return MockLLMProvider()

        if _cached_provider is None or not isinstance(_cached_provider, GeminiProvider) or force_refresh:
            _cached_provider = GeminiProvider()
        return _cached_provider

    if settings.is_demo_mode:
        return MockLLMProvider()

    if target == LLMProviderType.OLLAMA:
        logger.warning("Ollama provider requested but not yet fully configured. Using mock.")
        return MockLLMProvider()

    return MockLLMProvider()


def get_llm_status() -> Dict[str, Any]:
    """
    Returns live LLM connection diagnostics for UI and health checking.
    """
    if settings.GEMINI_API_KEY:
        try:
            provider = get_llm_provider()
            if hasattr(provider, "get_status"):
                status_info = provider.get_status()
                status_info["mode"] = settings.CAREERPILOT_MODE.value
                return status_info
        except Exception as e:
            return {
                "provider": "gemini" if settings.LLM_PROVIDER == LLMProviderType.GEMINI else "mock",
                "model": settings.GEMINI_MODEL,
                "status": f"ERROR: {e}",
                "mode": settings.CAREERPILOT_MODE.value,
                "last_call_at": None,
                "last_error": str(e),
                "api_key_configured": bool(settings.GEMINI_API_KEY),
                "api_key_masked": settings.masked_gemini_key,
            }

    if settings.is_demo_mode:
        return {
            "provider": "mock",
            "model": "mock-model-v1",
            "status": "MOCK_ACTIVE",
            "mode": "DEMO",
            "last_call_at": None,
            "last_error": None,
            "api_key_configured": False,
            "api_key_masked": None,
        }

    try:
        provider = get_llm_provider()
        if hasattr(provider, "get_status"):
            status_info = provider.get_status()
            status_info["mode"] = settings.CAREERPILOT_MODE.value
            return status_info
    except Exception as e:
        return {
            "provider": "gemini" if settings.LLM_PROVIDER == LLMProviderType.GEMINI else "mock",
            "model": settings.GEMINI_MODEL,
            "status": f"ERROR: {e}",
            "mode": settings.CAREERPILOT_MODE.value,
            "last_call_at": None,
            "last_error": str(e),
            "api_key_configured": bool(settings.GEMINI_API_KEY),
            "api_key_masked": settings.masked_gemini_key,
        }

    return {
        "provider": "mock",
        "model": "mock-model-v1",
        "status": "MOCK_ACTIVE",
        "mode": settings.CAREERPILOT_MODE.value,
        "last_call_at": None,
        "last_error": None,
        "api_key_configured": bool(settings.GEMINI_API_KEY),
        "api_key_masked": settings.masked_gemini_key,
    }
