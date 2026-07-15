import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.dependencies import require_permission
from backend.app.api.v1.schemas import (
    CopilotRequest,
    CopilotResponse,
    DashboardKPIs,
    ExceptionResponse,
    InvoiceResponse,
    ProcessingResultResponse,
)
from backend.app.application.services.invoice_service import CopilotService, DashboardService, InvoiceProcessingService
from backend.app.infrastructure.database.models import Invoice, InvoiceStatus, User, Vendor
from backend.app.infrastructure.database.repositories import ExceptionRepository, InvoiceRepository, VendorRepository
from backend.app.infrastructure.database.session import get_db_session
from backend.app.infrastructure.storage.minio_storage import ObjectStorageService

router = APIRouter(tags=["Invoices"])


@router.post("/invoices/upload", response_model=ProcessingResultResponse)
async def upload_invoice(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    file: UploadFile = File(...),  # No auth required for testing
):
    """Upload and process invoice. Public endpoint for testing."""
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    storage = ObjectStorageService()
    path = storage.upload_file(content, file.filename or "invoice.pdf", file.content_type or "application/pdf")

    vendor_repo = VendorRepository(session)
    vendor = await vendor_repo.get_by_name("Global Tech Solutions")
    if not vendor:
        vendor = await vendor_repo.create(
            Vendor(vendor_code="VND-001", name="Global Tech Solutions", trust_score=95.0, country="US", currency="USD")
        )

    invoice = Invoice(
        invoice_number=f"INV-{uuid.uuid4().hex[:8].upper()}",
        vendor_id=vendor.id,
        status=InvoiceStatus.RECEIVED,
        document_path=path,
        currency="USD",
    )
    invoice = await InvoiceRepository(session).create(invoice)

    service = InvoiceProcessingService(session)
    result = await service.process_invoice(invoice.id, content, file.filename or "invoice.pdf")

    return ProcessingResultResponse(
        pipeline_id=result.pipeline_id,
        invoice_id=str(invoice.id),
        status=result.status,
        processing_time_ms=result.processing_time_ms,
        exceptions_count=len(result.exceptions),
        risk_score=result.risk_score.overall_score if result.risk_score else None,
        recommendation=result.recommendation.summary if result.recommendation else None,
        agent_insights_count=len(result.agent_insights),
    )


@router.get("/invoices", response_model=list[InvoiceResponse])
async def list_invoices(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    skip: int = 0,
    limit: int = 50,
    status_filter: str | None = None,
):
    repo = InvoiceRepository(session)
    invoice_status = InvoiceStatus(status_filter) if status_filter else None
    invoices = await repo.list_invoices(skip=skip, limit=limit, status=invoice_status)
    return [
        InvoiceResponse(
            id=inv.id,
            invoice_number=inv.invoice_number,
            vendor_name=inv.vendor.name if inv.vendor else None,
            status=inv.status.value,
            total_amount=float(inv.total_amount),
            currency=inv.currency,
            risk_score=inv.risk_score,
            fraud_score=inv.fraud_score,
            health_score=inv.health_score,
            auto_approved=inv.auto_approved,
            ai_summary=inv.ai_summary,
            created_at=inv.created_at,
        )
        for inv in invoices
    ]


@router.get("/invoices/{invoice_id}")
async def get_invoice(
    invoice_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    invoice = await InvoiceRepository(session).get_by_id(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return {
        "id": str(invoice.id),
        "invoice_number": invoice.invoice_number,
        "vendor": {"id": str(invoice.vendor.id), "name": invoice.vendor.name} if invoice.vendor else None,
        "status": invoice.status.value,
        "total_amount": float(invoice.total_amount),
        "currency": invoice.currency,
        "risk_score": invoice.risk_score,
        "fraud_score": invoice.fraud_score,
        "health_score": invoice.health_score,
        "compliance_score": invoice.compliance_score,
        "auto_approved": invoice.auto_approved,
        "ai_summary": invoice.ai_summary,
        "extracted_data": invoice.extracted_data_json,
        "exceptions": [
            {
                "id": str(e.id),
                "category": e.category,
                "severity": e.severity,
                "title": e.title,
                "reasoning": e.reasoning,
                "confidence": e.confidence,
                "suggested_resolution": e.suggested_resolution,
                "financial_impact": float(e.financial_impact),
            }
            for e in invoice.exceptions
        ],
        "agent_insights": [
            {
                "agent": i.agent_name,
                "reasoning": i.reasoning,
                "confidence": i.confidence,
            }
            for i in invoice.agent_insights
        ],
        "approvals": [
            {
                "role": a.approver_role,
                "department": a.department,
                "status": a.status,
                "reason": a.reason,
            }
            for a in invoice.approvals
        ],
    }


@router.get("/exceptions", response_model=list[ExceptionResponse])
async def list_exceptions(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    limit: int = 50,
):
    exceptions = await ExceptionRepository(session).list_open(limit=limit)
    return [
        ExceptionResponse(
            id=e.id,
            category=e.category,
            severity=e.severity,
            title=e.title,
            description=e.description,
            reasoning=e.reasoning,
            confidence=e.confidence,
            suggested_resolution=e.suggested_resolution,
            financial_impact=float(e.financial_impact),
            status=e.status.value,
        )
        for e in exceptions
    ]


@router.post("/copilot/ask", response_model=CopilotResponse)
async def ask_copilot(
    request: CopilotRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    context = dict(request.context)
    if request.invoice_id:
        invoice = await InvoiceRepository(session).get_by_id(request.invoice_id)
        if invoice:
            context["invoice"] = {
                "id": str(invoice.id),
                "status": invoice.status.value,
                "risk_score": invoice.risk_score,
                "ai_summary": invoice.ai_summary,
                "extracted_data_json": invoice.extracted_data_json,
            }
            context["exceptions"] = [
                {"reasoning": e.reasoning, "description": e.description} for e in invoice.exceptions
            ]

    result = await CopilotService().ask(request.question, context)
    return CopilotResponse(
        answer=result.get("answer", ""),
        intent=result.get("intent", "general"),
        confidence=result.get("confidence", 0.7),
        evidence=result.get("evidence", []),
        citations=result.get("citations", []),
    )