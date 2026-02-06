from abc import ABC, abstractmethod
from typing import List, Dict, Any
from playwright.async_api import Page, AsyncPlaywright

class BaseScraper(ABC):
    def __init__(self, platform_name: str):
        self.platform_name = platform_name

    @abstractmethod
    async def scrape(self, playwright: AsyncPlaywright, search_url: str, limit_pages: int = 1) -> List[Dict[str, Any]]:
        """
        Scrapes listings from a given search URL.
        """
        pass

    @abstractmethod
    def parse_listing(self, html_content: str) -> Dict[str, Any]:
        """
        Parses a single listing HTML block/page into a dictionary.
        """
        pass
