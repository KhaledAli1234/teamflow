from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "teamflow",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.modules.auth.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    broker_connection_retry_on_startup=True,
)