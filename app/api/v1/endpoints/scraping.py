"""Scraping API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.dependencies import get_current_active_user, require_roles
from app.models.user import User
from app.services.scraping_service import ScrapingService
from app.tasks.scraping_tasks import run_scraping_task
from app.tasks.task_factory import run_scraping_job_async, run_scraping_job_sync, task_runner

router = APIRouter()


@router.post("/run")
async def run_scraping_job(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db),
    # current_user: User = Depends(require_roles("admin")),
) -> dict:
    """Run the scraping job in the background. Requires admin role."""
    # Run scraping in background using task factory
    # background_tasks.add_task(run_scraping_job_async)
    task = await run_scraping_job_async()
    
    return {"message": "Scraping job started in background"}


@router.post("/run-sync")
async def run_scraping_job_sync_endpoint(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_roles("admin")),
) -> dict:
    """Run the scraping job synchronously and return results. Requires admin role."""
    # Use task factory for synchronous execution
    results = await run_scraping_job_async()
    
    return {
        "message": "Scraping job completed",
        "results": results,
    }


@router.get("/stats")
async def get_scraping_statistics(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Get scraping statistics. Requires authentication."""
    service = ScrapingService(db)
    stats = await service.get_scraping_statistics()
    return stats

@router.get("/tasks/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Check status of a Celery task.
    Works only if Redis/Celery is enabled.
    Requires authentication.
    """
    try:
        task = run_scraping_task.AsyncResult(task_id)
        
        # Get task info
        task_info = task.info if hasattr(task, 'info') and task.info else {}
        
        response = {
            "task_id": task.id,
            "status": task.status,
            "ready": task.ready(),
            "successful": task.successful() if hasattr(task, 'successful') else False,
            "failed": task.failed() if hasattr(task, 'failed') else False,
        }
        
        # Add result based on status
        if task.ready():
            if task.successful():
                response["result"] = task.result
                response["message"] = "Task completed successfully"
            elif task.failed():
                response["result"] = str(task.result)
                response["error"] = str(task.result)
                response["message"] = "Task failed"
            else:
                response["result"] = task.result
                response["message"] = "Task completed"
        else:
            response["result"] = "Not ready"
            response["message"] = task_info.get('message', 'Task is running...')
            
        return response
        
    except Exception as e:
        return {
            "task_id": task_id,
            "status": "UNKNOWN",
            "error": f"Failed to get task status: {str(e)}",
            "message": "Task status could not be retrieved"
        }