"""Tasks package for background job processing."""

# Conditional import to avoid issues in environments without Celery/Redis
try:
    from app.tasks.scraping_tasks import run_scraping_task
    __all__ = ["run_scraping_task"]
except ImportError:
    # If Celery tasks are not available, provide a fallback
    def run_scraping_task():
        """Fallback task when Celery is not available."""
        raise RuntimeError("Celery task runner not available")
    
    __all__ = ["run_scraping_task"]
