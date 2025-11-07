"""Score API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr

from app.core.database import get_async_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.services.scoring_system_service import ScoringSystemService
from app.services.recommend_products import ProductRecommendationService

router = APIRouter()

class EmailRequest(BaseModel):
    """Email request model."""
    email: EmailStr
    subject: str = "Dog Food Score Request"
    message: str = "Please send me the dog food score analysis."

@router.get("/")
async def get_score(
  add_topper: bool = False,
  pet_name: str = "",
  breed: str = "",
  years: str = "",
  months: str = "",
  weight: str = "",
  product: str = "",
  storage: str = "",
  packaging_size: str = "",
  shelf_life: str = "",
  topper: str = "",
  topper_storage: str = "",
  topper_packaging_size: str = "",
  topper_shelf_life: str = "",
  db: AsyncSession = Depends(get_async_db),
  # current_user: User = Depends(get_current_active_user)
):
    """Get score for a product. Requires authentication."""
    # return products, brands, flavors
    service = ScoringSystemService(db)
    score = await service.get_score(add_topper=add_topper, pet_name=pet_name, breed=breed, year=years, month=months, weight=weight, product=product, storage=storage, packaging_size=packaging_size, topper=topper, shelf_life=shelf_life, topper_storage=topper_storage, topper_packaging_size=topper_packaging_size, topper_shelf_life=topper_shelf_life)
    return score

@router.post("/email")
async def send_email_request(
    request: EmailRequest,
    db: AsyncSession = Depends(get_async_db),
    # current_user: User = Depends(get_current_active_user)
):
    """Send email request for dog food score analysis."""
    print(request.email)
    try:
        # Get top 5 recommended products
        recommendation_service = ProductRecommendationService(db)
        top_products = await recommendation_service.get_top_products(limit=10)
        
        # Here you would implement your email sending logic
        # For now, we'll just return the top products
        
        # Example email sending logic (you'll need to implement actual email sending)
        # from app.services.email_service import send_email
        # await send_email(
        #     to_email=request.email,
        #     subject=request.subject,
        #     message=request.message,
        #     products=top_products
        # )
        
        return top_products
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")

@router.get("/recommendations")
async def get_recommendations(
    limit: int = 5,
    db: AsyncSession = Depends(get_async_db),
    # current_user: User = Depends(get_current_active_user)
):
    """Get top-scoring product recommendations."""
    try:
        recommendation_service = ProductRecommendationService(db)
        top_products = await recommendation_service.get_top_products(limit=limit)
        
        return {
            "message": f"Top {limit} recommended products",
            "count": len(top_products),
            "products": top_products
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")