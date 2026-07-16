"""Evaluation metrics API."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

# In-memory store for demo purposes
_eval_traces: list[dict[str, Any]] = []
_eval_metrics: dict[str, Any] = {
    "total_traces": 1,
    "avg_pipeline_latency_ms": 2450.0,
    "business_metrics": {
        "total_invoices_processed": 1,
        "straight_through_rate": 0.0,
        "exception_rate": 200.0,
        "auto_approved_count": 0,
        "manual_review_count": 1,
        "total_savings": 0.0,
        "avg_processing_time_ms": 2450.0,
        "po_match_rate": 100.0,
        "contract_match_rate": 100.0,
        "fraud_detected": 0,
        "duplicate_prevented": 0,
    },
    "agent_metrics": {
        "document_intake": {
            "total_executions": 1,
            "success_rate": 100.0,
            "avg_duration_ms": 450.0,
            "avg_confidence": 0.98,
            "tool_call_success_rate": 100.0,
        },
        "invoice_understanding": {
            "total_executions": 1,
            "success_rate": 100.0,
            "avg_duration_ms": 1200.0,
            "avg_confidence": 0.96,
            "tool_call_success_rate": 100.0,
        },
        "po_matching": {
            "total_executions": 1,
            "success_rate": 100.0,
            "avg_duration_ms": 15.0,
            "avg_confidence": 0.90,
            "tool_call_success_rate": 100.0,
        },
        "exception_detection": {
            "total_executions": 1,
            "success_rate": 100.0,
            "avg_duration_ms": 800.0,
            "avg_confidence": 0.89,
            "tool_call_success_rate": 100.0,
        },
        "workflow": {
            "total_executions": 1,
            "success_rate": 100.0,
            "avg_duration_ms": 0.0,
            "avg_confidence": 0.93,
            "tool_call_success_rate": 0.0,
        },
    },
    "top_tools": [
        {"tool": "invoice_understanding.gpt4_extraction", "count": 1},
        {"tool": "document_intake.azure_ocr", "count": 1},
        {"tool": "exception_detection.exception_classifier", "count": 1},
        {"tool": "po_matching.db_query_po", "count": 1},
    ],
}


class EvalRequest(BaseModel):
    trace: dict[str, Any]


@router.get("/evaluation/summary")
async def get_evaluation_summary():
    return _eval_metrics


@router.post("/evaluation/traces")
async def add_evaluation_trace(payload: EvalRequest):
    _eval_traces.append(payload.trace)
    return {"status": "ok"}