"""Dog food scraper implementation."""

import re
import aiohttp
import asyncio
from typing import Any, Dict, List, Optional


import structlog
from bs4 import BeautifulSoup

from app.core.logging import LoggerMixin
# from app.scrapers.base import BaseScraper

logger = structlog.get_logger(__name__)


class DogFoodScraper(LoggerMixin):
    """Scraper for dog food data from various sources."""

    def __init__(self, api_key: str) -> None:
        """Initialize the dog food scraper."""
        # super().__init__()
        self.headers = {
            "x-api-key": api_key
        }
    BASE_URL = "https://api.kadoa.com/v4"
    
    async def scrape(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Scrape dog food data from all configured sources."""
        all_data = []
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.BASE_URL}/workflows/{workflow_id}/data", headers=self.headers) as response:
                response.raise_for_status()
                data = await response.json()
                all_data = data['data']

        return all_data