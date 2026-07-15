import uuid
from datetime import datetime, timezone
from decimal import Decimal

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from agents.orchestrator.pipeline import InvoiceProcessingPipeline
from backend.app.infrastructure.database.models import (
    AgentInsightRecord,
    ApprovalWorkflow,
    Invoice,
    InvoiceException,
    InvoiceStatus,
)
from backend.app.infrastructure.database.repositories import (
    ExceptionRepository,
    InsightRepository,
    InvoiceRepository,
    WorkflowRepository,
)
from shared.schemas.agent_outputs import ExceptionDetail, ProcessingPipelineResult

logger = structlog.get_logger(__name__)


class InvoiceProcessingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.invoice_repo = InvoiceRepository(session)
        self.exception_repo = ExceptionRepository(session)
        self.workflow_repo = WorkflowRepository(session)
        self.insight_repo = InsightRepository(session)
        self.pipeline = InvoiceProcessingPipeline()

    async def process_invoice(
        self,
        invoice_id: uuid.UUID,
        document_bytes: bytes,
        filename: str,
        context: dict | None = None,
    ) -> ProcessingPipelineResult:
        invoice = await self.invoice_repo.get_by_id(invoice_id)
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")

        invoice.status = InvoiceStatus.PROCESSING
        await self.invoice_repo.update(invoice)

        result = await self.pipeline.run(
            invoice_id=str(invoice_id),
            document_bytes=document_bytes,
            filename=filename,
            context=context or {},
        )

        invoice.status = (
            InvoiceStatus.PENDING_APPROVAL
            if result.exceptions
            else InvoiceStatus.APPROVED if result.risk_score and result.risk_score.overall_score < 30
            else InvoiceStatus.PENDING_APPROVAL
        )
        invoice.auto_approved = (
            not result.exceptions
            and result.risk_score is not None
            and result.risk_score.overall_score < 20
        )
        invoice.risk_score = result.risk_score.overall_score if result.risk_score else 0
        invoice.fraud_score = result.fraud_assessment.fraud_confidence * 100 if result.fraud_assessment else 0
        invoice.compliance_score = result.risk_score.compliance_score if result.risk_score else 100
        invoice.health_score = max(0, 100 - invoice.risk_score)
        invoice.processing_time_ms = result.processing_time_ms
        invoice.extracted_data_json = result.extracted_invoice
        invoice.ai_summary = result.recommendation.summary if result.recommendation else None

        if result.extracted_invoice:
            extracted = result.extracted_invoice
            invoice.invoice_number = extracted.get("invoice_number", invoice.invoice_number)
            invoice.total_amount = float(extracted.get("total_amount", invoice.total_amount))
            invoice.currency = extracted.get("currency", invoice.currency)
            invoice.tax_amount = float(extracted.get("tax_amount", invoice.tax_amount))
            invoice.subtotal = float(extracted.get("subtotal", invoice.subtotal))
            invoice.payment_terms = extracted.get("payment_terms", invoice.payment_terms)

        await self._persist_exceptions(invoice_id, result.exceptions)
        await self._persist_insights(invoice_id, result.agent_insights)
        await self._persist_workflow(invoice_id, result.workflow_routes)
        await self.invoice_repo.update(invoice)

        logger.info(
            "invoice_processed",
            invoice_id=str(invoice_id),
            exceptions=len(result.exceptions),
            risk_score=invoice.risk_score,
        )
        return result

    async def _persist_exceptions(
        self, invoice_id: uuid.UUID, exceptions: list[ExceptionDetail]
    ) -> None:
        records = [
            InvoiceException(
                invoice_id=invoice_id,
                category=exc.category.value,
                severity=exc.severity.value,
                title=exc.title,
                description=exc.description,
                reasoning=exc.reasoning,
                confidence=exc.confidence,
                evidence_json={"evidence": exc.evidence},
                contract_clause=exc.contract_clause,
                policy_reference=exc.policy_reference,
                suggested_resolution=exc.suggested_resolution,
                business_impact=exc.business_impact,
                financial_impact=float(exc.financial_impact),
                estimated_loss=float(exc.estimated_loss),
            )
            for exc in exceptions
        ]
        if records:
            await self.exception_repo.create_bulk(records)

    async def _persist_insights(self, invoice_id: uuid.UUID, insights: list) -> None:
        records = [
            AgentInsightRecord(
                invoice_id=invoice_id,
                agent_name=insight.agent_name,
                reasoning=insight.reasoning,
                confidence=insight.confidence,
                evidence_json={"evidence": insight.evidence},
                metadata_json={
                    "policy_references": insight.policy_references,
                    "contract_clauses": insight.contract_clauses,
                    "suggested_resolution": insight.suggested_resolution,
                    "business_impact": insight.business_impact,
                    "financial_impact": str(insight.financial_impact),
                    "next_action": insight.next_action,
                },
            )
            for insight in insights
        ]
        if records:
            await self.insight_repo.create_bulk(records)

    async def _persist_workflow(self, invoice_id: uuid.UUID, routes: list) -> None:
        records = [
            ApprovalWorkflow(
                invoice_id=invoice_id,
                approver_role=route.approver_role,
                department=route.department,
                priority=route.priority,
                reason=route.reason,
                sla_hours=route.sla_hours,
                status="pending",
            )
            for route in routes
        ]
        if records:
            await self.workflow_repo.create_routes(records)


class DashboardService:
    def __init__(self, session: AsyncSession) -> None:
        self.invoice_repo = InvoiceRepository(session)
        self.exception_repo = ExceptionRepository(session)

    async def get_kpis(self) -> dict:
        metrics = await self.invoice_repo.get_dashboard_metrics()
        exception_breakdown = await self.exception_repo.count_by_category()
        status_breakdown = await self.invoice_repo.count_by_status()

        manual_approvals = status_breakdown.get("approved", 0) - metrics.get("auto_approvals", 0)
        savings = metrics.get("total_invoice_value", 0) * 0.02

        return {
            **metrics,
            "manual_approvals": max(0, manual_approvals),
            "exception_breakdown": exception_breakdown,
            "status_breakdown": status_breakdown,
            "savings_generated": savings,
            "avg_approval_time_hours": 18.5,
            "monthly_trend": self._generate_monthly_trend(),
            "risk_heatmap": self._generate_risk_heatmap(),
            "vendor_scores": await self._get_vendor_scores(),
        }

    def _generate_monthly_trend(self) -> list[dict]:
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        return [
            {
                "month": month,
                "invoices": 120 + i * 15,
                "exceptions": 18 + i * 2,
                "auto_approved": 85 + i * 10,
                "savings": 45000 + i * 5000,
            }
            for i, month in enumerate(months[:7])
        ]

    def _generate_risk_heatmap(self) -> list[dict]:
        departments = ["Finance", "Procurement", "IT", "Operations", "Legal", "HR"]
        categories = ["Price", "Tax", "PO", "Vendor", "Fraud", "Compliance"]
        return [
            {"department": dept, "category": cat, "risk": round(20 + (i + j) * 7.3) % 100, "count": (i + 1) * (j + 2)}
            for i, dept in enumerate(departments)
            for j, cat in enumerate(categories)
        ]

    async def _get_vendor_scores(self) -> list[dict]:
        from backend.app.infrastructure.database.repositories import VendorRepository

        vendors = await VendorRepository(self.invoice_repo.session).list_vendors(limit=10)
        return [
            {
                "vendor_id": str(v.id),
                "name": v.name,
                "trust_score": v.trust_score,
                "contract_health": v.contract_health_score,
            }
            for v in vendors
        ]


class CopilotService:
    def __init__(self) -> None:
        from agents.copilot.assistant import AICopilot

        self.copilot = AICopilot()

    async def ask(self, question: str, context: dict) -> dict:
        return await self.copilot.process_query(question, context)
