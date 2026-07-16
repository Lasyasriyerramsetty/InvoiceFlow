"""Demo runner for evaluation suite."""

import sys
from pathlib import Path

# Ensure the project root is in the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluation.harness import harness
from evaluation.trace import AgentType, ToolCallType
from datetime import datetime


def run_demo():
    """Run a demo evaluation with sample data."""
    print("=" * 60)
    print("InvoiceFlow Evaluation Suite - Demo Run")
    print("=" * 60)

    # Start trace for an invoice
    trace = harness.start_trace("inv-demo-1", "INV-DEMO-001")

    # Simulate Document Intake Agent
    harness.record_agent_execution(
        trace,
        AgentType.DOCUMENT_INTAKE,
        input_context={"document_type": "pdf", "filename": "invoice.pdf"},
        tool_calls=[
            ("azure_ocr", ToolCallType.OCR, {"file": "invoice.pdf"}, {"text": "..."}, 450.0, True),
        ],
        output_context={"classified_as": "invoice", "confidence": 0.98},
        reasoning="Document successfully classified as invoice with high quality",
        confidence=0.98,
    )

    # Simulate Invoice Understanding Agent
    harness.record_agent_execution(
        trace,
        AgentType.INVOICE_UNDERSTANDING,
        input_context={"ocr_text": "..."},
        tool_calls=[
            ("gpt4_extraction", ToolCallType.LLM_CALL, {"prompt": "extract fields"}, {"fields": {}}, 1200.0, True),
        ],
        output_context={"invoice_number": "INV-DEMO-001", "total_amount": 115000.0},
        reasoning="Successfully extracted all required fields with 96% confidence",
        confidence=0.96,
    )

    # Simulate PO Matching Agent
    harness.record_agent_execution(
        trace,
        AgentType.PO_MATCHING,
        input_context={"invoice_total": 115000.0},
        tool_calls=[
            ("db_query_po", ToolCallType.DATABASE_QUERY, {"po_number": "PO-123"}, {"po": {}}, 15.0, True),
        ],
        output_context={"match_score": 65, "mismatches": 2},
        reasoning="3-way match failed due to price mismatches on 2 line items",
        confidence=0.90,
    )

    # Simulate Exception Detection Agent
    harness.record_agent_execution(
        trace,
        AgentType.EXCEPTION_DETECTION,
        input_context={"mismatches": 2},
        tool_calls=[
            ("exception_classifier", ToolCallType.LLM_CALL, {"data": "..."}, {"exceptions": []}, 800.0, True),
        ],
        output_context={"exceptions": 2, "risk_score": 48},
        reasoning="Detected 2 price mismatch exceptions with medium-high risk",
        confidence=0.89,
    )

    # Simulate Workflow Agent
    harness.record_agent_execution(
        trace,
        AgentType.WORKFLOW,
        input_context={"risk_score": 48, "amount": 115000.0},
        tool_calls=[],
        output_context={"routes": ["Procurement", "Finance Manager"]},
        reasoning="Invoice requires procurement review due to price mismatches",
        confidence=0.93,
    )

    # Finalize trace
    harness.finalize_trace(
        trace,
        final_status="pending_approval",
        exceptions_detected=2,
        matched_po=True,
        matched_contract=True,
        auto_approved=False,
        routed_to="Procurement Manager",
    )

    # Get and display metrics
    metrics = harness.get_metrics()
    summary = metrics.to_summary()

    print("\n📊 Evaluation Results:")
    print(f"Total Traces: {summary['total_traces']}")
    print(f"Avg Pipeline Latency: {summary['avg_pipeline_latency_ms']:.2f}ms")
    print(f"\n💼 Business Metrics:")
    print(f"  Total Invoices Processed: {summary['business_metrics']['total_invoices_processed']}")
    print(f"  Straight-Through Rate: {summary['business_metrics']['straight_through_rate']:.1f}%")
    print(f"  Exception Rate: {summary['business_metrics']['exception_rate']:.1f}%")
    print(f"  Auto-Approved: {summary['business_metrics']['auto_approved_count']}")
    print(f"  Manual Review: {summary['business_metrics']['manual_review_count']}")
    print(f"\n🤖 Agent Performance:")
    for agent_type, agent_data in summary['agent_metrics'].items():
        print(f"  {agent_type}:")
        print(f"    Executions: {agent_data['total_executions']}")
        print(f"    Success Rate: {agent_data['success_rate']:.1f}%")
        print(f"    Avg Duration: {agent_data['avg_duration_ms']:.2f}ms")
        print(f"    Avg Confidence: {agent_data['avg_confidence']:.2f}")
    print(f"\n🔧 Top Tools Used:")
    for tool, count in summary['top_tools']:
        print(f"  {tool}: {count} calls")

    print("\n" + "=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    run_demo()