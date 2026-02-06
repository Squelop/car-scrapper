import asyncio
from typing import List, Dict, Any
from playwright.async_api import Page
from bs4 import BeautifulSoup
from .base import BaseScraper
import re
from datetime import datetime

class OLXScraper(BaseScraper):
    def __init__(self):
        super().__init__("olx")

    async def scrape(self, playwright: AsyncPlaywright, search_url: str, limit_pages: int = 1) -> List[Dict[str, Any]]:
        results = []
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        current_url = search_url
        for page_num in range(limit_pages):
            print(f"[OLX] Scraping page {page_num + 1}: {current_url}")
            try:
                await page.goto(current_url, timeout=60000)
                await page.wait_for_load_state("networkidle")
                
                # Handle cookie consent if present
                try:
                    await page.click("button[data-cy='ad-consent-accept']", timeout=3000)
                except:
                    pass

                content = await page.content()
                soup = BeautifulSoup(content, "html.parser")
                
                # OLX uses div[data-cy="l-card"] for listing cards
                listings = soup.select("div[data-cy='l-card']")
                
                if not listings:
                    # Fallback to alternative selector
                    listings = soup.select("div.css-1sw7q4x")
                
                print(f"[OLX] Found {len(listings)} listings on page {page_num + 1}")
                
                for listing in listings:
                    try:
                        data = self.parse_listing(listing)
                        if data:
                            results.append(data)
                    except Exception as e:
                        print(f"[OLX] Error parsing listing: {e}")

                # Find next page
                next_button = soup.select_one("a[data-cy='pagination-forward']")
                if next_button and next_button.get("href"):
                    current_url = "https://www.olx.pl" + next_button["href"]
                else:
                    break
                    
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"[OLX] Error scraping page {current_url}: {e}")
                break
        
        await browser.close()
        return results

    def parse_listing(self, soup_element) -> Dict[str, Any]:
        def get_text(selector):
            el = soup_element.select_one(selector)
            return el.get_text(strip=True) if el else None

        # Link and ID
        link_tag = soup_element.select_one("a[data-cy='listing-ad-title']") or soup_element.select_one("a.css-rc5s2u")
        if not link_tag:
            return None
        
        source_url = link_tag.get("href")
        if not source_url.startswith("http"):
            source_url = "https://www.olx.pl" + source_url
            
        # Extract ID from URL
        source_id = None
        id_match = re.search(r'-ID([A-Za-z0-9]+)\.html', source_url)
        if id_match:
            source_id = id_match.group(1)
        else:
            source_id = source_url.split("/")[-1].replace(".html", "")

        # Title
        title = get_text("a[data-cy='listing-ad-title']") or get_text("h6")
        
        # Price
        price_raw = get_text("p[data-testid='ad-price']") or get_text("p.css-10b0gli")
        price = None
        currency = "PLN"
        if price_raw:
            # Remove spaces and "zł"
            price_clean = re.sub(r"[^\d]", "", price_raw)
            try:
                price = float(price_clean)
            except:
                pass
            if "€" in price_raw or "EUR" in price_raw:
                currency = "EUR"

        # Location
        location = get_text("p[data-testid='location-date']") or get_text("p.css-1a4brun")
        
        # Date posted
        date_posted = None
        if location:
            # OLX shows location and date together, e.g., "Warszawa - Dziś 12:30"
            date_match = re.search(r'(dziś|wczoraj|.*\d{2}:\d{2})', location, re.IGNORECASE)
            if date_match:
                date_posted = date_match.group(1)
        
        # Extract details from title/description
        details_text = title or ""
        
        # Parse year
        production_year = None
        year_match = re.search(r'\b(19\d{2}|20\d{2})\b', details_text)
        if year_match:
            try:
                parsed_year = int(year_match.group(1))
                if 1900 < parsed_year <= 2026:
                    production_year = parsed_year
            except:
                pass

        # Parse mileage
        mileage = None
        mileage_match = re.search(r'(\d[\d\s]*)\s*km', details_text, re.IGNORECASE)
        if mileage_match:
            try:
                mileage = int(re.sub(r'\s', '', mileage_match.group(1)))
            except:
                pass

        # Parse fuel type
        fuel_type = None
        fuel_keywords = {
            "benzyna": "Benzyna",
            "diesel": "Diesel",
            "hybryda": "Hybryda",
            "elektryczny": "Elektryczny",
            "lpg": "LPG",
            "cng": "CNG"
        }
        details_lower = details_text.lower()
        for keyword, fuel_name in fuel_keywords.items():
            if keyword in details_lower:
                fuel_type = fuel_name
                break

        # Parse engine capacity
        engine_capacity = None
        capacity_match = re.search(r'(\d[\d\s]*)\s*cm3', details_text, re.IGNORECASE)
        if capacity_match:
            try:
                engine_capacity = float(re.sub(r'\s', '', capacity_match.group(1)))
            except:
                pass

        # Parse brand and model from title
        brand = None
        model = None
        # Common Polish car brands
        brands = ["Audi", "BMW", "Mercedes", "Volkswagen", "VW", "Opel", "Ford", "Toyota", 
                  "Nissan", "Honda", "Mazda", "Renault", "Peugeot", "Citroën", "Fiat", 
                  "Skoda", "Seat", "Kia", "Hyundai", "Volvo", "Lexus", "Porsche"]
        
        for brand_name in brands:
            if brand_name.lower() in details_text.lower():
                brand = brand_name
                # Try to extract model (word after brand)
                model_match = re.search(rf'{brand_name}\s+([A-Za-z0-9\-]+)', details_text, re.IGNORECASE)
                if model_match:
                    model = model_match.group(1)
                break

        return {
            "source_id": source_id,
            "source_url": source_url,
            "platform": "olx",
            "brand": brand,
            "model": model or title,
            "price": price,
            "currency": currency,
            "production_year": production_year,
            "mileage": mileage,
            "fuel_type": fuel_type,
            "engine_capacity": engine_capacity,
            "location": location,
            "created_at_source": date_posted
        }

