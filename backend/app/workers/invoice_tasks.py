import uuid
from decimal import Decimal

from celery import shared_task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.orchestrator.pipeline import InvoiceProcessingPipeline
from backend.app.infrastructure.database.models import Invoice, InvoiceStatus
from backend.app.infrastructure.database.session import AsyncSessionLocal, engine
from backend.app.infrastructure.storage.minio_storage import ObjectStorageService


@shared_task(bind=True, name="process_invoice_document")
def process_invoice_document(
    self,
    invoice_id: str,
    document_path: str,
) -> dict:
    """Background task for processing invoice documents."""
    import asyncio

    return asyncio.run(_process_invoice_async(invoice_id, document_path))


async def _process_invoice_async(invoice_id: str, document_path: str) -> dict:
    """Async processing logic."""
    async with AsyncSessionLocal() as session:
        invoice = await session.get(Invoice, uuid.UUID(invoice_id))
        if not invoice:
            return {"error": "Invoice not found", "invoice_id": invoice_id}

        storage = ObjectStorageService()
        document_bytes = storage.download_file(document_path)

        pipeline = InvoiceProcessingPipeline()
        result = await pipeline.run(
            invoice_id=invoice_id,
            document_bytes=document_bytes,
            filename=document_path,
        )

        invoice.status = InvoiceStatus.PENDING_APPROVAL if result.exceptions else InvoiceStatus.APPROVED
        invoice.processing_time_ms = result.processing_time_ms
        invoice.extracted_data_json = result.extracted_invoice
        invoice.risk_score = result.risk_score.overall_score if result.risk_score else 0
        invoice.fraud_score = result.fraud_assessment.fraud_confidence * 100 if result.fraud_assessment else 0

        await session.commit()

        return {
            "invoice_id": invoice_id,
            "status": invoice.status.value,
            "processing_time_ms": result.processing_time_ms,
            "exceptions_count": len(result.exceptions),
        }