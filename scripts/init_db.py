#!/usr/bin/env python3
"""Initialize database with sample data."""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import AsyncSessionLocal, init_db
from app.core.logging import configure_logging, get_logger
from app.models.dog_food import DogFoodBrand, DogFoodFlavors, DogFoodProduct
from app.schemas.dog_food import DogFoodBrandCreate, DogFoodFlavorsCreate, DogFoodProductCreate
from app.services.dog_food_service import DogFoodService

configure_logging()
logger = get_logger(__name__)


async def create_sample_data():
    """Create sample data for testing."""
    print("Creating sample data")
    async with AsyncSessionLocal() as db:
        service = DogFoodService(db)
        
        # Create sample brands
        brands_data = [
            {"brand_name": "Royal Canin", "website_url": "https://www.royalcanin.com"},
            {"brand_name": "Hill's Science Diet", "website_url": "https://www.hillspet.com"},
            {"brand_name": "Blue Buffalo", "website_url": "https://www.bluebuffalo.com"},
            {"brand_name": "Purina Pro Plan", "website_url": "https://www.purina.com"},
            {"brand_name": "Wellness", "website_url": "https://www.wellnesspetfood.com"},
        ]
        
        brands = []
        for brand_data in brands_data:
            brand = await service.create_brand(DogFoodBrandCreate(**brand_data))
            brands.append(brand)
            logger.info(f"Created brand: {brand.brand_name}")
        
        # Create sample categories
        flavors_data = [
            {"flavor_name": "Chicken", "feeding_guidelines": "Kibble and dry dog food", "ingredients": "Chicken, chicken meal, chicken fat, chicken liver, chicken gizzards, chicken hearts, chicken lungs, chicken kidneys, chicken trachea, chicken broth, chicken liver, chicken gizzards, chicken hearts, chicken lungs, chicken kidneys, chicken trachea, chicken broth"},
            {"flavor_name": "Beef", "feeding_guidelines": "Canned and wet dog food", "ingredients": "Beef, beef meal, beef fat, beef liver, beef gizzards, beef hearts, beef lungs, beef kidneys, beef trachea, beef broth, beef liver, beef gizzards, beef hearts, beef lungs, beef kidneys, beef trachea, beef broth"},
            {"flavor_name": "Lamb", "feeding_guidelines": "Food for puppies", "ingredients": "Lamb, lamb meal, lamb fat, lamb liver, lamb gizzards, lamb hearts, lamb lungs, lamb kidneys, lamb trachea, lamb broth, lamb liver, lamb gizzards, lamb hearts, lamb lungs, lamb kidneys, lamb trachea, lamb broth"},
            {"flavor_name": "Turkey", "feeding_guidelines": "Food for senior dogs", "ingredients": "Turkey, turkey meal, turkey fat, turkey liver, turkey gizzards, turkey hearts, turkey lungs, turkey kidneys, turkey trachea, turkey broth, turkey liver, turkey gizzards, turkey hearts, turkey lungs, turkey kidneys, turkey trachea, turkey broth"},
            {"flavor_name": "Salmon", "feeding_guidelines": "Grain-free dog food", "ingredients": "Salmon, salmon meal, salmon fat, salmon liver, salmon gizzards, salmon hearts, salmon lungs, salmon kidneys, salmon trachea, salmon broth, salmon liver, salmon gizzards, salmon hearts, salmon lungs, salmon kidneys, salmon trachea, salmon broth"},
            {"flavor_name": "Salmon", "feeding_guidelines": "Grain-free dog food", "ingredients": "Salmon, salmon meal, salmon fat, salmon liver, salmon gizzards, salmon hearts, salmon lungs, salmon kidneys, salmon trachea, salmon broth, salmon liver, salmon gizzards, salmon hearts, salmon lungs, salmon kidneys, salmon trachea, salmon broth"},
            {"flavor_name": "Salmon", "feeding_guidelines": "Grain-free dog food", "ingredients": "Salmon, salmon meal, salmon fat, salmon liver, salmon gizzards, salmon hearts, salmon lungs, salmon kidneys, salmon trachea, salmon broth, salmon liver, salmon gizzards, salmon hearts, salmon lungs, salmon kidneys, salmon trachea, salmon broth"},
        ]
        
        flavors = []
        for flavor_data in flavors_data:
            flavor = await service.create_flavor(DogFoodFlavorsCreate(**flavor_data))
            flavors.append(flavor)
            logger.info(f"Created flavor: {flavor.flavor_name}")
        
        # Create sample dog food products
        products_data = [
            {
                "product_name": "Royal Canin Adult Medium",
                "brand_id": brands[0].id,
                "flavor_id": flavors[0].id,
                "description": "Complete nutrition for adult medium dogs",
                "price": 45.99,
                "size": "15 lbs",
                "weight_grams": 6804,
                "life_stage": "Adult",
                "breed_size": "Medium",
                "rating": 4.5,
                "review_count": 150,
            },
            {
                "product_name": "Hill's Science Diet Puppy",
                "brand_id": brands[1].id,
                "flavor_id": flavors[2].id,
                "description": "Nutrition for growing puppies",
                "price": 38.50,
                "size": "12.5 lbs",
                "weight_grams": 5670,
                "life_stage": "Puppy",
                "breed_size": "All",
                "rating": 4.3,
                "review_count": 89,
            },
            {
                "product_name": "Blue Buffalo Life Protection",
                "brand_id": brands[2].id,
                "flavor_id": flavors[0].id,
                "description": "Natural adult dog food",
                "price": 42.99,
                "size": "15 lbs",
                "weight_grams": 6804,
                "life_stage": "Adult",
                "breed_size": "All",
                "rating": 4.2,
                "review_count": 203,
            },
            {
                "product_name": "Purina Pro Plan Sensitive Skin",
                "brand_id": brands[3].id,
                "flavor_id": flavors[4].id,
                "description": "For dogs with sensitive skin",
                "price": 39.99,
                "size": "16 lbs",
                "weight_grams": 7257,
                "life_stage": "Adult",
                "breed_size": "All",
                "special_diet": "Sensitive Skin",
                "rating": 4.1,
                "review_count": 67,
            },
            {
                "product_name": "Wellness Core Grain-Free",
                "brand_id": brands[4].id,
                "flavor_id": flavors[4].id,
                "description": "Grain-free high protein formula",
                "price": 49.99,
                "size": "12 lbs",
                "weight_grams": 5443,
                "life_stage": "Adult",
                "breed_size": "All",
                "special_diet": "Grain-Free",
                "rating": 4.4,
                "review_count": 124,
            },
        ]
        
        for product_data in products_data:
            product = await service.create_product(DogFoodProductCreate(**product_data))
            logger.info(f"Created product: {product.product_name}")
        
        logger.info("Sample data creation completed")


async def main():
    """Main function."""
    try:
        logger.info("Initializing database...")
        await init_db()
        logger.info("Database initialized successfully")
        
        logger.info("Creating sample data...")
        await create_sample_data()
        logger.info("Sample data created successfully")
        
    except Exception as e:
        logger.error(f"Error during initialization: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
