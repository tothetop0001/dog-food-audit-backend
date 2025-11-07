"""Task factory for handling different task runners based on environment."""

import os
from typing import Dict, Any, Callable
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


def get_task_runner():
    """Get the appropriate task runner based on environment."""
    # Check if we're in a production environment
    # Production environments typically have Redis available
    redis_available = _is_redis_available()
    
    if redis_available:
        logger.info("Using Celery task runner for production environment")
        return _get_celery_task_runner()
    else:
        logger.info("Using local task runner for development environment")
        return _get_local_task_runner()


def _is_redis_available() -> bool:
    """Check if Redis is available."""
    try:
        import redis
        r = redis.from_url(settings.redis_url)
        r.ping()
        return True
    except Exception as e:
        logger.debug("Redis not available, falling back to local task runner", error=str(e))
        return False


def _get_celery_task_runner():
    """Get Celery task runner for production."""
    try:
        from app.tasks.scraping_tasks import run_scraping_task
        
        async def run_scraping_job_async() -> Dict[str, Any]:
            """Run scraping job using Celery."""
            # For background tasks, we can use Celery's delay method
            # For sync tasks, we need to run it directly
            task = run_scraping_task.delay()
            # return task.get()  # This will block until completion
            return task
        
        def run_scraping_job_sync() -> Dict[str, Any]:
            """Run scraping job synchronously using Celery."""
            task = run_scraping_task.delay()
            return task.get()
        
        return {
            'async': run_scraping_job_async,
            'sync': run_scraping_job_sync
        }
    except ImportError as e:
        logger.error("Failed to import Celery task runner, falling back to local", error=str(e))
        # Fall back to local task runner if Celery is not available
        return _get_local_task_runner()
    except Exception as e:
        logger.error("Failed to initialize Celery task runner, falling back to local", error=str(e))
        return _get_local_task_runner()


def _get_local_task_runner():
    """Get local task runner for development."""
    try:
        from app.tasks.local_tasks import run_scraping_job_local, run_scraping_task_local
        
        async def run_scraping_job_async() -> Dict[str, Any]:
            """Run scraping job using local task runner."""
            try:
                return await run_scraping_job_local()
            except Exception as e:
                logger.error("Local scraping job failed", error=str(e))
                return {"message": "Scraping failed", "error": str(e)}
        
        def run_scraping_job_sync() -> Dict[str, Any]:
            """Run scraping job synchronously using local task runner."""
            try:
                return run_scraping_task_local()
            except Exception as e:
                logger.error("Local scraping job failed", error=str(e))
                return {"message": "Scraping failed", "error": str(e)}
        
        return {
            'async': run_scraping_job_async,
            'sync': run_scraping_job_sync
        }
    except ImportError as e:
        logger.error("Failed to import local task runner", error=str(e))
        # If local tasks are not available, create a minimal fallback
        async def run_scraping_job_async() -> Dict[str, Any]:
            """Fallback scraping job."""
            logger.warning("Using fallback scraping job - no task runner available")
            return {"message": "Scraping not available", "error": "No task runner configured"}
        
        def run_scraping_job_sync() -> Dict[str, Any]:
            """Fallback scraping job."""
            logger.warning("Using fallback scraping job - no task runner available")
            return {"message": "Scraping not available", "error": "No task runner configured"}
        
        return {
            'async': run_scraping_job_async,
            'sync': run_scraping_job_sync
        }


# Get the task runner instance
task_runner = get_task_runner()

# Export the functions for use in endpoints
run_scraping_job_async = task_runner['async']
run_scraping_job_sync = task_runner['sync']
