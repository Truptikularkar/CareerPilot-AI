import time
import uuid
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from contextlib import contextmanager
import statistics
from careerpilot.core.logging import get_logger

logger = get_logger("careerpilot.observability")


@dataclass
class TraceEvent:
    trace_id: str
    event_type: str
    operation: str
    duration_ms: float
    status: str
    timestamp: float = field(default_factory=time.time)
    tokens: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "event_type": self.event_type,
            "operation": self.operation,
            "duration_ms": round(self.duration_ms, 2),
            "status": self.status,
            "timestamp": self.timestamp,
            "tokens": self.tokens,
            "metadata": self.metadata,
        }


class EventTracer:
    """
    In-memory lightweight observability tracer tracking workflow events,
    latency percentiles (min, avg, median, p95), and token metrics with zero PII logging.
    """

    def __init__(self, max_traces: int = 200):
        self.max_traces = max_traces
        self._traces: List[TraceEvent] = []
        self._latencies_by_op: Dict[str, List[float]] = {}
        # Configurable model pricing per 1M tokens ($)
        self.pricing_per_1m = {
            "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
            "gemini-1.5-pro": {"input": 3.50, "output": 10.50},
        }

    def record_event(
        self,
        event_type: str,
        operation: str,
        duration_ms: float = 0.0,
        status: str = "SUCCESS",
        tokens: Optional[Dict[str, int]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TraceEvent:
        """Records an execution event trace."""
        trace = TraceEvent(
            trace_id=f"tr_{uuid.uuid4().hex[:8]}",
            event_type=event_type,
            operation=operation,
            duration_ms=max(0.0, duration_ms),
            status=status,
            tokens=tokens or {},
            metadata=metadata or {},
        )
        self._traces.append(trace)
        if len(self._traces) > self.max_traces:
            self._traces.pop(0)

        if operation not in self._latencies_by_op:
            self._latencies_by_op[operation] = []
        self._latencies_by_op[operation].append(duration_ms)
        if len(self._latencies_by_op[operation]) > 500:
            self._latencies_by_op[operation].pop(0)

        return trace

    @contextmanager
    def span(self, event_type: str, operation: str, metadata: Optional[Dict[str, Any]] = None):
        """Context manager measuring execution duration and recording the span trace."""
        t0 = time.perf_counter()
        status = "SUCCESS"
        tokens = {}
        try:
            yield
        except Exception as e:
            status = f"ERROR: {str(e)[:50]}"
            raise
        finally:
            dur_ms = (time.perf_counter() - t0) * 1000.0
            self.record_event(
                event_type=event_type,
                operation=operation,
                duration_ms=dur_ms,
                status=status,
                tokens=tokens,
                metadata=metadata,
            )

    def get_latency_summary(self) -> Dict[str, Dict[str, float]]:
        """Calculates min, avg, median, and p95 latency percentiles per operation."""
        summary = {}
        for op, lat_list in self._latencies_by_op.items():
            if not lat_list:
                continue
            sorted_lat = sorted(lat_list)
            p95_idx = int(len(sorted_lat) * 0.95)
            summary[op] = {
                "count": len(sorted_lat),
                "min_ms": round(min(sorted_lat), 2),
                "avg_ms": round(statistics.mean(sorted_lat), 2),
                "median_ms": round(statistics.median(sorted_lat), 2),
                "p95_ms": round(sorted_lat[min(p95_idx, len(sorted_lat) - 1)], 2),
            }
        return summary

    def get_recent_traces(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Returns recent traces in reverse chronological order."""
        return [t.to_dict() for t in reversed(self._traces[-limit:])]

    def get_token_and_cost_summary(self, model_name: str = "gemini-1.5-flash") -> Dict[str, Any]:
        """Calculates total token consumption and estimated cost."""
        total_in = sum(t.tokens.get("prompt_tokens", 0) for t in self._traces)
        total_out = sum(t.tokens.get("completion_tokens", 0) for t in self._traces)
        total = total_in + total_out

        pricing = self.pricing_per_1m.get(model_name, {"input": 0.0, "output": 0.0})
        cost = (total_in / 1_000_000.0 * pricing["input"]) + (total_out / 1_000_000.0 * pricing["output"])

        return {
            "total_events": len(self._traces),
            "total_tokens": total,
            "prompt_tokens": total_in,
            "completion_tokens": total_out,
            "estimated_cost_usd": round(cost, 6) if total > 0 else 0.0,
            "cost_status": "MEASURED" if total > 0 else "UNKNOWN / OFFLINE MOCK",
        }


# Global Singleton Tracer
tracer = EventTracer()
