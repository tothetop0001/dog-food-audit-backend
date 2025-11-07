"""Dog food service for business logic."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import LoggerMixin
from app.models.dog_food import Product
from app.schemas.dog_food import ProductCreate


class DogFoodService(LoggerMixin):
    """Service class for dog food business logic."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize the service with database session."""
        self.db = db

    async def create_product(self, product_data: ProductCreate) -> Product:
        """Create a new dog food product."""
        self.logger.info("Creating product", name=product_data.product_name)
        
        # Check if product already exists
        existing_product = await self.get_product_by_name(product_data.product_name)
        if existing_product:
            self.logger.info("Product already exists", name=product_data.product_name)
            return existing_product
        
        product = Product(**product_data.model_dump())
        self.db.add(product)
        await self.db.commit()
        await self.db.refresh(product)
        
        self.logger.info("Product created successfully", product_id=product.id, name=product.product_name)
        return product

    async def get_product_by_name(self, name: str) -> Optional[Product]:
        """Get product by name."""
        result = await self.db.execute(
            select(Product).where(Product.product_name == name)
        )
        return result.scalar_one_or_none()

    async def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Get product by ID."""
        result = await self.db.execute(
            select(Product).where(Product.id == product_id)
        )
        return result.scalar_one_or_none()

    async def get_products(self) -> List[Product]:
        """Get all products."""
        result = await self.db.execute(
            select(Product).order_by(Product.product_name)
        )
        return list(result.scalars().all())