"""Tests for evaluation suite."""

import pytest
from datetime import datetime

from evaluation.trace import EvaluationTrace, AgentTrace, AgentType, ToolCall, ToolCallType
from evaluation.metrics import EvaluationMetrics, BusinessMetrics, AgentMetrics
from evaluation.harness import EvaluationHarness


class TestEvaluationTrace:
    def test_agent_trace_duration(self):
        trace = AgentTrace(agent_type=AgentType.PO_MATCHING)
        trace.start_time = datetime(2024, 1, 1, 10, 0, 0)
        trace.end_time = datetime(2024, 1, 1, 10, 0, 1)
        assert trace.duration_ms == 1000.0

    def test_agent_trace_tool_calls(self):
        trace = AgentTrace(agent_type=AgentType.EXCEPTION_DETECTION)
        trace.add_tool_call(
            ToolCall(tool_type=ToolCallType.DATABASE_QUERY, tool_name="query_exceptions", latency_ms=25.0)
        )
        trace.add_tool_call(
            ToolCall(tool_type=ToolCallType.LLM_CALL, tool_name="gpt4_analysis", latency_ms=150.0, success=False)
        )
        assert trace.tool_call_count == 2
        assert trace.failed_tool_calls == 1

    def test_evaluation_trace_to_dict(self):
        trace = EvaluationTrace(invoice_id="inv-1", invoice_number="INV-001")
        trace.finalize("approved", 0)
        trace.auto_approved = True
        data = trace.to_dict()
        assert data["invoice_number"] == "INV-001"
        assert data["final_status"] == "approved"
        assert data["exceptions_detected"] == 0
        assert data["auto_approved"] is True


class TestEvaluationMetrics:
    def test_empty_metrics(self):
        metrics = EvaluationMetrics()
        assert metrics.total_traces == 0
        assert metrics.avg_pipeline_latency_ms is None

    def test_business_metrics(self):
        metrics = EvaluationMetrics()
        trace1 = EvaluationTrace(invoice_id="inv-1")
        trace1.auto_approved = True
        trace1.exceptions_detected = 0
        trace1.pipeline_start = datetime(2024, 1, 1, 10, 0, 0)
        trace1.pipeline_end = datetime(2024, 1, 1, 10, 0, 1)

        trace2 = EvaluationTrace(invoice_id="inv-2")
        trace2.auto_approved = False
        trace2.exceptions_detected = 2
        trace2.pipeline_start = datetime(2024, 1, 1, 10, 0, 0)
        trace2.pipeline_end = datetime(2024, 1, 1, 10, 0, 2)

        metrics.add_trace(trace1)
        metrics.add_trace(trace2)

        assert metrics.business_metrics.total_invoices_processed == 2
        assert metrics.business_metrics.straight_through_rate == 50.0
        assert metrics.business_metrics.exception_rate == 100.0
        assert metrics.business_metrics.avg_processing_time_ms == 1500.0


class TestEvaluationHarness:
    def test_harness_basic_flow(self):
        harness = EvaluationHarness()
        trace = harness.start_trace("inv-1", "INV-001")
        harness.record_agent_execution(
            trace,
            AgentType.PO_MATCHING,
            input_context={"invoice_id": "inv-1"},
            tool_calls=[
                ("ocr_service", ToolCallType.OCR, {}, {}, 120.0, True)
            ],
            output_context={"match_score": 95},
            reasoning="PO matched successfully",
            confidence=0.95,
        )
        harness.finalize_trace(trace, "approved", auto_approved=True)
        metrics = harness.get_metrics()
        assert metrics.total_traces == 1
        assert metrics.business_metrics.auto_approved_count == 1