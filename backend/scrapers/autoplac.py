import asyncio
from typing import List, Dict, Any
from playwright.async_api import Page
from bs4 import BeautifulSoup
from .base import BaseScraper
import re

class AutoplacScraper(BaseScraper):
    def __init__(self):
        super().__init__("autoplac")

    async def scrape(self, playwright, search_url: str, limit_pages: int = 1) -> List[Dict[str, Any]]:
        results = []
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        current_url = search_url
        for page_num in range(limit_pages):
            print(f"[Autoplac] Scraping page {page_num + 1}: {current_url}")
            try:
                await page.goto(current_url, timeout=60000)
                await page.wait_for_load_state("networkidle")
                
                # Handle cookie consent
                try:
                    await page.click("button.cookie-accept", timeout=3000)
                except:
                    pass

                content = await page.content()
                soup = BeautifulSoup(content, "html.parser")
                
                # Autoplac uses article.offer-item or similar
                listings = soup.select("article.offer-item, div.offer-item, div.listing-item")
                
                if not listings:
                    # Try alternative selectors
                    listings = soup.select("div[data-offer-id]")
                
                print(f"[Autoplac] Found {len(listings)} listings on page {page_num + 1}")
                
                for listing in listings:
                    try:
                        data = self.parse_listing(listing)
                        if data:
                            results.append(data)
                    except Exception as e:
                        print(f"[Autoplac] Error parsing listing: {e}")

                # Find next page
                next_button = soup.select_one("a.next-page, a[rel='next'], li.next a")
                if next_button and next_button.get("href"):
                    next_url = next_button["href"]
                    if not next_url.startswith("http"):
                        current_url = "https://www.autoplac.pl" + next_url
                    else:
                        current_url = next_url
                else:
                    break
                    
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"[Autoplac] Error scraping page {current_url}: {e}")
                break
        
        await browser.close()
        return results

    def parse_listing(self, soup_element) -> Dict[str, Any]:
        def get_text(selector):
            el = soup_element.select_one(selector)
            return el.get_text(strip=True) if el else None

        # Link and ID
        link_tag = soup_element.select_one("a.offer-link, a[href*='/oferta/'], h3 a, h2 a")
        if not link_tag:
            return None
        
        source_url = link_tag.get("href")
        if not source_url.startswith("http"):
            source_url = "https://www.autoplac.pl" + source_url
            
        # Extract ID from URL or data attribute
        source_id = soup_element.get("data-offer-id")
        if not source_id:
            id_match = re.search(r'/oferta/(\d+)', source_url)
            if id_match:
                source_id = id_match.group(1)
            else:
                source_id = source_url.split("/")[-1]

        # Title
        title = get_text("h3.offer-title, h2.offer-title, .offer-name")
        
        # Price
        price_raw = get_text(".offer-price, .price, span.price-value")
        price = None
        currency = "PLN"
        if price_raw:
            price_clean = re.sub(r"[^\d]", "", price_raw)
            try:
                price = float(price_clean)
            except:
                pass
            if "€" in price_raw or "EUR" in price_raw:
                currency = "EUR"

        # Details - Autoplac typically shows details in a list
        details_text = soup_element.get_text(" | ", strip=True)
        
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

        # Parse power
        power = None
        power_match = re.search(r'(\d+)\s*KM', details_text, re.IGNORECASE)
        if power_match:
            try:
                power = int(power_match.group(1))
            except:
                pass

        # Parse brand and model
        brand = None
        model = None
        brands = ["Audi", "BMW", "Mercedes", "Volkswagen", "VW", "Opel", "Ford", "Toyota", 
                  "Nissan", "Honda", "Mazda", "Renault", "Peugeot", "Citroën", "Fiat", 
                  "Skoda", "Seat", "Kia", "Hyundai", "Volvo", "Lexus", "Porsche"]
        
        if title:
            for brand_name in brands:
                if brand_name.lower() in title.lower():
                    brand = brand_name
                    model_match = re.search(rf'{brand_name}\s+([A-Za-z0-9\-]+)', title, re.IGNORECASE)
                    if model_match:
                        model = model_match.group(1)
                    break

        # Location
        location = get_text(".offer-location, .location")

        # Condition
        condition = None
        if "uszkodzony" in details_lower or "uszkodzone" in details_lower:
            condition = "damaged"
        elif "nowy" in details_lower or "nowe" in details_lower:
            condition = "new"
        else:
            condition = "used"

        return {
            "source_id": source_id,
            "source_url": source_url,
            "platform": "autoplac",
            "brand": brand,
            "model": model or title,
            "price": price,
            "currency": currency,
            "production_year": production_year,
            "mileage": mileage,
            "fuel_type": fuel_type,
            "engine_capacity": engine_capacity,
            "power": power,
            "location": location,
            "condition": condition
        }

