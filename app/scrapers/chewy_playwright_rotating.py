# chewy_playwright_rotating.py
# pip install playwright
# python -m playwright install
# run: python chewy_playwright_rotating.py

import asyncio, csv, json, random, re, time
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from app.core.logging import LoggerMixin

CATEGORY_URL = "https://www.chewy.com/b/dog-food-332"
OUTPUT_CSV = "chewy_dogfood.csv"
OUTPUT_JSONL = "chewy_dogfood.jsonl"

# Put proxy entries here (or leave empty for no proxy). Example format:
# PROXY_POOL = ["http://user:pass@1.2.3.4:8000", "socks5://127.0.0.1:9050"]
PROXY_POOL = []  # <-- fill if using proxies

DELAY_MIN = 2.0
DELAY_MAX = 4.5
PAGE_TIMEOUT_MS = 45000
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"

PRODUCT_HREF_RE = re.compile(r"/[^/]+/p/|/product/|/p/|/dp/|/product-page", re.IGNORECASE)

class ChewyPlaywrightScraper(LoggerMixin):
    """Scraper for Chewy."""

    def __init__(self):
        """Initialize the Chewy scraper."""
        super().__init__()
    
    def parse_price(self, text):
      if not text: return None
      m = re.search(r"(\d+(?:\.\d+)?)", text.replace(",", ""))
      return float(m.group(1)) if m else None

    async def extract_jsonld_from_page(self, page):
      texts = await page.locator('script[type="application/ld+json"]').all_text_contents()
      for t in texts:
          try:
              d = json.loads(t.strip())
          except:
              continue
          if isinstance(d, list):
              for item in d:
                  if isinstance(item, dict) and item.get("@type","").lower() == "product":
                      return item
          elif isinstance(d, dict):
              if d.get("@type","").lower() == "product": return d
              if "@graph" in d:
                  for item in d["@graph"]:
                      if item.get("@type","").lower() == "product": return item
      return None

    async def gather_product_links_from_category(self, page):
      found, seen = [], set()
      # try pagination + scroll heuristics
      for _ in range(20):
          anchors = await page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
          for a in anchors:
              if a and PRODUCT_HREF_RE.search(a) and a not in seen:
                  seen.add(a); found.append(a)
          # try next button
          next_selectors = ['a[rel="next"]','a[aria-label="Next"]','button.next','a.next']
          clicked=False
          for sel in next_selectors:
              if await page.locator(sel).count():
                  try:
                      await page.locator(sel).first.click()
                      await page.wait_for_load_state("domcontentloaded", timeout=PAGE_TIMEOUT_MS)
                      clicked=True; break
                  except: pass
          if clicked: await asyncio.sleep(random.uniform(1.0,2.0)); continue
          # scroll to load more
          await page.evaluate("window.scrollBy(0, document.body.scrollHeight)"); await asyncio.sleep(1.2)
      return [u for u in found if u.startswith("http")]

    def get_guaranteed_analysis_data(self, table: BeautifulSoup):
        guaranteed_analysis_data = {
          "protein": "",
          "fat": "",
          "fiber": "",
          "moisture": "",
          "ash": "",
          "dirty_dozen": ""
        }
        tbody = table.select_one("tbody")
        if tbody is None:
            return guaranteed_analysis_data
        for row in tbody.select("tr"):
          if row.select_one("th").get_text().lower() == "protein" or row.select_one("th").get_text().lower() == "protein (min)" or row.select_one("th").get_text().lower() == "protein (max)" or row.select_one("th").get_text().lower() == "crude protein (min)" or row.select_one("th").get_text().lower() == "crude protein (max)" or row.select_one("th").get_text().lower() == "crude protein":
            guaranteed_analysis_data["protein"] = re.search(r"\d+\.?\d*", row.select_one("td").get_text()).group()
          elif row.select_one("th").get_text().lower() == "fat" or row.select_one("th").get_text().lower() == "fat (min)" or row.select_one("th").get_text().lower() == "fat (max)" or row.select_one("th").get_text().lower() == "crude fat (min)" or row.select_one("th").get_text().lower() == "crude fat (max)" or row.select_one("th").get_text().lower() == "crude fat":
            guaranteed_analysis_data["fat"] = re.search(r"\d+\.?\d*", row.select_one("td").get_text()).group()
          elif row.select_one("th").get_text().lower() == "fiber" or row.select_one("th").get_text().lower() == "fiber (min)" or row.select_one("th").get_text().lower() == "fiber (max)" or row.select_one("th").get_text().lower() == "crude fiber (min)" or row.select_one("th").get_text().lower() == "crude fiber (max)" or row.select_one("th").get_text().lower() == "crude fiber":
            guaranteed_analysis_data["fiber"] = re.search(r"\d+\.?\d*", row.select_one("td").get_text()).group()
          elif row.select_one("th").get_text().lower() == "moisture" or row.select_one("th").get_text().lower() == "moisture (min)" or row.select_one("th").get_text().lower() == "moisture (max)" or row.select_one("th").get_text().lower() == "crude moisture (min)" or row.select_one("th").get_text().lower() == "crude moisture (max)" or row.select_one("th").get_text().lower() == "crude moisture":
            guaranteed_analysis_data["moisture"] = re.search(r"\d+\.?\d*", row.select_one("td").get_text()).group()
          elif row.select_one("th").get_text().lower() == "ash" or row.select_one("th").get_text().lower() == "ash (min)" or row.select_one("th").get_text().lower() == "ash (max)" or row.select_one("th").get_text().lower() == "crude ash (min)" or row.select_one("th").get_text().lower() == "crude ash (max)" or row.select_one("th").get_text().lower() == "crude ash":
            guaranteed_analysis_data["ash"] = re.search(r"\d+\.?\d*", row.select_one("td").get_text()).group()
          else:
            guaranteed_analysis_data['dirty_dozen'] += row.select_one("th").get_text() + ", "

        if guaranteed_analysis_data["protein"] != "":
          if guaranteed_analysis_data["ash"] == "":
            guaranteed_analysis_data["ash"] = "6.0"
        if guaranteed_analysis_data["dirty_dozen"] != "":
          guaranteed_analysis_data["dirty_dozen"] = guaranteed_analysis_data["dirty_dozen"].rstrip(", ")
        return guaranteed_analysis_data

    async def parse_product_page(self, soup: BeautifulSoup, url: str, image_url: str):
        data = {}
        guaranteed_analysis_data = {}

        try:
            product_name_section = soup.select_one(".styles_productName__klctO")
            if product_name_section:
                data["product_name"] = product_name_section.get_text().split(",")[0]
                data['packaging_size'] = product_name_section.get_text().split(",")[1].strip()
                data['container_weight'] = re.search(r"\d+\.?\d*", product_name_section.get_text().split(",")[1]).group()
            else:
                data["product_name"] = ""
                data['packaging_size'] = ""
                data['container_weight'] = ""

            brand_section = soup.select_one(".styles_root__t2C58").select_one("a")
            if brand_section:
                data["brand"] = brand_section.get_text()
            else:
                data["brand"] = ""

            teble_all = soup.select("table")
            for table in teble_all:
                tbody = table.select_one("tbody")
                if tbody is None:
                    continue
                for row in tbody.select("tr"):
                    th_element = row.select_one("th")
                    td_element = row.select_one("td")
                    if th_element and td_element and th_element.get_text().lower() == "food form":
                        data["food_category"] = td_element.get_text()

            # Find the guaranteed analysis section with null checks
            guaranteed_analysis_section = soup.select_one("#GUARANTEED_ANALYSIS-section")
            if guaranteed_analysis_section:
                table = guaranteed_analysis_section.select_one("table")
                guaranteed_analysis_data = self.get_guaranteed_analysis_data(table)
            
            description_section = soup.select_one("#KEY_BENEFITS-section")
            if description_section:
                description_ul = description_section.select_one("ul")
                if description_ul:
                    description_li = description_ul.select("li")
                    if description_li:
                        description_text = " ".join([li.get_text() for li in description_li])
                        data["description"] = description_text
                    else:
                        data["description"] = description_ul.get_text()
                else:
                    data["description"] = description_section.get_text()
            else:
                data["description"] = ""
            
            ingredients_section = soup.select_one("#INGREDIENTS-section")
            if ingredients_section:
                data["ingredients"] = ingredients_section.select("p")[0].get_text()
            else:
                data["ingredients"] = ""

            teble_all: list[BeautifulSoup] = soup.select("table")
            for table in teble_all:
                tbody = table.select_one("tbody")
                if tbody is None:
                    data["food_category"] = ""
                    continue
                for row in tbody.select("tr"):
                    th_element = row.select_one("th")
                    td_element = row.select_one("td")
                    if th_element and td_element and th_element.get_text().lower() == "food form":
                        data["food_category"] = td_element.get_text() if td_element.get_text() else ""
            
            food_storage_section = soup.select_one("#STORAGE-section")
            if food_storage_section:
              data["food_storage"] = food_storage_section.get_text()
            else:
              data["food_storage"] = ""
            
            num_servings_section = soup.select_one("#SERVINGS-section")
            if num_servings_section:
              data["num_servings"] = num_servings_section.get_text()
            else:
              data["num_servings"] = ""
            
            serving_size_section = soup.select_one("#SERVING-section")
            if serving_size_section:
              data["serving_size"] = serving_size_section.get_text()
            else:
              data["serving_size"] = ""

            shelf_life_section = soup.select_one("#SHELF_LIFE-section")
            if shelf_life_section:
              data["shelf_life"] = shelf_life_section.get_text()
            else:
              data["shelf_life"] = ""

            feeding_guidelines_section = soup.select_one("#FEEDING_INSTRUCTIONS-section")
            if feeding_guidelines_section:
                if feeding_guidelines_section.select_one("p"):
                    data["feeding_guidelines"] = feeding_guidelines_section.select_one("p").get_text()
                else:
                    data["feeding_guidelines"] = ""
            else:
                data["feeding_guidelines"] = ""

            for tag in soup.find_all(attrs={"aria-label": True}):
              label: str = tag["aria-label"]
              if label.lower().startswith("flavor:"):
                data['flavors'] = label.split("Flavor:")[-1].split(",")[0].strip()
              else:
                data['flavors'] = ""
                
        except Exception as e:
            print(f"Error parsing guaranteed analysis: {e}")

        # Set default ash if not found
        if guaranteed_analysis_data != {}:
          data["guaranteed_analysis"] = guaranteed_analysis_data
        else:
          data["guaranteed_analysis"] = {
            "protein": "",
            "fat": "",
            "fiber": "",
            "moisture": "",
            "ash": "",
            "dirty_dozen": ""
          }
        data["product_url"] = url
        data["image_url"] = image_url
        return data

    async def scrape(self):
        async with async_playwright() as p:
            # Launch with more realistic settings

            results = []

            browser = await p.chromium.launch(
                headless=False,  # Visible browser
                args=['--disable-blink-features=AutomationControlled']
            )
            
        # Choose proxy per context from PROXY_POOL to keep session affinity
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                viewport={"width": 1920, "height": 1080}
            )
            
            page = await context.new_page()
            
            try:
                # First, test with a simpler page to verify connection
                print("Testing connection to Chewy homepage...")
                try:
                    await page.goto("https://www.chewy.com/", wait_until="domcontentloaded", timeout=30000)
                    print("✓ Homepage loaded successfully!")
                    await asyncio.sleep(2)
                except Exception as e:
                    print(f"✗ Failed to load homepage: {e}")
                    print("This suggests network/blocking issues. Trying category page anyway...")
                
                # Now try the category page with more lenient settings
                print(f"\nNavigating to {CATEGORY_URL}...")
                
                # Use 'domcontentloaded' instead of 'networkidle' - much more forgiving
                # 'networkidle' waits for all network activity to stop, which may never happen
                
                await page.goto("https://www.chewy.com/b/dog-food-332", wait_until="domcontentloaded", timeout=45000)
                await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                print("✓ Homepage loaded successfully!")
                await asyncio.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

                content = await page.content()
                # Check for various issues
                content_lower = content.lower()
                if "captcha" in content_lower:
                    print("⚠️  WARNING: CAPTCHA detected!")
                elif "are you human" in content_lower or "verify you are human" in content_lower:
                    print("⚠️  WARNING: Human verification required!")
                elif "access denied" in content_lower or "forbidden" in content_lower:
                    print("⚠️  WARNING: Access denied!")
                elif "rate limit" in content_lower or "too many requests" in content_lower:
                    print("⚠️  WARNING: Rate limited!")
                else:
                    print("✓ No obvious blocking detected")

                soup = BeautifulSoup(content, "html.parser")
                current_page = "https://www.chewy.com/b/dog-food-332"
                count = 0
                while True:
                    print("Scraping page...", count)
                    for item in soup.select(".kib-product-card"):
                        link = item.select_one(".kib-product-title").get("href", "")
                        image_url = item.select_one(".kib-product-image").select_one("img").get("src", "")
                        print("link!!!:", link)
                        if link == "":
                          continue
                        if "https://www.chewy.com" not in link:
                          continue
                        await page.goto(link, wait_until="domcontentloaded")
                        await asyncio.sleep(5)
                        page.wait_for_selector(".styles_markdownTable__0uIx2", timeout=50000)
                        product_content = await page.content()
                        product_soup = BeautifulSoup(product_content, "html.parser")
                        data = await self.parse_product_page(product_soup, link, image_url)
                        print("data!!!:", data)
                        if "Bundle:" in data["product_name"].lower():
                          continue
                        if data["product_name"]:
                          results.append(data)
                    print("Navigating to first page...")
                    await page.goto(current_page, wait_until="domcontentloaded", timeout=45000)
                    await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                    await asyncio.sleep(5)
                    content = await page.content()
                    soup = BeautifulSoup(content, "html.parser")
                    next_page_button = soup.select_one(".kib-pagination-new__list-item--next").select_one("a")
                    if next_page_button and next_page_button.get("href", "") != "/b/food-332":
                        next_page_button_href = next_page_button.get("href", "")
                        if "https://www.chewy.com" not in next_page_button_href:
                          next_page_button_href = "https://www.chewy.com" + next_page_button_href
                          current_page = next_page_button_href
                        if next_page_button_href == "https://www.chewy.com/b/dog-food-332":
                          continue
                        print("Navigating to next page...")
                        await page.goto(next_page_button_href, wait_until="domcontentloaded", timeout=45000)
                        content = await page.content()
                        soup = BeautifulSoup(content, "html.parser")
                        await asyncio.sleep(5)
                    else:
                        break
                    count += 1
                
                # Uncomment below to enable full scraping
                print("\nTo enable full scraping, uncomment the code below...")
                
            except Exception as e:
                print(f"Error: {e}")
                import traceback
                traceback.print_exc()
                
                # Try to save screenshot even on error
                try:
                    await page.screenshot(path="chewy_page_error.png")
                    print("Error screenshot saved to chewy_page_error.png")
                except:
                    pass
            
            finally:
                print("Closing browser...")
                await browser.close()
                print("Done!")
                return results
