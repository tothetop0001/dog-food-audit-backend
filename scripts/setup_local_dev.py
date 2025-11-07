#!/usr/bin/env python3
"""Setup local development environment."""

import asyncio
import os
import sys
import shutil
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Create .env file first if it doesn't exist
def create_env_file():
    """Create .env file from template if it doesn't exist."""
    env_file = Path(".env")
    if not env_file.exists():
        env_example = Path("env.example")
        if env_example.exists():
            shutil.copy(env_example, env_file)
            print("✅ Created .env file from template")
        else:
            print("❌ env.example file not found!")
            return False
    return True

# Create .env file before importing any modules that need configuration
if not create_env_file():
    sys.exit(1)

# Now import modules that need configuration
from app.core.config import get_settings
from app.core.database import AsyncSessionLocal, init_db
from app.core.logging import configure_logging, get_logger
from app.models.dog_food import Product, IngredientQuality, GuaranteedAnalysis
from app.services.dog_food_service import DogFoodService

configure_logging()
logger = get_logger(__name__)


def check_environment():
    """Check if environment is properly configured."""
    logger.info("Checking environment configuration...")
    
    # Check database connection
    try:
        settings = get_settings()
        logger.info(f"Database URL: {settings.database_url}")
        logger.info(f"Using configuration with defaults for local development")
        return True
    except Exception as e:
        logger.error(f"Error checking configuration: {e}")
        return False


async def setup_database():
    """Set up the database."""
    
    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized successfully")
        
        # Check if we have any data
        async with AsyncSessionLocal() as db:
            service = DogFoodService(db)
            brands = await service.get_brands()
            
            if not brands:
                logger.info("No data found. Creating sample data...")
                await create_sample_data()
            else:
                logger.info(f"Found {len(brands)} brands in database")
        
        return True
        
    except Exception as e:
        logger.error(f"Error setting up database: {e}")
        return False


async def create_sample_data():
    """Create sample data for testing."""
    from app.schemas.dog_food import ProductCreate, IngredientQualityCreate, GuaranteedAnalysisCreate
    
    async with AsyncSessionLocal() as db:
        service = DogFoodService(db)
        
        # Create sample brands
        guaranteed_analyses_data = [
            {"name": "Royal Canin", "website": "https://www.royalcanin.com", "description": "Premium pet nutrition"},
            {"name": "Hill's Science Diet", "website": "https://www.hillspet.com", "description": "Veterinarian recommended"},
            {"name": "Blue Buffalo", "website": "https://www.bluebuffalo.com", "description": "Natural pet food"},
            {"name": "Purina Pro Plan", "website": "https://www.purina.com", "description": "Advanced nutrition"},
            {"name": "Wellness", "website": "https://www.wellnesspetfood.com", "description": "Natural pet food"},
        ]
        
        guaranteed_analyses = []
        for guaranteed_analysis_data in guaranteed_analyses_data:
            guaranteed_analysis = await service.create_guaranteed_analysis(GuaranteedAnalysisCreate(**guaranteed_analysis_data))
            guaranteed_analyses.append(guaranteed_analysis)
            logger.info(f"Created guaranteed analysis: {guaranteed_analysis.name}")
        
        # Create sample categories
        ingredient_qualities_data = [
            {"name": "Dry Food", "description": "Kibble and dry dog food"},
            {"name": "Wet Food", "description": "Canned and wet dog food"},
            {"name": "Puppy Food", "description": "Food for puppies"},
            {"name": "Senior Food", "description": "Food for senior dogs"},
            {"name": "Grain-Free", "description": "Grain-free dog food"},
        ]
        
        ingredient_qualities = []
        for ingredient_quality_data in ingredient_qualities_data:
            ingredient_quality = await service.create_ingredient_quality(IngredientQualityCreate(**ingredient_quality_data))
            ingredient_qualities.append(ingredient_quality)
            logger.info(f"Created ingredient quality: {ingredient_quality.name}")
        
        # Create sample dog food products
        products_data = [
            {
                "name": "Royal Canin Adult Medium",
                "guaranteed_analysis_id": guaranteed_analyses[0].id,
                "ingredient_quality_id": ingredient_qualities[0].id,
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
                "name": "Hill's Science Diet Puppy",
                "guaranteed_analysis_id": guaranteed_analyses[1].id,
                "ingredient_quality_id": ingredient_qualities[2].id,
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
                "name": "Blue Buffalo Life Protection",
                "guaranteed_analysis_id": guaranteed_analyses[2].id,
                "ingredient_quality_id": ingredient_qualities[0].id,
                "description": "Natural adult dog food",
                "price": 42.99,
                "size": "15 lbs",
                "weight_grams": 6804,
                "life_stage": "Adult",
                "breed_size": "All",
                "rating": 4.2,
                "review_count": 203,
            },
        ]
        
        for product_data in products_data:
            product = await service.create_product(ProductCreate(**product_data))
            logger.info(f"Created product: {product.product_name}")
        
        logger.info("Sample data creation completed")


def print_instructions():
    """Print setup instructions."""
    print("\n" + "="*60)
    print("🐕 DOG FOOD API - LOCAL DEVELOPMENT SETUP")
    print("="*60)
    print()
    print("✅ Environment setup completed!")
    print()
    print("📋 NEXT STEPS:")
    print("1. Make sure PostgreSQL is running on your system")
    print("2. Update the .env file with your PostgreSQL credentials:")
    print("   - DATABASE_URL=postgresql://username:password@localhost:5432/dog_food_db")
    print("   - DATABASE_URL_ASYNC=postgresql+asyncpg://username:password@localhost:5432/dog_food_db")
    print()
    print("3. Create the database (if not exists):")
    print("   createdb dog_food_db")
    print()
    print("4. Run database migrations:")
    print("   alembic upgrade head")
    print()
    print("5. Start the development server:")
    print("   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    print()
    print("6. Access the API:")
    print("   - API Documentation: http://localhost:8000/docs")
    print("   - Health Check: http://localhost:8000/health")
    print("   - API Base URL: http://localhost:8000/api/v1")
    print()
    print("🔧 OPTIONAL: Install Redis for background tasks")
    print("   - Windows: Download from https://github.com/microsoftarchive/redis/releases")
    print("   - Or use the memory broker (already configured)")
    print()
    print("="*60)


async def main():
    """Main setup function."""
    try:
        logger.info("Starting local development setup...")
        
        # Check environment
        if not check_environment():
            logger.error("Environment check failed")
            sys.exit(1)
        
        # Setup database
        if not await setup_database():
            logger.error("Database setup failed")
            sys.exit(1)
        
        logger.info("Local development setup completed successfully!")
        print_instructions()
        
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
