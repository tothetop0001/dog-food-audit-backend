"""Scraping service for managing data collection."""

from datetime import datetime
import json, asyncio
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import LoggerMixin
from app.models.dog_food import IngredientQuality, GuaranteedAnalysis, Product
from app.schemas.dog_food import IngredientQualityCreate, GuaranteedAnalysisCreate, ProductCreate
from app.scrapers.dog_food_scraper import DogFoodScraper
from app.services.guaranteed_detection_service import infer_guaranteed_analysis
from app.services.ingredient_classification_service import classify_ingredient_list
from app.services.nutritional_detection_service import infer_nutritionally_adequate
from app.services.processing_detection_service import infer_processing_method
from app.services.category_classification_service import infer_category
from app.scrapers.chewy_scraper import ChewyScraper
from app.scrapers.chewy_playwright_rotating import ChewyPlaywrightScraper
from app.services.sourcing_detection_service import infer_sourcing


class ScrapingService(LoggerMixin):
    """Service class for managing scraping operations."""

    def __init__(self, db: AsyncSession()) -> None:
        """Initialize the service with database session."""
        self.db = db
        self.scraper = DogFoodScraper(api_key="04b51035-2d23-44c0-8a90-24cfb715cc79")
        self.chewy_scraper = ChewyScraper()
        self.chewy_playwright_scraper = ChewyPlaywrightScraper()

    async def run_scraping_job(self) -> Dict[str, int]:
        """Run the complete scraping job."""
        self.logger.info("Starting scraping job")

        # Initialize results tracking
        results = {
            "processed": 0,
            "errors": 0,
            "created": 0,
            "updated": 0
        }

        results_tmp = await self.chewy_playwright_scraper.scrape()
        print("results_tmp", results_tmp)

        # Check if scraper returned valid data
        if not results_tmp:
            self.logger.error("Scraper returned None or empty results")
            return results

        try:

            scraped_items = []
            
            for result_tmp in results_tmp:
                try:
                    print("result_tmp", result_tmp)
                    processing_method = infer_processing_method("Made in the USA with global ingredients you can trust.High-quality protein supports your furbaby's lean muscles.Omega-6 fatty acids and vitamin E support your best friend's skin and coat health.The kibble size is perfect for dogs who prefer a smaller kibble.This recipe is made with tasty, natural ingredients.")
                    processing_method = infer_processing_method(result_tmp["product_name"])
                    if processing_method["method"] == None or processing_method["method"] == "":
                        processing_method = infer_processing_method(result_tmp["description"])
                        if processing_method["method"] == None or processing_method["method"] == "":
                            processing_method = infer_processing_method(result_tmp["feeding_guidelines"])

                    # # Safely get ingredients and split
                    ingredients: str = result_tmp["ingredients"]
                    if ingredients and ingredients != '':
                        classified_ingredients = classify_ingredient_list(ingredients.split(", "))
                    else:
                        classified_ingredients = {"protein": "", "fat": "", "fiber": "", "carbohydrate": ""}

                    sourcing = infer_sourcing(result_tmp["description"])
                    if sourcing["sourcing"] == None or sourcing["sourcing"] == "":
                        sourcing = infer_sourcing(result_tmp["feeding_guidelines"])

                    # Safely get guaranteed analysis
                    guaranteed_analysis = result_tmp["guaranteed_analysis"]
                    dirty_dozen = guaranteed_analysis["dirty_dozen"]
                    
                    # Safely get product name and classify category
                    product_name = result_tmp["product_name"]
                    category = infer_category(product_name)
                    
                    # Safely get description for nutritional adequacy
                    description = result_tmp["description"]
                    
                    scraped_items.append({
                        "brand": result_tmp["brand"],
                        "productName": product_name,
                        "category": result_tmp["food_category"],
                        # "category": categories,
                        "category": result_tmp["food_category"].split(",")[0] if result_tmp["food_category"] else category.get("category", "Unknown"),
                        "synthetic": result_tmp["synthetic"] if result_tmp["synthetic"] else 0,
                        "longevity": result_tmp["longevity"] if result_tmp["longevity"] else 0,
                        "flavors": result_tmp["flavors"],
                        "nutritionallyAdequate": infer_nutritionally_adequate(description) if description else "Unknown",
                        "processingMethod": processing_method.get("method", "Unknown"),
                        "ingredients": ingredients,
                        "guaranteedAnalysis": guaranteed_analysis,
                        "classifiedIngredients": classified_ingredients,
                        "dirtyDozen": dirty_dozen,
                        "foodStorage": result_tmp["food_storage"],
                        "sourcing": sourcing.get("sourcing", "Unknown"),
                        "packagingSize": result_tmp["packaging_size"],
                        "numServings": result_tmp["num_servings"],
                        "containerWeight": result_tmp["container_weight"],
                        "servingSize": result_tmp["serving_size"],
                        "feedingGuideline": result_tmp["feeding_guidelines"],
                        "description": description,
                        "productUrl": result_tmp["product_url"],
                        "imageUrl": result_tmp["image_url"],
                    })
                    
                except Exception as e:
                    self.logger.error("Error processing scraped item", error=str(e))
                    results["errors"] += 1
                    continue
            
            # Process each scraped item
            for item_data in scraped_items:
                try:
                    # Start a new transaction for each item
                    async with self.db.begin():
                        ingredient_quality, guaranteed_analysis, product = await self._process_scraped_item(item_data)
                        if ingredient_quality and guaranteed_analysis and product:
                            results["processed"] += 1
                            results["created"] += 1
                        else:
                            results["errors"] += 1
                except Exception as e:
                    self.logger.error("Error processing item", error=str(e))
                    results["errors"] += 1
                    # Rollback is automatic with begin() context manager

        except asyncio.TimeoutError:
            self.logger.error("Scraping job timed out")
            results["errors"] += 1
        except Exception as e:
            self.logger.error("Scraping job failed", error=str(e))
            results["errors"] += 1

        self.logger.info("Scraping job completed", **results)
        return results

    async def _process_scraped_item(self, item_data: Dict) -> tuple:
        """Process a single scraped item and return the created objects."""
        try:
            # Set or create ingredient quality
            ingredient_quality = await self._set_or_create_ingredient_quality(
                item_data["classifiedIngredients"], 
                item_data["dirtyDozen"]
            )
            if not ingredient_quality:
                self.logger.error("Failed to create ingredient quality")
                return None, None, None

            # Set or create guaranteed analysis
            guaranteed_analysis = await self._set_or_create_guaranteed_analysis(
                item_data["guaranteedAnalysis"]
            )
            if not guaranteed_analysis:
                self.logger.error("Failed to create guaranteed analysis")
                return None, None, None
            
            # Set or create product
            product = await self._set_or_create_product(
                item_data, 
                guaranteed_analysis.id, 
                ingredient_quality.id
            )
            if not product:
                self.logger.error("Failed to create product")
                return None, None, None

            return ingredient_quality, guaranteed_analysis, product
            
        except Exception as e:
            self.logger.error("Error processing scraped item", error=str(e))
            return None, None, None
        
    async def _set_or_create_ingredient_quality(self, classified_ingredients: json, dirty_dozen: str) -> Optional[IngredientQuality]:
        """Set or update or create ingredient quality."""
        try:
            if not classified_ingredients or classified_ingredients == {}:
                self.logger.warning("Invalid classified ingredients data")
                return None

            if classified_ingredients['protein'] == "Unknown":
                protein = ""
            else:
                protein = classified_ingredients['protein']

            if classified_ingredients['fat'] == "Unknown":
                fat = ""
            else:
                fat = classified_ingredients['fat']

            if classified_ingredients['fiber'] == "Unknown":
                fiber = ""
            else:
                fiber = classified_ingredients['fiber']

            if classified_ingredients['carbohydrate'] == "Unknown":
                carbohydrate = ""
            else:
                carbohydrate = classified_ingredients['carbohydrate']

            # Try to find existing ingredient quality
            self.logger.debug("Looking for existing ingredient quality", classified_ingredients=classified_ingredients)
            result = await self.db.execute(
                select(IngredientQuality).where(
                    IngredientQuality.protein == protein, 
                    IngredientQuality.fat == fat, 
                    IngredientQuality.fiber == fiber, 
                    IngredientQuality.carbohydrate == carbohydrate, 
                    IngredientQuality.dirty_dozen == dirty_dozen
                )
            )

            existing_ingredient_quality = result.scalar_one_or_none()
                
            if existing_ingredient_quality:
                self.logger.debug("Found existing ingredient quality", id=existing_ingredient_quality.id)
                return existing_ingredient_quality
                
            # Create new ingredient quality
            self.logger.info("Creating new ingredient quality")
            
            # Handle both lowercase and capitalized keys
            # def get_ingredient_value(data, key):
            #     """Get ingredient value handling both lowercase and capitalized keys."""
            #     return data.get(key) or data.get(key.capitalize()) or "Unknown"
            
            new_ingredient_quality = IngredientQuality()
            new_ingredient_quality.protein = protein
            new_ingredient_quality.fat = fat
            new_ingredient_quality.fiber = fiber
            new_ingredient_quality.carbohydrate = carbohydrate

            new_ingredient_quality.dirty_dozen = dirty_dozen
            self.db.add(new_ingredient_quality)
            await self.db.flush()  # Flush to get the ID without committing
            await self.db.refresh(new_ingredient_quality)
                
            self.logger.info("Created new ingredient quality", ingredient_quality_id=new_ingredient_quality.id, protein=new_ingredient_quality.protein, fat=new_ingredient_quality.fat, fiber=new_ingredient_quality.fiber, carbohydrate=new_ingredient_quality.carbohydrate, dirty_dozen=new_ingredient_quality.dirty_dozen)
            return new_ingredient_quality
            
        except Exception as e:
            self.logger.error("Error in _set_or_create_ingredient_quality", error=str(e), classified_ingredients=classified_ingredients, dirty_dozen=dirty_dozen)
            return None

    async def _set_or_create_guaranteed_analysis(self, guaranteed_analysis_data: Dict) -> Optional[GuaranteedAnalysis]:
        """Set or update or create guaranteed analysis."""
        try:
            if not guaranteed_analysis_data or guaranteed_analysis_data == {}:
                self.logger.warning("Invalid guaranteed analysis data")
                return None
                
            # Try to find existing guaranteed analysis
            self.logger.debug("Looking for existing guaranteed analysis", data=guaranteed_analysis_data)
            result = await self.db.execute(
                select(GuaranteedAnalysis).where(
                    GuaranteedAnalysis.protein == guaranteed_analysis_data["protein"], 
                    GuaranteedAnalysis.fat == guaranteed_analysis_data["fat"], 
                    GuaranteedAnalysis.fiber == guaranteed_analysis_data["fiber"], 
                    GuaranteedAnalysis.moisture == guaranteed_analysis_data["moisture"], 
                    GuaranteedAnalysis.ash == guaranteed_analysis_data["ash"]
                )
            )

            existing_guaranteed_analysis = result.scalar_one_or_none()
                
            if existing_guaranteed_analysis:
                self.logger.debug("Found existing guaranteed analysis", id=existing_guaranteed_analysis.id)
                return existing_guaranteed_analysis
                
            # Create new guaranteed analysis
            self.logger.info("Creating new guaranteed analysis")
            new_guaranteed_analysis = GuaranteedAnalysis()
            new_guaranteed_analysis.protein = guaranteed_analysis_data["protein"]
            new_guaranteed_analysis.fat = guaranteed_analysis_data["fat"]
            new_guaranteed_analysis.fiber = guaranteed_analysis_data["fiber"]
            new_guaranteed_analysis.moisture = guaranteed_analysis_data["moisture"]
            new_guaranteed_analysis.ash = guaranteed_analysis_data["ash"]
            self.db.add(new_guaranteed_analysis)
            await self.db.flush()  # Flush to get the ID without committing
            await self.db.refresh(new_guaranteed_analysis)
                
            self.logger.info("Created new guaranteed analysis", guaranteed_analysis_id=new_guaranteed_analysis.id, protein=new_guaranteed_analysis.protein, fat=new_guaranteed_analysis.fat, fiber=new_guaranteed_analysis.fiber, moisture=new_guaranteed_analysis.moisture, ash=new_guaranteed_analysis.ash)
            return new_guaranteed_analysis
            
        except Exception as e:
            self.logger.error("Error in _set_or_create_guaranteed_analysis", error=str(e), data=guaranteed_analysis_data)
            return None
        
    async def _set_or_create_product(self, item_data: Dict, guaranteed_analysis_id: int, ingredient_quality_id: int) -> Optional[Product]:
        """Set or update or create product."""
        try:
            if not item_data["productName"] or item_data["productName"] == "":
                self.logger.warning("Invalid product name")
                return None
        
            # Try to find existing product
            self.logger.debug("Looking for existing product", name=item_data["productName"])
            result = await self.db.execute(
                select(Product).where(
                    Product.product_name == item_data["productName"], 
                    Product.brand == item_data["brand"],
                    Product.image_url == item_data["imageUrl"],
                    Product.description == item_data["description"]
                )
            )

            existing_product = result.scalar_one_or_none()

            if existing_product:
                self.logger.debug("Found existing product, updating", id=existing_product.id)
                existing_product.brand = item_data["brand"]
                existing_product.product_name = item_data["productName"]
                existing_product.guaranteed_analysis_id = guaranteed_analysis_id
                existing_product.ingredient_quality_id = ingredient_quality_id
                existing_product.category = item_data["category"]
                existing_product.flavors = item_data["flavors"]
                existing_product.processing_method = item_data["processingMethod"]
                existing_product.nutritionally_adequate = item_data["nutritionallyAdequate"]
                existing_product.ingredients = item_data["ingredients"]
                existing_product.food_storage = item_data["foodStorage"]
                existing_product.sourcing = item_data["sourcing"]
                existing_product.synthetic = item_data["synthetic"]
                existing_product.longevity = item_data["longevity"]
                existing_product.packaging_size = item_data["packagingSize"]
                existing_product.num_servings = item_data["numServings"]
                existing_product.container_weight = item_data["containerWeight"]
                existing_product.serving_size = item_data["servingSize"]
                existing_product.feeding_guidelines = item_data["feedingGuideline"]
                existing_product.description = item_data["description"]
                existing_product.product_url = item_data["productUrl"]
                existing_product.image_url = item_data["imageUrl"]
                existing_product.updated_at = datetime.utcnow()
                await self.db.flush()  # Flush changes without committing
                await self.db.refresh(existing_product)
                return existing_product
            
            # Create new product
            self.logger.info("Creating new product", name=item_data["productName"])
            new_product = Product()
            new_product.brand = item_data["brand"]
            new_product.product_name = item_data["productName"]
            new_product.guaranteed_analysis_id = guaranteed_analysis_id
            new_product.ingredient_quality_id = ingredient_quality_id
            new_product.category = item_data["category"]
            new_product.flavors = item_data["flavors"]
            new_product.processing_method = item_data["processingMethod"]
            new_product.nutritionally_adequate = item_data["nutritionallyAdequate"]
            new_product.ingredients = item_data["ingredients"]
            new_product.food_storage = item_data["foodStorage"]
            new_product.sourcing = item_data["sourcing"]
            new_product.synthetic = item_data["synthetic"]
            new_product.longevity = item_data["longevity"]
            new_product.packaging_size = item_data["packagingSize"]
            new_product.num_servings = item_data["numServings"]
            new_product.container_weight = item_data["containerWeight"]
            new_product.serving_size = item_data["servingSize"]
            new_product.feeding_guidelines = item_data["feedingGuideline"]
            new_product.description = item_data["description"]
            new_product.product_url = item_data["productUrl"]
            new_product.image_url = item_data["imageUrl"]
            self.db.add(new_product)
            await self.db.flush()  # Flush to get the ID without committing
            await self.db.refresh(new_product)
            
            self.logger.info("Created new product", product_id=new_product.id, name=new_product.product_name, brand=new_product.brand, image_url=new_product.image_url, description=new_product.description, processing_method=new_product.processing_method, storage_type=new_product.food_storage)
            return new_product
            
        except Exception as e:
            self.logger.error("Error in _set_or_create_product", error=str(e), product_name=item_data.get("productName"), brand=item_data.get("brand"))
            return None

    async def get_scraping_statistics(self) -> Dict[str, int]:
        """Get scraping statistics."""
        try:
            # Count total products
            total_products = await self.db.execute(select(Product))
            total_products_count = len(total_products.scalars().all())
            
            # Count ingredient qualities
            total_ingredient_qualities = await self.db.execute(select(IngredientQuality))
            total_ingredient_qualities_count = len(total_ingredient_qualities.scalars().all())
            
            # Count guaranteed analyses
            total_guaranteed_analyses = await self.db.execute(select(GuaranteedAnalysis))
            total_guaranteed_analyses_count = len(total_guaranteed_analyses.scalars().all())
            
            return {
                "total_products": total_products_count,
                "total_ingredient_qualities": total_ingredient_qualities_count,
                "total_guaranteed_analyses": total_guaranteed_analyses_count,
                "last_updated": datetime.utcnow().isoformat()
            }
        except Exception as e:
            self.logger.error("Error getting scraping statistics", error=str(e))
            return {
                "total_products": 0,
                "total_ingredient_qualities": 0,
                "total_guaranteed_analyses": 0,
                "error": str(e)
            }