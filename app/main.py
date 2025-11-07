"""Main FastAPI application."""

from contextlib import asynccontextmanager
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.api import api_router
from app.core.config import get_settings
from app.core.database import init_db
from app.core.logging import configure_logging, get_logger

PORT = os.getenv("PORT", 8000)

# Configure logging
configure_logging()
logger = get_logger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Dog Food API", version=settings.version)
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Dog Food API")


# Create FastAPI application
app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    description="A FastAPI project for dog food data scraping and REST API",
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
        "message": "Welcome to Dog Food API",
        "version": settings.version,
        "docs_url": "/docs",
        "api_url": settings.api_v1_str,
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.version}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=PORT,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
