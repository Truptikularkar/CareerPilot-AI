import pytest
from pydantic import BaseModel
from careerpilot.llm.base import BaseLLMProvider, LLMResponse
from careerpilot.llm.mock_provider import MockLLMProvider


class SampleStructuredOutput(BaseModel):
    summary: str
    fit_score: float
    is_qualified: bool


def test_mock_llm_provider_generate_text():
    provider = MockLLMProvider(default_response="Deterministic Analysis")
    response = provider.generate_text("Evaluate this job description for a Data Engineer")

    assert isinstance(response, LLMResponse)
    assert "Deterministic Analysis" in response.content
    assert response.model_name == "mock-model-v1"
    assert response.finish_reason == "stop"
    assert "total_tokens" in response.token_usage


def test_mock_llm_provider_generate_structured():
    provider = MockLLMProvider()
    structured = provider.generate_structured(
        prompt="Analyze role fit",
        schema=SampleStructuredOutput,
    )

    assert isinstance(structured, SampleStructuredOutput)
    assert isinstance(structured.summary, str)
    assert isinstance(structured.fit_score, float)
    assert isinstance(structured.is_qualified, bool)
