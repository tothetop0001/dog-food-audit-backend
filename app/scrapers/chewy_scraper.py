import asyncio
import time
import random
import sys
import os
from typing import Any, Dict, List, Optional

import aiohttp
import structlog
import requests
import urllib.parse
from bs4 import BeautifulSoup

# Add the project root to the Python path when running as a script
if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, project_root)

from app.scrapers.base import BaseScraper

logger = structlog.get_logger(__name__)


class ChewyScraper(BaseScraper):
    """Chewy scraper implementation with aggressive rate limiting handling."""
    
    BASE_URL: str = "https://www.chewy.com"
    
    def __init__(self) -> None:
        """Initialize the Chewy scraper."""
        super().__init__()
        # Override headers for Chewy specifically
        self.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        })

        self.token = "744094ddf86348049c8a10c94f046a5a56e9b8af5da"
        self.target_url = urllib.parse.quote(f"{self.BASE_URL}/b/dog-food-332")

    async def fetch_with_retry(self) -> Optional[str]:
        """Fetch a page with aggressive retry logic for rate limiting."""
        url = "http://api.scrape.do/?token={}&url={}&super=true".format(self.token, self.target_url)
        response = requests.request("GET", url, headers=self.headers)
        return response.text

    async def fetch_product_list(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch a list of dog food products from Chewy."""
        content = await self.fetch_with_retry()
        
        if not content:
            self.logger.warning("Failed to fetch product list, returning fallback data")
            return self._get_fallback_products(limit)
        
        # soup = self.parse_html(content)
        soup = BeautifulSoup(content, "html.parser")
        products = []

        for item in soup.select(".kib-product-card")[:limit]:
            try:
                print(item)
                # name_elem = item.select_one(".prod-title")
                # price_elem = item.select_one(".ga-eec__price")
                # link_elem = item.select_one("a")
                
                # if name_elem and link_elem:
                #     name = self.clean_text(name_elem.get_text())
                #     price = self.clean_text(price_elem.get_text()) if price_elem else None
                #     link = self.BASE_URL + link_elem.get("href", "")
                    
                #     products.append({
                #         "name": name,
                #         "price": price,
                #         "target_url": link,
                #         "brand": self._extract_brand(name),
                #         "category": "dog_food"
                #     })
            except Exception as e:
                self.logger.warning("Error parsing product item", error=str(e))
                continue

        return products
        # return soup
    
    async def fetch_product_detail(self, target_url: str) -> Dict[str, Any]:
        """Fetch detailed information for a specific product."""
        content = await self.fetch_with_retry()
        
        if not content:
            return {"name": "Unknown Product", "ingredients": None, "url": target_url}
        
        soup = self.parse_html(content)
        
        try:
            name_elem = soup.select_one("h1[data-testid='product-title']")
            name = self.clean_text(name_elem.get_text()) if name_elem else "Unknown Product"
            
            ingredients = soup.find("div", string="Ingredients")
            ingredients_text = None
            if ingredients:
                next_div = ingredients.find_next("div")
                if next_div:
                    ingredients_text = self.clean_text(next_div.get_text())
            
            return {
                "name": name,
                "ingredients": ingredients_text,
                "url": target_url,
                "brand": self._extract_brand(name)
            }
        except Exception as e:
            self.logger.error("Error parsing product detail", url=target_url, error=str(e))
            return {"name": "Unknown Product", "ingredients": None, "url": target_url}
    
    def _extract_brand(self, product_name: str) -> str:
        """Extract brand name from product name."""
        if not product_name:
            return "Unknown"
        
        # Common dog food brands
        brands = [
            "Royal Canin", "Hill's", "Purina", "Blue Buffalo", "Wellness", 
            "Orijen", "Acana", "Taste of the Wild", "Merrick", "Fromm",
            "Nutro", "Iams", "Eukanuba", "Pedigree", "Cesar", "Beneful"
        ]
        
        product_lower = product_name.lower()
        for brand in brands:
            if brand.lower() in product_lower:
                return brand
        
        # If no known brand found, try to extract first word
        words = product_name.split()
        return words[0] if words else "Unknown"
    
    def _get_fallback_products(self, limit: int) -> List[Dict[str, Any]]:
        """Return fallback product data when scraping fails."""
        fallback_products = [
            {
                "name": "Royal Canin Adult Dry Dog Food",
                "price": "$45.99",
                "url": f"{self.BASE_URL}/royal-canin-adult-dry-dog-food",
                "brand": "Royal Canin",
                "category": "dog_food"
            },
            {
                "name": "Hill's Science Diet Adult Dog Food",
                "price": "$52.99",
                "url": f"{self.BASE_URL}/hills-science-diet-adult-dog-food",
                "brand": "Hill's",
                "category": "dog_food"
            },
            {
                "name": "Blue Buffalo Life Protection Formula",
                "price": "$38.99",
                "url": f"{self.BASE_URL}/blue-buffalo-life-protection-formula",
                "brand": "Blue Buffalo",
                "category": "dog_food"
            }
        ]
        return fallback_products[:limit]
    
    async def scrape(self) -> List[Dict[str, Any]]:
        """Main scraping method required by BaseScraper."""
        products = await self.fetch_product_list(10)
        
        # Add delays between product detail fetching
        # for i, product in enumerate(products):
        #     if i > 0:  # Skip delay for first product
        #         delay = random.uniform(10, 20)  # 10-20 seconds between products
        #         self.logger.info(f"Waiting {delay:.1f} seconds before next product...")
        #         await asyncio.sleep(delay)
            
        #     # Fetch detailed information for each product
        #     detail = await self.fetch_product_detail(product["target_url"])
        #     product.update(detail)
        
        # return products
        return products
    
    def get_source_name(self) -> str:
        """Get the name of the data source."""
        return "chewy"


async def run():
    """Test function to run the scraper."""
    async with ChewyScraper() as scraper:
        logger.info("Starting Chewy scraper test...")
        products = await scraper.scrape()
        print(products)
        
        # logger.info(f"Scraped {len(products)} products from Chewy")
        # for product in products:
        #     logger.info("Product", name=product.get("name"), brand=product.get("brand"))


if __name__ == "__main__":
    asyncio.run(run())
