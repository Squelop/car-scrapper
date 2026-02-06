import asyncio
from typing import List, Dict, Any
from playwright.async_api import AsyncPlaywright, Page
from bs4 import BeautifulSoup
from .base import BaseScraper
import re
from ..models import Listing

class OtomotoScraper(BaseScraper):
    def __init__(self):
        super().__init__("otomoto")

    async def scrape(self, playwright: AsyncPlaywright, search_url: str, limit_pages: int = 1) -> List[Dict[str, Any]]:
        results = []
        browser = await playwright.chromium.launch(headless=False) # Headless=False to avoid some detections
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        page = await context.new_page()

        current_url = search_url
        for page_num in range(limit_pages):
            print(f"Scraping page {page_num + 1}: {current_url}")
            try:
                await page.goto(current_url, timeout=60000)
                await page.wait_for_load_state("networkidle")
                
                # Handle cookie banner if present
                try:
                    await page.click("#onetrust-accept-btn-handler", timeout=5000)
                except:
                    pass

                content = await page.content()
                soup = BeautifulSoup(content, "html.parser")
                
                # Select articles
                articles = soup.select("article[data-testid='listing-ad']")
                
                for article in articles:
                    try:
                        data = self.parse_listing(article)
                        if data:
                            results.append(data)
                    except Exception as e:
                        print(f"Error parsing listing: {e}")

                # Find next page
                next_page_tag = soup.select_one("li[title='Next Page'] a")
                if next_page_tag and next_page_tag.get("href"):
                    current_url = next_page_tag["href"]
                else:
                    break
                    
                # Small delay
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"Error scraping page {current_url}: {e}")
                break
        
        await browser.close()
        return results

    def parse_listing(self, soup_element) -> Dict[str, Any]:
        # Helper to extract text
        def get_text(selector):
            el = soup_element.select_one(selector)
            return el.get_text(strip=True) if el else None

        # Link and ID
        link_tag = soup_element.select_one("h1 a") or soup_element.select_one("h2 a")
        if not link_tag:
            return None
        
        source_url = link_tag.get("href")
        source_id = source_url.split("-")[-1].split(".")[0] if "-" in source_url else source_url

        # Basic Info
        title = get_text("h1 a") or get_text("h2 a")
        
        # Price
        price_raw = get_text("h3") or get_text("div[data-testid='ad-price']") 
        price = None
        currency = "PLN"
        if price_raw:
            price_clean = re.sub(r"[^\d,]", "", price_raw).replace(",", ".")
            try:
                price = float(price_clean)
            except:
                pass
            if "EUR" in price_raw:
                currency = "EUR"

        # Parameters (Year, Mileage, Capacity, Fuel) typically in a list or specific divs
        # This part is tricky as Otomoto changes often. We'll look for specific patterns.
        # Often it is a dl/dd or div list.
        # Strategy: Iterate over all text nodes that look like parameters.
        
        details_text = soup_element.get_text(" | ", strip=True)
        
        # Heuristics for parsing details from the text blob if selectors fail
        production_year = None
        mileage = None
        fuel_type = None
        engine_capacity = None
        power = None
        brand = None
        model = None
        body_type = None
        color = None
        condition = None
        location = None
        created_at_source = None
        
        # Example: "2018 | 150 000 km | 1 998 cm3 | Benzyna"
        # We can try to parse known patterns.
        
        # Re-parse simple params usually found in specific divs if possible
        # Currently Otomoto uses specific testids for params basically.
        
        # Fallback regex
        year_match = re.search(r"(\d{4})", details_text)
        if year_match:
            try:
                parsed_year = int(year_match.group(1))
                if 1900 < parsed_year < 2026:
                    production_year = parsed_year
            except: pass

        mileage_match = re.search(r"(\d[\d\s]*)\s*km", details_text, re.IGNORECASE)
        if mileage_match:
             mileage = int(re.sub(r"\s", "", mileage_match.group(1)))

        capacity_match = re.search(r"(\d[\d\s]*)\s*cm3", details_text, re.IGNORECASE)
        if capacity_match:
             engine_capacity = float(re.sub(r"\s", "", capacity_match.group(1)))
             
        # Power
        power_match = re.search(r"(\d+)\s*KM", details_text, re.IGNORECASE)
        if power_match:
            try:
                power = int(power_match.group(1))
            except:
                pass
             
        # Fuel
        for fuel in ["Benzyna", "Diesel", "Hybryda", "Elektryczny", "LPG", "CNG"]:
            if fuel in details_text:
                fuel_type = fuel
                break

        # Brand and Model parsing from title
        brands = ["Audi", "BMW", "Mercedes", "Volkswagen", "VW", "Opel", "Ford", "Toyota", 
                  "Nissan", "Honda", "Mazda", "Renault", "Peugeot", "Citroën", "Fiat", 
                  "Skoda", "Seat", "Kia", "Hyundai", "Volvo", "Lexus", "Porsche", "Dacia",
                  "Suzuki", "Mitsubishi", "Subaru", "Jeep", "Land Rover", "Mini", "Alfa Romeo"]
        
        if title:
            for brand_name in brands:
                if brand_name.lower() in title.lower():
                    brand = brand_name
                    # Extract model (word after brand)
                    model_match = re.search(rf'{brand_name}\s+([A-Za-z0-9\-]+)', title, re.IGNORECASE)
                    if model_match:
                        model = model_match.group(1)
                    break

        # Body type
        body_types = ["Sedan", "Kombi", "SUV", "Hatchback", "Coupe", "Kabriolet", "Minivan", "Pickup"]
        for body in body_types:
            if body.lower() in details_text.lower():
                body_type = body
                break

        # Color
        colors = ["Biały", "Czarny", "Srebrny", "Szary", "Niebieski", "Czerwony", "Zielony", 
                  "Żółty", "Brązowy", "Beżowy", "Złoty", "Pomarańczowy"]
        for col in colors:
            if col.lower() in details_text.lower():
                color = col
                break

        # Condition
        details_lower = details_text.lower()
        if "uszkodzony" in details_lower or "uszkodzone" in details_lower or "po wypadku" in details_lower:
            condition = "damaged"
        elif "nowy" in details_lower or "nowe" in details_lower:
            condition = "new"
        else:
            condition = "used"

        # Location (often in a specific element)
        location = get_text("p[data-testid='location']") or get_text(".location")

        # Date posted
        date_elem = get_text("p[data-testid='date']") or get_text(".date")
        if date_elem:
            created_at_source = date_elem

        return {
            "source_id": source_id,
            "source_url": source_url,
            "platform": "otomoto",
            "brand": brand,
            "model": model or title,
            "price": price,
            "currency": currency,
            "production_year": production_year,
            "mileage": mileage,
            "fuel_type": fuel_type,
            "engine_capacity": engine_capacity,
            "power": power,
            "body_type": body_type,
            "color": color,
            "condition": condition,
            "location": location,
            "created_at_source": created_at_source
        }
