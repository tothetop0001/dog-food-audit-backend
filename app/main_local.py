"""Local development FastAPI application without Docker dependencies."""

import asyncio
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.api import api_router
from app.core.config import get_settings
from app.core.database import init_db
from app.core.logging import configure_logging, get_logger

# Set Windows-specific asyncio policy to prevent event loop issues
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Configure logging
configure_logging()
logger = get_logger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Dog Food API (Local Development)", version=settings.version)
    
    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        logger.info("Please make sure PostgreSQL is running and the database exists")
        logger.info("You can create the database with: createdb dog_food_db")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Dog Food API")
    
    # Ensure all pending tasks are completed
    try:
        # Get all pending tasks
        pending_tasks = [task for task in asyncio.all_tasks() if not task.done()]
        if pending_tasks:
            logger.info(f"Cancelling {len(pending_tasks)} pending tasks")
            for task in pending_tasks:
                task.cancel()
            
            # Wait for tasks to complete cancellation
            await asyncio.gather(*pending_tasks, return_exceptions=True)
    except Exception as e:
        logger.warning(f"Error during shutdown cleanup: {e}")
    
    # Give a moment for cleanup
    await asyncio.sleep(0.1)


# Create FastAPI application
app = FastAPI(
    title=f"{settings.project_name} (Local Dev)",
    version=settings.version,
    description="A FastAPI project for dog food data scraping and REST API - Local Development",
    openapi_url=f"{settings.api_v1_str}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"],  # Configure this properly for production
)

# Include API router
app.include_router(api_router, prefix=settings.api_v1_str)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Dog Food API (Local Development)",
        "version": settings.version,
        "docs_url": "/docs",
        "api_url": settings.api_v1_str,
        "environment": "local_development",
        "database": "postgresql_local",
        "celery": "memory_broker" if getattr(settings, 'use_memory_broker', True) else "redis",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy", 
        "version": settings.version,
        "environment": "local_development",
        "database": "postgresql_local",
    }


@app.get("/setup")
async def setup_info():
    """Setup information endpoint."""
    return {
        "message": "Local development setup information",
        "database_url": settings.database_url,
        "debug_mode": settings.debug,
        "log_level": settings.log_level,
        "instructions": {
            "database": "Make sure PostgreSQL is running and database 'dog_food_db' exists",
            "migrations": "Run 'alembic upgrade head' to apply database migrations",
            "sample_data": "Run 'python scripts/init_db.py' to create sample data",
            "scraping": "Use memory broker (no Redis required) or install Redis for background tasks",
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main_local:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
