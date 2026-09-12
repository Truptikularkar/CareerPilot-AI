from typing import Optional, Type, TypeVar, Dict, Any
from pydantic import BaseModel
from careerpilot.llm.base import BaseLLMProvider, LLMResponse

T = TypeVar("T", bound=BaseModel)


class MockLLMProvider(BaseLLMProvider):
    """
    Deterministic, offline mock LLM provider for fast unit tests without network access or API keys.
    """

    def __init__(self, default_response: str = "Mocked LLM Response"):
        self.default_response = default_response
        self.model_name = "mock-model-v1"
        self.provider_name = "mock"


    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        content = f"{self.default_response} for query: {prompt[:60]}..."
        return LLMResponse(
            content=content,
            model_name=self.model_name,
            token_usage={"prompt_tokens": 10, "completion_tokens": 15, "total_tokens": 25},
            finish_reason="stop",
        )

    def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        system_instruction: Optional[str] = None,
        temperature: float = 0.1,
    ) -> T:
        """
        Dynamically constructs a valid mock instance of the requested Pydantic schema.
        """
        mock_values: Dict[str, Any] = {}
        for field_name, field_info in schema.model_fields.items():
            field_type = field_info.annotation
            default_val = field_info.default

            if default_val is not None and str(default_val) != "PydanticUndefined":
                mock_values[field_name] = default_val
            elif field_type is str:
                mock_values[field_name] = f"Mock {field_name}"
            elif field_type in (int, float):
                mock_values[field_name] = 85.0 if field_type is float else 1
            elif field_type is bool:
                mock_values[field_name] = True
            elif hasattr(field_type, "__origin__") and field_type.__origin__ is list:
                mock_values[field_name] = []
            elif hasattr(field_type, "__origin__") and field_type.__origin__ is dict:
                mock_values[field_name] = {}
            else:
                # If nested model, attempt empty instantiation
                try:
                    mock_values[field_name] = field_type()
                except Exception:
                    mock_values[field_name] = None

        return schema.model_validate(mock_values)
