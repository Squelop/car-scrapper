from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from .database import engine, Base, get_db
from .models import Listing
from .scrapers.otomoto import OtomotoScraper
from playwright.async_api import async_playwright
import uvicorn

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Car Scraper API is running"}

@app.get("/listings")
def get_listings(
    skip: int = 0, 
    limit: int = 100, 
    min_price: Optional[float] = None, 
    max_price: Optional[float] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Listing)
    if min_price:
        query = query.filter(Listing.price >= min_price)
    if max_price:
        query = query.filter(Listing.price <= max_price)
    
    return query.offset(skip).limit(limit).all()

async def run_scraper_task(search_url: str):
    # This should be more robust in production, creating separate sessions
    async with async_playwright() as p:
        scraper = OtomotoScraper()
        data = await scraper.scrape(p, search_url, limit_pages=2)
        
        # Save to DB
        db = next(get_db())
        try:
            for item in data:
                # Check duplication
                exists = db.query(Listing).filter(Listing.source_id == item["source_id"]).first()
                if not exists:
                    listing = Listing(**item)
                    db.add(listing)
                else:
                    # Update price/data?
                    pass
            db.commit()
        except Exception as e:
            print(f"DB Error: {e}")
        finally:
            db.close()

@app.post("/scrape")
async def trigger_scrape(search_url: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_scraper_task, search_url)
    return {"message": "Scraping started", "url": search_url}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
