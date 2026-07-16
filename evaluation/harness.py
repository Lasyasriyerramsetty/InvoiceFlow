"""Evaluation harness for running agent evaluations."""

import asyncio
from datetime import datetime
from typing import Any
import uuid

from .metrics import EvaluationMetrics
from .trace import EvaluationTrace, AgentTrace, AgentType, ToolCall, ToolCallType


class EvaluationHarness:
    """Harness for evaluating agent executions."""

    def __init__(self):
        self.metrics = EvaluationMetrics()
        self._active_traces: dict[str, EvaluationTrace] = {}

    def start_trace(self, invoice_id: str, invoice_number: str | None = None) -> EvaluationTrace:
        trace = EvaluationTrace(invoice_id=invoice_id, invoice_number=invoice_number)
        self._active_traces[invoice_id] = trace
        return trace

    def record_agent_execution(
        self,
        trace: EvaluationTrace,
        agent_type: AgentType,
        input_context: dict[str, Any],
        tool_calls: list[tuple[str, ToolCallType, dict[str, Any], dict[str, Any], float, bool]] | None = None,
        output_context: dict[str, Any] | None = None,
        reasoning: str | None = None,
        confidence: float | None = None,
        success: bool = True,
        error: str | None = None,
    ):
        agent_trace = AgentTrace(
            agent_type=agent_type,
            invoice_id=trace.invoice_id,
            input_context=input_context,
            success=success,
            error=error,
        )
        if tool_calls:
            for tool_name, tool_type, in_data, out_data, latency, ok in tool_calls:
                agent_trace.add_tool_call(
                    ToolCall(
                        tool_type=tool_type,
                        tool_name=tool_name,
                        input_data=in_data,
                        output_data=out_data,
                        latency_ms=latency,
                        success=ok,
                    )
                )
        if output_context is not None and reasoning is not None and confidence is not None:
            agent_trace.finalize(output_context, reasoning, confidence)
        trace.add_agent_trace(agent_trace)

    def finalize_trace(
        self,
        trace: EvaluationTrace,
        final_status: str,
        exceptions_detected: int = 0,
        matched_po: bool = False,
        matched_contract: bool = False,
        auto_approved: bool = False,
        routed_to: str | None = None,
    ):
        trace.finalize(final_status, exceptions_detected)
        trace.matched_po = matched_po
        trace.matched_contract = matched_contract
        trace.auto_approved = auto_approved
        trace.routed_to = routed_to
        self.metrics.add_trace(trace)
        if trace.invoice_id in self._active_traces:
            del self._active_traces[trace.invoice_id]

    def get_metrics(self) -> EvaluationMetrics:
        return self.metrics

    def reset(self):
        self.metrics = EvaluationMetrics()
        self._active_traces.clear()


harness = EvaluationHarness()