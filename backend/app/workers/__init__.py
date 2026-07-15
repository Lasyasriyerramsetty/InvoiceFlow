import os
from celery import Celery
from backend.app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "ap_invoice_agent",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["backend.app.workers.invoice_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    task_time_limit=300,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
)

__all__ = ["celery_app"]