from celery import Celery
from app.config import settings

# Initialize Celery app
celery_app = Celery(
    "talanta_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.ocr_tasks",
        "app.tasks.scraper_tasks",
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Africa/Nairobi",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max
    task_soft_time_limit=25 * 60,
)

# Periodic tasks (Celery Beat schedule)
celery_app.conf.beat_schedule = {
    "scrape-jobs-every-6-hours": {
        "task": "app.tasks.scraper_tasks.scrape_jobs",
        "schedule": 6 * 60 * 60,  # 6 hours in seconds
    },
}

if __name__ == "__main__":
    celery_app.start()
