"""Products API endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.dependencies import get_current_active_user, require_roles
from app.models.user import User
from app.schemas.dog_food import ProductCreate, ProductResponse
from app.services.dog_food_service import DogFoodService

router = APIRouter()


@router.get("/", response_model=List[ProductResponse])
async def get_products(
    db: AsyncSession = Depends(get_async_db),
) -> List[ProductResponse]:
    """Get all dog food products. Requires authentication."""
    service = DogFoodService(db)

    products = await service.get_products()
    return products


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_async_db),
) -> ProductResponse:
    """Get a specific product by ID. Requires authentication."""
    service = DogFoodService(db)
    product = await service.get_product_by_id(product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return product


@router.post("/", response_model=ProductResponse)
async def create_product(
    product_data: ProductCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_roles("admin")),
) -> ProductResponse:
    """Create a new dog food product. Requires admin role."""
    service = DogFoodService(db)
    product = await service.create_product(product_data)
    return product
