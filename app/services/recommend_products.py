"""Product recommendation service."""

from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from app.models.dog_food import Product
from app.services.scoring_system_service import ScoringSystemService
from app.core.logging import LoggerMixin


class ProductRecommendationService(LoggerMixin):
    """Service for recommending top-scoring products."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize the service with database session."""
        self.db = db
        self.scoring_service = ScoringSystemService(db)

    async def get_top_products(
        self, 
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Get top-scoring products with their scores."""
        
        # Get Dry Food products
        raw_food_result = await self.db.execute(
            select(Product)
            .options(
                selectinload(Product.ingredient_quality),
                selectinload(Product.guaranteed_analysis)
            )
            .where(Product.category == "Raw Food")
        )
        raw_food_products = raw_food_result.scalars().all()
        
        # Get Fresh Food products
        fresh_food_result = await self.db.execute(
            select(Product)
            .options(
                selectinload(Product.ingredient_quality),
                selectinload(Product.guaranteed_analysis)
            )
            .where(Product.category == "Fresh Food")
        )
        fresh_food_products = fresh_food_result.scalars().all()
        
        if not raw_food_products and not fresh_food_products:
            self.logger.warning("No products found in database")
            return []
        
        # Calculate scores for all products
        product_scores = []
        
        # Process Dry Food products
        for product in raw_food_products:
            try:
                # Calculate score for this product
                score_data = await self.scoring_service.get_score(
                    add_topper=False,
                    pet_name="",
                    breed="",
                    year="",
                    month="",
                    weight="",
                    product=product.product_name,
                    storage="",
                    packaging_size="",
                    shelf_life="",
                    topper="",
                    topper_storage="",
                    topper_packaging_size="",
                    topper_shelf_life=""
                )
                
                # Extract score and classification
                score = score_data.get("score", 0)
                classification = score_data.get("classfication", "Unknown")
                
                product_scores.append({
                    "id": product.id,
                    "brand": product.brand,
                    "product_name": product.product_name,
                    "category": product.category,
                    "flavors": product.flavors,
                    "image_url": product.image_url,
                    "product_url": product.product_url,
                    "processing": product.processing_method if product.processing_method else "Uncooked (Not Frozen)",
                    "score": score,
                    "classification": classification
                })
                
            except Exception as e:
                self.logger.error(f"Error calculating score for product {product.product_name}: {e}")
                # Add product with zero score if calculation fails
                product_scores.append({
                    "id": product.id,
                    "brand": product.brand,
                    "product_name": product.product_name,
                    "category": product.category,
                    "flavors": product.flavors,
                    "image_url": product.image_url,
                    "product_url": product.product_url,
                    "processing": product.processing_method if product.processing_method else "Uncooked (Not Frozen)",
                    "score": 0,
                    "classification": "Error"
                })
        
        # Process Fresh Food products
        for product in fresh_food_products:
            try:
                # Calculate score for this product
                score_data = await self.scoring_service.get_score(
                    add_topper=False,
                    pet_name="",
                    breed="",
                    year="",
                    month="",
                    weight="",
                    product=product.product_name,
                    storage="",
                    packaging_size="",
                    shelf_life="",
                    topper="",
                    topper_storage="",
                    topper_packaging_size="",
                    topper_shelf_life=""
                )
                
                # Extract score and classification
                score = score_data.get("score", 0)
                classification = score_data.get("classfication", "Unknown")
                
                product_scores.append({
                    "id": product.id,
                    "brand": product.brand,
                    "product_name": product.product_name,
                    "category": product.category,
                    "flavors": product.flavors,
                    "image_url": product.image_url,
                    "product_url": product.product_url,
                    "processing": product.processing_method if product.processing_method else "Uncooked (Not Frozen)",
                    "score": score,
                    "classification": classification
                })
                
            except Exception as e:
                self.logger.error(f"Error calculating score for product {product.product_name}: {e}")
                # Add product with zero score if calculation fails
                product_scores.append({
                    "id": product.id,
                    "brand": product.brand,
                    "product_name": product.product_name,
                    "category": product.category,
                    "flavors": product.flavors,
                    "image_url": product.image_url,
                    "product_url": product.product_url,
                    "processing": product.processing_method if product.processing_method else "Uncooked (Not Frozen)",
                    "score": 0,
                    "classification": "Error"
                })
        
        # Sort by score (highest first)
        product_scores.sort(key=lambda x: x["score"], reverse=True)
        
        # Get 5 Raw Food + 5 Fresh Food, then sort by score
        raw_food_results = [p for p in product_scores if p["category"] == "Raw Food"][:5]
        fresh_food_results = [p for p in product_scores if p["category"] == "Fresh Food"][:5]
        
        # Combine and sort by score (highest first)
        combined_results = raw_food_results + fresh_food_results
        combined_results.sort(key=lambda x: x["score"], reverse=True)
        
        return combined_results
