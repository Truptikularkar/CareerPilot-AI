import pytest
import time
from careerpilot.observability.tracer import EventTracer, TraceEvent


def test_tracer_event_recording():
    tracer = EventTracer(max_traces=50)
    evt = tracer.record_event(
        event_type="TEST_EVENT",
        operation="unit_test_op",
        duration_ms=12.5,
        status="SUCCESS",
        tokens={"prompt_tokens": 100, "completion_tokens": 50},
        metadata={"job_id": "job_123"},
    )
    assert isinstance(evt, TraceEvent)
    assert evt.operation == "unit_test_op"
    assert evt.duration_ms == 12.5
    assert evt.tokens["prompt_tokens"] == 100

    recent = tracer.get_recent_traces(limit=10)
    assert len(recent) == 1
    assert recent[0]["operation"] == "unit_test_op"


def test_tracer_span_context_manager():
    tracer = EventTracer(max_traces=50)
    with tracer.span("TEST_SPAN", "fast_operation"):
        time.sleep(0.01)

    summary = tracer.get_latency_summary()
    assert "fast_operation" in summary
    assert summary["fast_operation"]["count"] == 1
    assert summary["fast_operation"]["min_ms"] > 0.0


def test_tracer_latency_percentiles():
    tracer = EventTracer(max_traces=100)
    latencies = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
    for lat in latencies:
        tracer.record_event("TEST", "bench_op", duration_ms=lat)

    summary = tracer.get_latency_summary()
    assert summary["bench_op"]["min_ms"] == 10.0
    assert summary["bench_op"]["avg_ms"] == 55.0
    assert summary["bench_op"]["median_ms"] == 55.0
    assert summary["bench_op"]["p95_ms"] == 100.0


def test_tracer_token_and_cost_calculation():
    tracer = EventTracer()
    tracer.record_event(
        "LLM_CALL",
        "gemini_call",
        tokens={"prompt_tokens": 10_000, "completion_tokens": 2_000},
    )
    cost_info = tracer.get_token_and_cost_summary(model_name="gemini-1.5-flash")
    assert cost_info["total_tokens"] == 12_000
    assert cost_info["prompt_tokens"] == 10_000
    assert cost_info["completion_tokens"] == 2_000
    assert cost_info["estimated_cost_usd"] > 0.0
