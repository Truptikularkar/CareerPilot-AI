"""
CareerPilot AI — Gemini LLM Provider
Wraps official google.genai Client with support for text generation,
schema-enforced structured generation, health tracking, and zero silent mock fallback in LOCAL_PRIVATE mode.
"""
from datetime import datetime
from typing import Optional, Type, TypeVar, Dict, Any
from pydantic import BaseModel

from careerpilot.core.config import settings
from careerpilot.core.constants import AppEnvironmentMode
from careerpilot.core.logging import get_logger
from careerpilot.llm.base import BaseLLMProvider, LLMResponse

logger = get_logger("careerpilot.llm.gemini")
T = TypeVar("T", bound=BaseModel)


class GeminiProvider(BaseLLMProvider):
    """
    Official Google Gemini API provider utilizing the google-genai SDK.
    Explicitly tracks connection status and disables silent mock fallbacks in LOCAL_PRIVATE mode.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
    ):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name or settings.GEMINI_MODEL
        self.provider_name = "gemini"
        self.client = None
        self.status = "INITIALIZING"
        self.last_call_at: Optional[str] = None
        self.last_error: Optional[str] = None

        if not self.api_key:
            self.status = "NO_KEY"
            self.last_error = "GEMINI_API_KEY not configured in environment or settings."
            logger.warning(self.last_error)
            return

        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
            self.status = "CONNECTED"
            logger.info(f"GeminiProvider initialized with model {self.model_name}")
        except Exception as e:
            self.status = "ERROR"
            self.last_error = str(e)
            logger.error(f"Failed to initialize google.genai Client: {e}")

    @property
    def masked_key(self) -> Optional[str]:
        if not self.api_key:
            return None
        if len(self.api_key) <= 8:
            return "****"
        return f"{self.api_key[:4]}...{self.api_key[-4:]}"

    def get_status(self) -> Dict[str, Any]:
        return {
            "provider": "gemini",
            "model": self.model_name,
            "status": self.status,
            "is_connected": self.status == "CONNECTED",
            "last_call_at": self.last_call_at,
            "last_error": self.last_error,
            "api_key_configured": bool(self.api_key),
            "api_key_masked": self.masked_key,
        }

    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Generates plain text response using Gemini."""
        if not self.client:
            err = f"GEMINI UNAVAILABLE: Client not initialized. Last error: {self.last_error}"
            self.status = "ERROR"
            self.last_error = err
            logger.error(err)
            raise RuntimeError(err)

        try:
            from google.genai import types

            config_kwargs: Dict[str, Any] = {
                "temperature": temperature,
            }
            if max_tokens:
                config_kwargs["max_output_tokens"] = max_tokens
            if system_instruction:
                config_kwargs["system_instruction"] = system_instruction

            config = types.GenerateContentConfig(**config_kwargs)
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config,
            )

            self.status = "CONNECTED"
            self.last_call_at = datetime.now().isoformat()
            self.last_error = None

            content = response.text or ""
            token_usage = {}
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                token_usage = {
                    "prompt_tokens": getattr(response.usage_metadata, "prompt_token_count", 0),
                    "completion_tokens": getattr(response.usage_metadata, "candidates_token_count", 0),
                    "total_tokens": getattr(response.usage_metadata, "total_token_count", 0),
                }

            return LLMResponse(
                content=content,
                model_name=self.model_name,
                token_usage=token_usage,
                finish_reason="stop",
            )
        except Exception as e:
            self.status = "ERROR"
            err_msg = f"GEMINI UNAVAILABLE: {e}"
            self.last_error = err_msg
            logger.error(err_msg)
            raise RuntimeError(err_msg) from e

    def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        system_instruction: Optional[str] = None,
        temperature: float = 0.1,
    ) -> T:
        """Generates a structured response validated against a Pydantic schema using Gemini native JSON output."""
        if not self.client:
            err = f"GEMINI UNAVAILABLE: Client not initialized. Last error: {self.last_error}"
            self.status = "ERROR"
            self.last_error = err
            logger.error(err)
            raise RuntimeError(err)

        try:
            from google.genai import types

            config_kwargs: Dict[str, Any] = {
                "temperature": temperature,
                "response_mime_type": "application/json",
                "response_schema": schema,
            }
            if system_instruction:
                config_kwargs["system_instruction"] = system_instruction

            config = types.GenerateContentConfig(**config_kwargs)
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config,
            )

            self.status = "CONNECTED"
            self.last_call_at = datetime.now().isoformat()
            self.last_error = None

            raw_json = response.text or "{}"
            return schema.model_validate_json(raw_json)
        except Exception as e:
            self.status = "ERROR"
            err_msg = f"GEMINI UNAVAILABLE: {e}"
            self.last_error = err_msg
            logger.error(err_msg)
            raise RuntimeError(err_msg) from e
