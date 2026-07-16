"""Evaluation tracing for agent executions."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from enum import Enum


class AgentType(Enum):
    DOCUMENT_INTAKE = "document_intake"
    INVOICE_UNDERSTANDING = "invoice_understanding"
    CONTRACT_INTELLIGENCE = "contract_intelligence"
    PO_MATCHING = "po_matching"
    FINANCE_POLICY = "finance_policy"
    EXCEPTION_DETECTION = "exception_detection"
    FRAUD_INTELLIGENCE = "fraud_intelligence"
    RECOMMENDATION = "recommendation"
    WORKFLOW = "workflow"
    REPORTING = "reporting"
    COPILOT = "copilot"


class ToolCallType(Enum):
    OCR = "ocr"
    DATABASE_QUERY = "database_query"
    VECTOR_SEARCH = "vector_search"
    LLM_CALL = "llm_call"
    API_CALL = "api_call"
    FILE_OPERATION = "file_operation"


@dataclass
class ToolCall:
    """Represents a single tool call during agent execution."""
    tool_type: ToolCallType
    tool_name: str
    input_data: dict[str, Any] = field(default_factory=dict)
    output_data: dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0.0
    success: bool = True
    error_message: str | None = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AgentTrace:
    """Trace for a single agent execution."""
    agent_type: AgentType
    invoice_id: str | None = None
    agent_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: datetime | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    input_context: dict[str, Any] = field(default_factory=dict)
    output_context: dict[str, Any] = field(default_factory=dict)
    reasoning: str | None = None
    confidence: float | None = None
    success: bool = True
    error: str | None = None

    @property
    def duration_ms(self) -> float | None:
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return None

    @property
    def tool_call_count(self) -> int:
        return len(self.tool_calls)

    @property
    def failed_tool_calls(self) -> int:
        return sum(1 for tc in self.tool_calls if not tc.success)

    def add_tool_call(self, tool_call: ToolCall):
        self.tool_calls.append(tool_call)

    def finalize(self, output_context: dict[str, Any], reasoning: str, confidence: float):
        self.end_time = datetime.utcnow()
        self.output_context = output_context
        self.reasoning = reasoning
        self.confidence = confidence


@dataclass
class EvaluationTrace:
    """Complete evaluation trace for an invoice processing pipeline."""
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    invoice_id: str | None = None
    invoice_number: str | None = None
    pipeline_start: datetime = field(default_factory=datetime.utcnow)
    pipeline_end: datetime | None = None
    agent_traces: list[AgentTrace] = field(default_factory=list)
    final_status: str | None = None
    exceptions_detected: int = 0
    matched_po: bool = False
    matched_contract: bool = False
    auto_approved: bool = False
    routed_to: str | None = None

    @property
    def duration_ms(self) -> float | None:
        if self.pipeline_end and self.pipeline_start:
            return (self.pipeline_end - self.pipeline_start).total_seconds() * 1000
        return None

    @property
    def total_tool_calls(self) -> int:
        return sum(at.tool_call_count for at in self.agent_traces)

    @property
    def total_failed_calls(self) -> int:
        return sum(at.failed_tool_calls for at in self.agent_traces)

    def add_agent_trace(self, agent_trace: AgentTrace):
        self.agent_traces.append(agent_trace)

    def finalize(self, final_status: str, exceptions_detected: int):
        self.pipeline_end = datetime.utcnow()
        self.final_status = final_status
        self.exceptions_detected = exceptions_detected

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "invoice_id": self.invoice_id,
            "invoice_number": self.invoice_number,
            "pipeline_start": self.pipeline_start.isoformat(),
            "pipeline_end": self.pipeline_end.isoformat() if self.pipeline_end else None,
            "duration_ms": self.duration_ms,
            "total_tool_calls": self.total_tool_calls,
            "total_failed_calls": self.total_failed_calls,
            "agent_traces": [
                {
                    "agent_type": at.agent_type.value,
                    "start_time": at.start_time.isoformat(),
                    "end_time": at.end_time.isoformat() if at.end_time else None,
                    "duration_ms": at.duration_ms,
                    "tool_call_count": at.tool_call_count,
                    "failed_tool_calls": at.failed_tool_calls,
                    "confidence": at.confidence,
                    "success": at.success,
                }
                for at in self.agent_traces
            ],
            "final_status": self.final_status,
            "exceptions_detected": self.exceptions_detected,
            "matched_po": self.matched_po,
            "matched_contract": self.matched_contract,
            "auto_approved": self.auto_approved,
            "routed_to": self.routed_to,
        }