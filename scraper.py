import aiohttp
from bs4 import BeautifulSoup
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict
import logging
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AppInfo:
    name: Optional[str] = None
    link: Optional[str] = None
    platform: str = ""
    search_term: str = ""

class AppSearchManager:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    async def search_apple_store(self, session: aiohttp.ClientSession, search_term: str) -> AppInfo:
        base_url = f"https://www.apple.com/tw/search/{search_term}?src=serp"
        app_info = AppInfo(platform="Apple App Store", search_term=search_term)
        
        try:
            async with session.get(base_url, headers=self.headers) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    if product_block := soup.find('div', class_='rf-serp-product-description'):
                        if name_tag := product_block.find('h2', class_='rf-serp-productname'):
                            app_info.name = name_tag.get_text(strip=True)
                        if link_tag := product_block.find('a', href=True):
                            app_info.link = link_tag['href']
        except Exception as e:
            logger.error(f"Apple Store search error: {e}")
        
        return app_info

    async def search_google_play(self, session: aiohttp.ClientSession, search_term: str) -> AppInfo:
        base_url = f"https://play.google.com/store/search?q={search_term}&c=apps"
        app_info = AppInfo(platform="Google Play Store", search_term=search_term)
        
        try:
            async with session.get(base_url, headers=self.headers) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    if name_div := soup.select_one('div.vWM94c'):
                        app_info.name = name_div.text.strip()
                    if link_element := soup.select_one('a[href*="/store/apps/details"]'):
                        app_info.link = f"https://play.google.com{link_element['href']}"
        except Exception as e:
            logger.error(f"Google Play search error: {e}")
        
        return app_info

    async def search_all_platforms(self, search_terms: List[str]) -> List[Dict]:
        async with aiohttp.ClientSession() as session:
            tasks = []
            for term in search_terms:
                tasks.append(self.search_apple_store(session, term))
                tasks.append(self.search_google_play(session, term))
            
            results = await asyncio.gather(*tasks)
            return [asdict(result) for result in results] 