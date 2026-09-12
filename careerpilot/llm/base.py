from abc import ABC, abstractmethod
from typing import Optional, Type, TypeVar, Dict, Any
from pydantic import BaseModel, Field

T = TypeVar("T", bound=BaseModel)


class LLMResponse(BaseModel):
    """Standardized LLM response object."""
    content: str
    model_name: str
    token_usage: Dict[str, int] = Field(default_factory=dict)
    finish_reason: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None


class BaseLLMProvider(ABC):
    """Abstract interface for pluggable LLM backends (Gemini, Ollama, Mock)."""

    @abstractmethod
    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Generates plain text response."""
        pass

    @abstractmethod
    def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        system_instruction: Optional[str] = None,
        temperature: float = 0.1,
    ) -> T:
        """Generates a response validated against a Pydantic schema."""
        pass
