"""Web scraping module for dog food data."""

from app.scrapers.base import BaseScraper
from app.scrapers.dog_food_scraper import DogFoodScraper

__all__ = ["BaseScraper", "DogFoodScraper"]
