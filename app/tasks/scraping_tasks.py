"""Background tasks for scraping operations."""

import asyncio
from datetime import datetime

from celery import Celery
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.core.logging import get_logger
from app.services.scraping_service import ScrapingService

settings = get_settings()
logger = get_logger(__name__)

# Initialize Celery
celery_app = Celery(
    "dog_food_api",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.scraping_tasks"],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)


@celery_app.task(bind=True, name="run_scraping_task")
def run_scraping_task(self) -> dict:
    """Celery task to run scraping job."""
    logger.info("Starting scraping task", task_id=self.request.id)
    
    # Update task status to STARTED
    self.update_state(state='STARTED', meta={'message': 'Scraping job started'})
    
    try:
        # Run the async scraping job with proper event loop handling
        loop = None
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Update status to PROGRESS
        self.update_state(state='PROGRESS', meta={'message': 'Running scraping job...'})
        
        if loop.is_running():
            # If loop is already running, create a new one
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _run_scraping_job())
                result = future.result()
        else:
            result = loop.run_until_complete(_run_scraping_job())
        
        # Update status to SUCCESS with results
        self.update_state(
            state='SUCCESS', 
            meta={
                'message': 'Scraping job completed successfully',
                'result': result
            }
        )
        
        loop.close()
        logger.info("Scraping task completed successfully", task_id=self.request.id, result=result)
        return result
        
    except Exception as e:
        logger.error("Scraping task failed", task_id=self.request.id, error=str(e))
        
        # Update status to FAILURE
        self.update_state(
            state='FAILURE',
            meta={
                'message': f'Scraping job failed: {str(e)}',
                'error': str(e)
            }
        )
        
        raise self.retry(exc=e, countdown=60, max_retries=3)
    finally:
        # Ensure proper cleanup
        if loop and not loop.is_closed():
            try:
                loop.close()
            except Exception:
                pass


async def _run_scraping_job() -> dict:
    """Run the actual scraping job."""
    try:
        async with AsyncSessionLocal() as db:
            service = ScrapingService(db)
            results = await service.run_scraping_job()
            return results
    except Exception as e:
        logger.error("Error in scraping job", error=str(e))
        raise


@celery_app.task(name="schedule_scraping_task")
def schedule_scraping_task() -> dict:
    """Schedule the next scraping task."""
    logger.info("Scheduling next scraping task")
    
    # Schedule the next run based on configuration
    interval_hours = settings.scraping_interval_hours
    next_run = datetime.utcnow().replace(
        hour=2, minute=0, second=0, microsecond=0
    )  # Run at 2 AM UTC
    
    # If it's already past 2 AM today, schedule for tomorrow
    if datetime.utcnow().hour >= 2:
        from datetime import timedelta
        next_run += timedelta(days=1)
    
    # Schedule the task
    run_scraping_task.apply_async(eta=next_run)
    
    logger.info("Next scraping task scheduled", next_run=next_run.isoformat())
    
    return {
        "message": "Scraping task scheduled",
        "next_run": next_run.isoformat(),
    }


# Periodic task configuration
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    "daily-scraping": {
        "task": "run_scraping_task",
        "schedule": crontab(hour="*/24", minute=0),  # Run daily at 2 AM UTC
    },
}

celery_app.conf.timezone = "UTC"
