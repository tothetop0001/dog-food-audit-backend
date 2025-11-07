"""Dog food database models."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class IngredientQuality(Base):
    """Ingredient model."""

    __tablename__ = "ingredient_qualities"

    id = Column(Integer, primary_key=True, index=True)
    protein = Column(String(100), nullable=True)
    fat = Column(String(100), nullable=True)
    fiber = Column(String(100), nullable=True)
    carbohydrate = Column(String(100), nullable=True)
    dirty_dozen = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)

    # Relationships
    products = relationship("Product", back_populates="ingredient_quality")

    def __repr__(self) -> str:
        return f"<IngredientQuality(id={self.id}, protein='{self.protein}', fat='{self.fat}', fiber='{self.fiber}', carbohydrate='{self.carbohydrate}', dirty_dozen='{self.dirty_dozen}')>"

class GuaranteedAnalysis(Base):
    """Guaranteed analysis model."""
    __tablename__ = "guaranteed_analyses"
    id = Column(Integer, primary_key=True, index=True)
    protein = Column(String(100), nullable=True)
    fat = Column(String(100), nullable=True)
    fiber = Column(String(100), nullable=True)
    moisture = Column(String(100), nullable=True)
    ash = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)

    # Relationships
    products = relationship("Product", back_populates="guaranteed_analysis")

    def __repr__(self) -> str:
        return f"<GuaranteedAnalysis(id={self.id}, protein='{self.protein}', fat='{self.fat}', fiber='{self.fiber}', moisture='{self.moisture}', ash='{self.ash}')>"

class Product(Base):
    """Product model."""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    brand = Column(String(255), nullable=False)
    category = Column(String(500), nullable=True)
    product_name = Column(String(500), nullable=False, index=True)
    ingredient_quality_id = Column(Integer, ForeignKey("ingredient_qualities.id"), nullable=True)
    guaranteed_analysis_id = Column(Integer, ForeignKey("guaranteed_analyses.id"), nullable=True)
    flavors = Column(String(500), nullable=True)
    processing_method = Column(String(100), nullable=True)
    nutritionally_adequate = Column(String(100), nullable=True)
    ingredients = Column(Text, nullable=True)
    food_storage = Column(String(100), nullable=True)
    sourcing = Column(String(100), nullable=True)
    synthetic = Column(Integer, nullable=True)
    longevity = Column(Integer, nullable=True)
    packaging_size = Column(String(100), nullable=True)
    shelf_life = Column(Integer, nullable=True)
    num_servings = Column(Text, nullable=True)
    container_weight = Column(Text, nullable=True)
    serving_size = Column(Text, nullable=True)
    feeding_guidelines = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    product_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    ingredient_quality = relationship("IngredientQuality", back_populates="products")
    guaranteed_analysis = relationship("GuaranteedAnalysis", back_populates="products")

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, brand='{self.brand}', product_name='{self.product_name}')>"

