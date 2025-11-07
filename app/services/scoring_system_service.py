from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import LoggerMixin
from app.models.dog_food import Product, IngredientQuality, GuaranteedAnalysis
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.services.food_scoring_engine import DogFoodScorer

class ScoringSystemService(LoggerMixin):
    """Service class for scoring system."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize the service with database session."""
        self.db = db
        self.scorer = DogFoodScorer()

    def _safe_float_conversion(self, value: str, default: float = 0.0) -> float:
        """Safely convert string to float with default value."""
        if not value or value.strip() == "":
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    async def get_score(self, add_topper: bool, pet_name: str, breed: str, year: str, month: str, weight: str, product: str, storage: str, packaging_size: str, topper: str, shelf_life: str, topper_storage: str, topper_packaging_size: str, topper_shelf_life: str) -> float:
        """Get the score."""
        base_product_result = await self.db.execute(
            select(Product)
            .options(
                selectinload(Product.ingredient_quality),
                selectinload(Product.guaranteed_analysis)
            )
            .where(Product.product_name == product)
        )

        base_products = base_product_result.scalars().all()
        
        if not base_products:
            self.logger.error("Base product not found", product=product)
            return 0
        
        if len(base_products) > 1:
            self.logger.warning(f"Multiple products found with name '{product}', using the first one", 
                              product=product, count=len(base_products))
        
        base_product = base_products[0]  # Use the first match

        # Get topper product if provided
        topper_product = None
        if add_topper:
            topper_result = await self.db.execute(
                select(Product)
                .options(
                    selectinload(Product.ingredient_quality),
                    selectinload(Product.guaranteed_analysis)
                )
                .where(Product.product_name == topper)
            )
            topper_products = topper_result.scalars().all()
            
            if topper_products:
                if len(topper_products) > 1:
                    self.logger.warning(f"Multiple topper products found with name '{topper}', using the first one", 
                                      topper=topper, count=len(topper_products))
                topper_product = topper_products[0]

        food_type = base_product.category
        if not food_type:
            food_type = ""
        base_processing = base_product.processing_method
        if not base_processing:
            base_processing = ""
        if topper_product:
            topper_processing = topper_product.processing_method
        else:
            topper_processing = ""
        sourcing = base_product.sourcing
        if not sourcing:
            sourcing = ""
        synthetic = base_product.synthetic
        if not synthetic:
            synthetic = 0
        longevity = base_product.longevity
        if not longevity:
            longevity = 0
        # Safely convert guaranteed analysis values to float with defaults
        protein = self._safe_float_conversion(base_product.guaranteed_analysis.protein, 0.0)
        fat = self._safe_float_conversion(base_product.guaranteed_analysis.fat, 0.0)
        fiber = self._safe_float_conversion(base_product.guaranteed_analysis.fiber, 0.0)
        moisture = self._safe_float_conversion(base_product.guaranteed_analysis.moisture, 0.0)
        ash = self._safe_float_conversion(base_product.guaranteed_analysis.ash, 6.0)  # Default ash is 6.0
        protein_quality = base_product.ingredient_quality.protein
        fat_quality = base_product.ingredient_quality.fat
        fiber_quality = base_product.ingredient_quality.fiber
        carbohydrate_quality = base_product.ingredient_quality.carbohydrate
        # Safely calculate dirty dozen count
        dirty_dozen_str = base_product.ingredient_quality.dirty_dozen or ""
        dirty_dozen = len(dirty_dozen_str.split(",")) if dirty_dozen_str.strip() else 0
        if(base_product.nutritionally_adequate == "Yes"):
            base_adequate = True
        else:
            base_adequate = False
        if topper_product:
            if(topper_product.nutritionally_adequate == "Yes"):
                topper_adequate = True
            else:
                topper_adequate = False
        else:
            topper_adequate = None

        #--------------------------
        # Start scoring system
        #--------------------------

        carb_percent = self.scorer.calculate_carb_percent(protein, fat, fiber, ash, moisture, food_type)
        food_deduction = self.scorer.food_deduction(food_type)
        sourcing_deduction = self.scorer.sourcing_deduction(sourcing)
        processing_deduction = self.scorer.processing_base_topper(base_processing, topper_processing)
        adequacy_deduction = self.scorer.adequacy_deduction(base_adequate)
        carb_deduction = self.scorer.carb_deduction(carb_percent)
        ingredient_quality_protein = self.scorer.ingredient_quality_protein_deduction(protein_quality.lower())
        ingredient_quality_fat = self.scorer.ingredient_quality_fat_deduction(fat_quality.lower())
        ingredient_quality_fiber = self.scorer.ingredient_quality_fiber_deduction(fiber_quality.lower())
        ingredient_quality_carbohydrate = self.scorer.ingredient_quality_carbohydrate_deduction(carbohydrate_quality.lower())
        dirty_dozen_deduction = self.scorer.dirty_dozen_deduction(dirty_dozen)
        synthetic_deduction = self.scorer.synthetic_deduction(synthetic)
        longevity_deduction = self.scorer.longevity_deduction(longevity)
        storage_deduction = self.scorer.storage_deduction(storage, topper_storage)
        packaging_deduction = self.scorer.packaging_deduction(packaging_size, topper_packaging_size)
        shelf_life_deduction = self.scorer.shelf_life_deduction(shelf_life, topper_shelf_life)

        deductions = [
            food_deduction["deduction"],
            sourcing_deduction["deduction"],
            processing_deduction["deduction"],
            adequacy_deduction["deduction"],
            carb_deduction["deduction"],
            ingredient_quality_protein["deduction"],
            ingredient_quality_fat["deduction"],
            ingredient_quality_fiber["deduction"],
            ingredient_quality_carbohydrate["deduction"],
            dirty_dozen_deduction["deduction"],
            synthetic_deduction["deduction"],
            longevity_deduction["deduction"],
            storage_deduction["deduction"],
            packaging_deduction["deduction"],
            shelf_life_deduction["deduction"],
        ]

        final_score = self.scorer.calculate_score(deductions)


        return {
            "score": final_score,
            "classfication": self.scorer.classify_score(final_score),
            "deductions": deductions,
            "carb_percent": carb_percent,
            "micro_score": {
                "food": {"grade": food_deduction["grade"], "score": int(food_deduction["score"])},
                "sourcing": {"grade": sourcing_deduction["grade"], "score": int(sourcing_deduction["score"])},
                "processing": {"grade": processing_deduction["grade"], "score": int(processing_deduction["score"])},
                "adequacy": {"grade": adequacy_deduction["grade"], "score": int(adequacy_deduction["score"])},
                "carb": {"grade": carb_deduction["grade"], "score": int(carb_deduction["score"])},
                "ingredient_quality_protein": {"grade": ingredient_quality_protein["grade"], "score": int(ingredient_quality_protein["score"])},
                "ingredient_quality_fat": {"grade": ingredient_quality_fat["grade"], "score": int(ingredient_quality_fat["score"])},
                "ingredient_quality_fiber": {"grade": ingredient_quality_fiber["grade"], "score": int(ingredient_quality_fiber["score"])},
                "ingredient_quality_carbohydrate": {"grade": ingredient_quality_carbohydrate["grade"], "score": int(ingredient_quality_carbohydrate["score"])},
                "dirty_dozen": {"grade": dirty_dozen_deduction["grade"], "score": int(dirty_dozen_deduction["score"])},
                "synthetic": {"grade": synthetic_deduction["grade"], "score": int(synthetic_deduction["score"])},
                "longevity": {"grade": longevity_deduction["grade"], "score": int(longevity_deduction["score"])},
                "storage": {"grade": storage_deduction["grade"], "score": int(storage_deduction["score"])},
                "packaging": {"grade": packaging_deduction["grade"], "score": int(packaging_deduction["score"])},
                "shelf_life": {"grade": shelf_life_deduction["grade"], "score": int(shelf_life_deduction["score"])},
            }
        }