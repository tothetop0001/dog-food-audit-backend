"""Base scraper class with common functionality."""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import aiohttp
import structlog
from bs4 import BeautifulSoup

from app.core.config import get_settings
from app.core.logging import LoggerMixin

logger = structlog.get_logger(__name__)


class BaseScraper(ABC, LoggerMixin):
    """Base scraper class with common functionality."""

    def __init__(self) -> None:
        """Initialize the scraper."""
        self.settings = get_settings()
        self.session: Optional[aiohttp.ClientSession] = None
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    async def __aenter__(self) -> "BaseScraper":
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=10, limit_per_host=5)
        )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def fetch_page(self, url: str) -> Optional[str]:
        """Fetch a web page and return its content."""
        if not self.session:
            raise RuntimeError("Scraper session not initialized. Use async context manager.")

        try:
            self.logger.info("Fetching page", url=url)
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    self.logger.info("Page fetched successfully", url=url, size=len(content))
                    return content
                else:
                    self.logger.warning("Failed to fetch page", url=url, status=response.status)
                    return None
        except Exception as e:
            self.logger.error("Error fetching page", url=url, error=str(e))
            return None

    def parse_html(self, html_content: str) -> BeautifulSoup:
        """Parse HTML content using BeautifulSoup."""
        return BeautifulSoup(html_content, "lxml")

    async def delay(self, seconds: Optional[float] = None) -> None:
        """Add delay between requests to be respectful to the server."""
        delay_time = seconds or self.settings.scraping_delay_seconds
        if delay_time > 0:
            await asyncio.sleep(delay_time)

    @abstractmethod
    async def scrape(self) -> List[Dict[str, Any]]:
        """Scrape data from the target website."""
        pass

    @abstractmethod
    def get_source_name(self) -> str:
        """Get the name of the data source."""
        pass

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate scraped data."""
        required_fields = ["name", "brand", "category"]
        return all(field in data and data[field] for field in required_fields)

    def clean_text(self, text: str) -> str:
        """Clean and normalize text data."""
        if not text:
            return ""
        return " ".join(text.strip().split())

    def extract_price(self, price_text: str) -> Optional[float]:
        """Extract numeric price from text."""
        if not price_text:
            return None
        
        import re
        # Remove currency symbols and extract numbers
        price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
        if price_match:
            try:
                return float(price_match.group())
            except ValueError:
                return None
        return None

    def extract_weight_grams(self, size_text: str) -> Optional[int]:
        """Extract weight in grams from size text."""
        if not size_text:
            return None
        
        import re
        size_text = size_text.lower()
        
        # Look for weight patterns
        patterns = [
            r'(\d+(?:\.\d+)?)\s*kg',  # kilograms
            r'(\d+(?:\.\d+)?)\s*lbs?',  # pounds
            r'(\d+(?:\.\d+)?)\s*g',  # grams
            r'(\d+(?:\.\d+)?)\s*oz',  # ounces
        ]
        
        for pattern in patterns:
            match = re.search(pattern, size_text)
            if match:
                value = float(match.group(1))
                if 'kg' in pattern:
                    return int(value * 1000)
                elif 'lbs' in pattern or 'lb' in pattern:
                    return int(value * 453.592)  # pounds to grams
                elif 'g' in pattern:
                    return int(value)
                elif 'oz' in pattern:
                    return int(value * 28.3495)  # ounces to grams
        
        return None
