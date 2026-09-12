"""
CareerPilot AI LLM Package
Pluggable LLM provider abstraction supporting Gemini, Ollama, and Mock providers.
"""
from careerpilot.llm.base import BaseLLMProvider, LLMResponse
from careerpilot.llm.mock_provider import MockLLMProvider
from careerpilot.llm.gemini_provider import GeminiProvider
from careerpilot.llm.factory import get_llm_provider, get_llm_status

__all__ = [
    "BaseLLMProvider",
    "LLMResponse",
    "MockLLMProvider",
    "GeminiProvider",
    "get_llm_provider",
    "get_llm_status",
]


