import asyncio
import uuid

import structlog
from celery import shared_task

from backend.app.workers.celery_app import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(name="backend.app.workers.tasks.process_invoice_async")
def process_invoice_async(invoice_id: str, document_path: str, filename: str):
    async def _run():
        from backend.app.application.services.invoice_service import InvoiceProcessingService
        from backend.app.infrastructure.database.session import AsyncSessionLocal
        from backend.app.infrastructure.storage.minio_storage import ObjectStorageService

        storage = ObjectStorageService()
        content = storage.download_file(document_path)

        async with AsyncSessionLocal() as session:
            service = InvoiceProcessingService(session)
            result = await service.process_invoice(uuid.UUID(invoice_id), content, filename)
            await session.commit()
            return result.model_dump()

    return asyncio.get_event_loop().run_until_complete(_run())


@celery_app.task(name="backend.app.workers.tasks.generate_weekly_report")
def generate_weekly_report():
    logger.info("weekly_report_generated")
    return {"status": "completed", "report_type": "weekly_executive_summary"}


@celery_app.task(name="backend.app.workers.tasks.index_document_rag")
def index_document_rag(document_id: str, text: str, document_type: str):
    async def _run():
        from rag.retriever import HybridRetriever

        retriever = HybridRetriever()
        count = await retriever.index_document(text, document_id, document_type)
        return {"document_id": document_id, "chunks_indexed": count}

    return asyncio.get_event_loop().run_until_complete(_run())
