"""Pydantic schemas for dog food models."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, validator


class IngredientQualityBase(BaseModel):
    """Base schema for dog food brand."""
    
    protein: str = Field(..., min_length=1, max_length=100, description="Protein")
    fat: str = Field(..., min_length=1, max_length=100, description="Fat")
    fiber: str = Field(..., min_length=1, max_length=100, description="Fiber")
    carbohydrate: str = Field(..., min_length=1, max_length=100, description="Carbohydrate")
    dirty_dozen: Optional[str] = Field(None, nullable=True, description="Dirty dozen")


class IngredientQualityCreate(IngredientQualityBase):
    """Schema for creating a ingredient quality."""
    pass


class IngredientQualityResponse(IngredientQualityBase):
    """Schema for ingredient quality response."""
    
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class GuaranteedAnalysisBase(BaseModel):
    """Base schema for dog food flavors."""
    
    protein: str = Field(..., min_length=1, max_length=100, description="Protein")
    fat: str = Field(..., min_length=1, max_length=100, description="Fat")
    fiber: str = Field(..., min_length=1, max_length=100, description="Fiber")
    moisture: str = Field(..., min_length=1, max_length=100, description="Moisture")
    ash: str = Field(..., min_length=1, max_length=100, description="Ash")
    created_at: datetime = Field(default=datetime.utcnow, nullable=True, description="Creation date")
    updated_at: datetime = Field(default=datetime.utcnow, nullable=True, description="Last update date")
    
class GuaranteedAnalysisCreate(GuaranteedAnalysisBase):
    """Schema for creating a guaranteed analysis."""
    pass

class GuaranteedAnalysisResponse(GuaranteedAnalysisBase):
    """Schema for guaranteed analysis response."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    """Base schema for product."""
    
    product_name: str = Field(..., min_length=1, max_length=500, description="Product name")
    brand: str = Field(..., nullable=False, description="The brand of Product Name")
    processing_method: Optional[str] = Field(None, nullable=True, description="Processing method")
    category: Optional[str] = Field(None, nullable=True, description="Category")
    ingredient_quality_id: int = Field(..., description="Ingredient quality ID")
    guaranteed_analysis_id: int = Field(..., description="Guaranteed analysis ID")
    flavors: Optional[str] = Field(None, nullable=True, description="Flavors")
    nutritionally_adequate: Optional[str] = Field(None, nullable=True, description="Nutritionally adequate")
    ingredients: Optional[str] = Field(None, nullable=True, description="Ingredients")
    food_storage: Optional[str] = Field(None, nullable=True, description="Food storage")
    sourcing: Optional[str] = Field(None, nullable=True, description="Sourcing")
    synthetic: Optional[int] = Field(None, nullable=True, description="Synthetic")
    longevity: Optional[int] = Field(None, nullable=True, description="Longevity")
    packaging_size: Optional[str] = Field(None, nullable=True, description="Packaging size")
    shelf_life: Optional[int] = Field(None, nullable=True, description="Shelf life")
    num_servings: Optional[str] = Field(None, nullable=True, description="Number of servings")
    container_weight: Optional[str] = Field(None, nullable=True, description="Container weight")
    serving_size: Optional[str] = Field(None, nullable=True, description="Serving size")
    feeding_guidelines: Optional[str] = Field(None, nullable=True, description="Feeding guidelines")
    description: Optional[str] = Field(None, nullable=True, description="Product description")
    image_url: Optional[str] = Field(None, max_length=500, description="Image URL")
    product_url: Optional[str] = Field(None, max_length=500, description="Product URL")
    created_at: datetime = Field(default=datetime.utcnow, nullable=True, description="Creation date")
    updated_at: datetime = Field(default=datetime.utcnow, nullable=True, description="Last update date")

class ProductCreate(ProductBase):
    """Schema for creating a product."""
    pass

class ProductResponse(ProductBase):
    """Schema for product response."""
    id: int
    category: Optional[str]
    ingredient_quality_id: int
    guaranteed_analysis_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

