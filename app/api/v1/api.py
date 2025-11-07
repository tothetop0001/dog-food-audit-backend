"""API v1 router configuration."""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, products, scraping, score, users

api_router = APIRouter()
api_router.include_router(
    auth.router, prefix="/auth", tags=["authentication"]
)
api_router.include_router(
    users.router, prefix="/users", tags=["user management"]
)
api_router.include_router(
    products.router, prefix="/products", tags=["products"]
)
api_router.include_router(
    scraping.router, prefix="/scraping", tags=["scraping"]
)
api_router.include_router(
    score.router, prefix="/score", tags=["score"]
)
