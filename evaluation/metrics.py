"""Evaluation metrics calculation."""

from dataclasses import dataclass
from typing import Any
from collections import defaultdict

from .trace import EvaluationTrace, AgentTrace, ToolCallType


@dataclass
class AgentMetrics:
    """Metrics for a single agent."""
    agent_type: str
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    total_duration_ms: float = 0.0
    total_tool_calls: int = 0
    total_failed_tool_calls: int = 0
    avg_confidence: float = 0.0
    confidence_sum: float = 0.0

    @property
    def success_rate(self) -> float:
        if self.total_executions == 0:
            return 0.0
        return (self.successful_executions / self.total_executions) * 100

    @property
    def avg_duration_ms(self) -> float | None:
        if self.total_executions == 0:
            return None
        return self.total_duration_ms / self.total_executions

    @property
    def tool_call_success_rate(self) -> float:
        if self.total_tool_calls == 0:
            return 100.0
        return ((self.total_tool_calls - self.total_failed_tool_calls) / self.total_tool_calls) * 100

    def add_trace(self, agent_trace: AgentTrace):
        self.total_executions += 1
        if agent_trace.success:
            self.successful_executions += 1
        else:
            self.failed_executions += 1
        if agent_trace.duration_ms:
            self.total_duration_ms += agent_trace.duration_ms
        self.total_tool_calls += agent_trace.tool_call_count
        self.total_failed_tool_calls += agent_trace.failed_tool_calls
        if agent_trace.confidence is not None:
            self.confidence_sum += agent_trace.confidence
            self.avg_confidence = self.confidence_sum / self.total_executions


@dataclass
class BusinessMetrics:
    """Business impact metrics."""
    total_invoices_processed: int = 0
    total_invoice_value: float = 0.0
    auto_approved_count: int = 0
    manual_review_count: int = 0
    exceptions_detected: int = 0
    total_savings: float = 0.0
    avg_processing_time_ms: float = 0.0
    po_match_rate: float = 0.0
    contract_match_rate: float = 0.0
    fraud_detected: int = 0
    duplicate_prevented: int = 0
    total_processing_time_ms: float = 0.0

    @property
    def straight_through_rate(self) -> float:
        if self.total_invoices_processed == 0:
            return 0.0
        return (self.auto_approved_count / self.total_invoices_processed) * 100

    @property
    def exception_rate(self) -> float:
        if self.total_invoices_processed == 0:
            return 0.0
        return (self.exceptions_detected / self.total_invoices_processed) * 100

    @property
    def savings_per_invoice(self) -> float:
        if self.total_invoices_processed == 0:
            return 0.0
        return self.total_savings / self.total_invoices_processed

    def add_trace(self, trace: EvaluationTrace):
        self.total_invoices_processed += 1
        if trace.auto_approved:
            self.auto_approved_count += 1
        else:
            self.manual_review_count += 1
        self.exceptions_detected += trace.exceptions_detected
        if trace.duration_ms:
            self.total_processing_time_ms += trace.duration_ms
            self.avg_processing_time_ms = self.total_processing_time_ms / self.total_invoices_processed
        if trace.matched_po:
            self.po_match_rate = ((self.po_match_rate * (self.total_invoices_processed - 1)) + 1) / self.total_invoices_processed
        if trace.matched_contract:
            self.contract_match_rate = ((self.contract_match_rate * (self.total_invoices_processed - 1)) + 1) / self.total_invoices_processed


class EvaluationMetrics:
    """Aggregated evaluation metrics."""

    def __init__(self):
        self.traces: list[EvaluationTrace] = []
        self.agent_metrics: dict[str, AgentMetrics] = defaultdict(
            lambda: AgentMetrics(agent_type="unknown")
        )
        self.business_metrics = BusinessMetrics()
        self.tool_usage: dict[str, int] = defaultdict(int)
        self.tool_latency: dict[str, list[float]] = defaultdict(list)

    def add_trace(self, trace: EvaluationTrace):
        self.traces.append(trace)
        self.business_metrics.add_trace(trace)
        for agent_trace in trace.agent_traces:
            agent_key = agent_trace.agent_type.value
            if agent_key not in self.agent_metrics:
                self.agent_metrics[agent_key] = AgentMetrics(agent_type=agent_key)
            self.agent_metrics[agent_key].add_trace(agent_trace)
            for tool_call in agent_trace.tool_calls:
                tool_key = f"{agent_trace.agent_type.value}.{tool_call.tool_name}"
                self.tool_usage[tool_key] += 1
                if tool_call.latency_ms > 0:
                    self.tool_latency[tool_key].append(tool_call.latency_ms)

    @property
    def total_traces(self) -> int:
        return len(self.traces)

    @property
    def avg_pipeline_latency_ms(self) -> float | None:
        durations = [t.duration_ms for t in self.traces if t.duration_ms is not None]
        if not durations:
            return None
        return sum(durations) / len(durations)

    def get_agent_metrics(self, agent_type: str) -> AgentMetrics | None:
        return self.agent_metrics.get(agent_type)

    def get_top_tools_by_usage(self, limit: int = 10) -> list[tuple[str, int]]:
        sorted_tools = sorted(self.tool_usage.items(), key=lambda x: x[1], reverse=True)
        return sorted_tools[:limit]

    def get_avg_tool_latency(self, tool_key: str) -> float | None:
        latencies = self.tool_latency.get(tool_key, [])
        if not latencies:
            return None
        return sum(latencies) / len(latencies)

    def to_summary(self) -> dict[str, Any]:
        return {
            "total_traces": self.total_traces,
            "avg_pipeline_latency_ms": self.avg_pipeline_latency_ms,
            "business_metrics": {
                "total_invoices_processed": self.business_metrics.total_invoices_processed,
                "straight_through_rate": self.business_metrics.straight_through_rate,
                "exception_rate": self.business_metrics.exception_rate,
                "auto_approved_count": self.business_metrics.auto_approved_count,
                "manual_review_count": self.business_metrics.manual_review_count,
                "total_savings": self.business_metrics.total_savings,
                "avg_processing_time_ms": self.business_metrics.avg_processing_time_ms,
                "po_match_rate": self.business_metrics.po_match_rate,
                "contract_match_rate": self.business_metrics.contract_match_rate,
                "fraud_detected": self.business_metrics.fraud_detected,
                "duplicate_prevented": self.business_metrics.duplicate_prevented,
            },
            "agent_metrics": {
                agent_type: {
                    "total_executions": metrics.total_executions,
                    "success_rate": metrics.success_rate,
                    "avg_duration_ms": metrics.avg_duration_ms,
                    "avg_confidence": metrics.avg_confidence,
                    "tool_call_success_rate": metrics.tool_call_success_rate,
                }
                for agent_type, metrics in self.agent_metrics.items()
            },
            "top_tools": self.get_top_tools_by_usage(10),
        }