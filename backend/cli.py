#!/usr/bin/env python3
"""
CLI for running car scrapers and saving data to JSON.
This is designed to be run by GitHub Actions or locally.
"""

import asyncio
import json
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from playwright.async_api import async_playwright

# Import scrapers
from scrapers.otomoto import OtomotoScraper
from scrapers.olx import OLXScraper
from scrapers.autoplac import AutoplacScraper


class ScraperCLI:
    def __init__(self):
        self.scrapers = {
            'otomoto': OtomotoScraper(),
            'olx': OLXScraper(),
            'autoplac': AutoplacScraper()
        }
    
    async def run_scraper(self, platform: str, search_url: str, limit_pages: int = 2) -> List[Dict[str, Any]]:
        """Run a specific scraper"""
        if platform not in self.scrapers:
            print(f"Error: Unknown platform '{platform}'")
            return []
        
        print(f"\n{'='*60}")
        print(f"Starting {platform.upper()} scraper")
        print(f"URL: {search_url}")
        print(f"Page limit: {limit_pages}")
        print(f"{'='*60}\n")
        
        async with async_playwright() as playwright:
            scraper = self.scrapers[platform]
            results = await scraper.scrape(playwright, search_url, limit_pages)
            
        print(f"\n✓ Scraped {len(results)} listings from {platform}")
        return results
    
    async def run_all_from_config(self, config_path: str, limit_pages: int = 2) -> List[Dict[str, Any]]:
        """Run all scrapers from a configuration file"""
        config_file = Path(config_path)
        if not config_file.exists():
            print(f"Error: Config file not found: {config_path}")
            return []
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        all_results = []
        
        for scraper_config in config.get('scrapers', []):
            platform = scraper_config.get('platform')
            search_url = scraper_config.get('search_url')
            pages = scraper_config.get('pages', limit_pages)
            
            if not platform or not search_url:
                print(f"Warning: Skipping invalid config entry: {scraper_config}")
                continue
            
            try:
                results = await self.run_scraper(platform, search_url, pages)
                all_results.extend(results)
            except Exception as e:
                print(f"Error scraping {platform}: {e}")
                continue
        
        return all_results
    
    def save_results(self, results: List[Dict[str, Any]], output_path: str):
        """Save results to JSON file"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing data if it exists
        existing_data = []
        if output_file.exists():
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except:
                existing_data = []
        
        # Merge new results with existing, avoiding duplicates
        existing_ids = {item.get('source_id') for item in existing_data if item.get('source_id')}
        new_results = [r for r in results if r.get('source_id') not in existing_ids]
        
        # Add scraped_at timestamp to new results
        timestamp = datetime.now().isoformat()
        for result in new_results:
            result['scraped_at'] = timestamp
        
        # Combine and save
        all_data = existing_data + new_results
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n{'='*60}")
        print(f"✓ Saved {len(new_results)} new listings to {output_path}")
        print(f"  Total listings in database: {len(all_data)}")
        print(f"{'='*60}\n")


async def main():
    parser = argparse.ArgumentParser(description='Car Scraper CLI')
    parser.add_argument('--platform', choices=['otomoto', 'olx', 'autoplac'], 
                        help='Platform to scrape')
    parser.add_argument('--url', help='Search URL to scrape')
    parser.add_argument('--config', help='Path to config JSON file')
    parser.add_argument('--output', default='frontend/public/data/listings.json',
                        help='Output JSON file path')
    parser.add_argument('--pages', type=int, default=2,
                        help='Number of pages to scrape per platform')
    parser.add_argument('--test', action='store_true',
                        help='Run test scrape with sample URLs')
    
    args = parser.parse_args()
    
    cli = ScraperCLI()
    results = []
    
    if args.test:
        # Test mode with sample URLs
        print("Running in TEST mode with sample URLs...")
        test_urls = {
            'otomoto': 'https://www.otomoto.pl/osobowe',
            'olx': 'https://www.olx.pl/motoryzacja/samochody/',
        }
        
        for platform, url in test_urls.items():
            try:
                platform_results = await cli.run_scraper(platform, url, limit_pages=1)
                results.extend(platform_results)
            except Exception as e:
                print(f"Test failed for {platform}: {e}")
    
    elif args.config:
        # Run from config file
        results = await cli.run_all_from_config(args.config, args.pages)
    
    elif args.platform and args.url:
        # Run single scraper
        results = await cli.run_scraper(args.platform, args.url, args.pages)
    
    else:
        parser.print_help()
        sys.exit(1)
    
    # Save results
    if results:
        cli.save_results(results, args.output)
    else:
        print("No results to save.")


if __name__ == '__main__':
    asyncio.run(main())
