"""Celery worker configuration for background tasks."""

import asyncio
from celery import Celery

from ...config.settings import settings

# Create Celery app
celery_app = Celery(
    "assignment_scraper",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "src.infrastructure.celery.tasks"
    ]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    task_routes={
        "src.infrastructure.celery.tasks.execute_scraping_job": {"queue": "scraping"},
        "src.infrastructure.celery.tasks.bulk_scrape_urls": {"queue": "bulk_scraping"},
        "src.infrastructure.celery.tasks.validate_urls": {"queue": "validation"},
    },
    beat_schedule={
        "cleanup-old-jobs": {
            "task": "src.infrastructure.celery.tasks.cleanup_old_jobs",
            "schedule": 3600.0,  # Run every hour
        },
        "health-check": {
            "task": "src.infrastructure.celery.tasks.health_check",
            "schedule": 300.0,  # Run every 5 minutes
        },
    },
)


# Helper function to run async tasks in Celery
def run_async_task(coro):
    """Run async coroutine in Celery task."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


if __name__ == "__main__":
    celery_app.start() 