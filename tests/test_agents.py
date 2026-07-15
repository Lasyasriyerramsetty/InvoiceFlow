import pytest
import uuid
from decimal import Decimal
from datetime import date

from agents.document_intake.agent import DocumentIntakeAgent
from agents.invoice_understanding.agent import InvoiceUnderstandingAgent
from agents.contract_intelligence.agent import ContractIntelligenceAgent
from agents.po_matching.agent import POMatchingAgent
from agents.finance_policy.agent import FinancePolicyAgent
from agents.exception_detection.agent import ExceptionDetectionAgent
from agents.fraud_intelligence.agent import FraudIntelligenceAgent
from agents.recommendation.agent import RecommendationAgent
from agents.workflow.agent import WorkflowAgent
from agents.reporting.agent import ReportingAgent


class TestAgents:
    @pytest.fixture
    def sample_invoice_text(self) -> str:
        return """INVOICE

Invoice Number: INV-2024-1456
Invoice Date: 15/06/2024
Due Date: 15/07/2024

From: Acme Corporation Pvt Ltd
GSTIN: 27AABCA1234A1Z5

Bill To: Enterprise Finance Corp

PO Number: PO-2024-8891

Description                    Qty    Unit Price    Amount
Cloud Services License          100    ₹425.00      ₹42,500.00
Implementation Support           40    ₹850.00      ₹34,000.00

Subtotal:                                          ₹76,500.00
GST (18%):                                         ₹13,770.00
Total Amount Due:                                  ₹90,270.00

Payment Terms: Net 30
Currency: INR
"""

    @pytest.fixture
    def sample_bytes(self, sample_invoice_text) -> bytes:
        return sample_invoice_text.encode("utf-8")

    @pytest.mark.asyncio
    async def test_document_intake_agent(self, sample_bytes):
        agent = DocumentIntakeAgent()
        result = await agent.execute({
            "document_bytes": sample_bytes,
            "filename": "test_invoice.pdf",
        })

        assert "classification" in result
        assert result["classification"]["document_type"] == "invoice"
        assert result["ocr_text"] != ""
        assert "insight" in result

    @pytest.mark.asyncio
    async def test_invoice_understanding_agent(self, sample_invoice_text):
        agent = InvoiceUnderstandingAgent()
        result = await agent.execute({
            "normalized_text": sample_invoice_text,
        })

        assert "extracted_invoice" in result
        invoice = result["extracted_invoice"]
        assert invoice["invoice_number"] == "INV-2024-1456"
        assert invoice["vendor_name"] == "Acme Corporation Pvt Ltd"
        assert len(invoice["line_items"]) == 2

    @pytest.mark.asyncio
    async def test_contract_intelligence_agent(self):
        agent = ContractIntelligenceAgent()
        result = await agent.execute({
            "extracted_invoice": {
                "vendor_name": "Acme Corporation",
                "line_items": [{"description": "Cloud Services"}],
            },
        })

        assert "contract_clauses" in result
        assert "pricing_limits" in result

    @pytest.mark.asyncio
    async def test_po_matching_agent(self, sample_invoice_text):
        agent = POMatchingAgent()
        result = await agent.execute({
            "extracted_invoice": {
                "total_amount": Decimal("90270"),
                "currency": "INR",
                "po_number": "PO-2024-8891",
                "line_items": [
                    {"line_number": 1, "description": "Cloud Services", "quantity": Decimal("100"), "unit_price": Decimal("425"), "total_amount": Decimal("42500")},
                    {"line_number": 2, "description": "Support", "quantity": Decimal("40"), "unit_price": Decimal("850"), "total_amount": Decimal("34000")},
                ],
            },
        })

        assert "po_match_result" in result
        assert "mismatches" in result["po_match_result"]

    @pytest.mark.asyncio
    async def test_finance_policy_agent(self):
        agent = FinancePolicyAgent()
        result = await agent.execute({
            "extracted_invoice": {"total_amount": Decimal("5000")},
            "vendor_country": "US",
        })

        assert "policy_validation" in result
        assert "violations" in result["policy_validation"]

    @pytest.mark.asyncio
    async def test_exception_detection_agent(self):
        agent = ExceptionDetectionAgent()
        result = await agent.execute({
            "po_match_result": {
                "mismatches": [
                    {"type": "price_mismatch", "severity": "high", "description": "Price exceeds limit", "expected": "400", "actual": "425"}
                ]
            },
            "extracted_invoice": {"total_amount": Decimal("90270")},
        })

        assert "exceptions" in result
        assert "risk_factors" in result

    @pytest.mark.asyncio
    async def test_workflow_agent(self):
        agent = WorkflowAgent()
        result = await agent.execute({
            "risk_factors": 50,
            "extracted_invoice": {"total_amount": Decimal("25000")},
        })

        assert "workflow_routes" in result
        assert len(result["workflow_routes"]) > 0

    @pytest.mark.asyncio
    async def test_recommendation_and_reporting_agents(self):
        rec_agent = RecommendationAgent()
        rec = await rec_agent.execute({
            "exceptions": [{"category": "price_mismatch", "severity": "high"}],
            "extracted_invoice": {"total_amount": Decimal("90270")},
        })
        assert "recommendation" in rec

        rep_agent = ReportingAgent()
        rep = await rep_agent.execute({
            "extracted_invoice": {"invoice_number": "INV-1"},
            "exceptions": rec.get("exceptions", []),
            "recommendation": rec.get("recommendation"),
            "risk_score": 50,
        })
        assert "report" in rep