"""Categories API endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.schemas.dog_food import DogFoodCategoryCreate, DogFoodCategoryResponse
from app.services.dog_food_service import DogFoodService

router = APIRouter()


@router.get("/", response_model=List[DogFoodCategoryResponse])
async def get_categories(
    db: AsyncSession = Depends(get_async_db),
) -> List[DogFoodCategoryResponse]:
    """Get all dog food categories."""
    service = DogFoodService(db)
    categories = await service.get_categories()
    return categories


@router.get("/{category_id}", response_model=DogFoodCategoryResponse)
async def get_category(
    category_id: int,
    db: AsyncSession = Depends(get_async_db),
) -> DogFoodCategoryResponse:
    """Get a specific category by ID."""
    service = DogFoodService(db)
    category = await service.get_category_by_id(category_id)
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return category


@router.post("/", response_model=DogFoodCategoryResponse)
async def create_category(
    category_data: DogFoodCategoryCreate,
    db: AsyncSession = Depends(get_async_db),
) -> DogFoodCategoryResponse:
    """Create a new dog food category."""
    service = DogFoodService(db)
    category = await service.create_category(category_data)
    return category
