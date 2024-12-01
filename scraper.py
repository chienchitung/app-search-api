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
    found: bool = False  # 添加標記來追蹤搜尋狀態

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
                            app_info.found = True
                        if link_tag := product_block.find('a', href=True):
                            app_info.link = link_tag['href']
                else:
                    logger.warning(f"Apple Store returned status {response.status} for term '{search_term}'")
        except Exception as e:
            logger.error(f"Apple Store search error for term '{search_term}': {e}")
        
        return app_info

    async def search_google_play(self, session: aiohttp.ClientSession, search_term: str) -> AppInfo:
        base_url = f"https://play.google.com/store/search?q={search_term}&c=apps&gl=TW"
        app_info = AppInfo(platform="Google Play Store", search_term=search_term)
        
        try:
            async with session.get(base_url, headers=self.headers) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    if name_div := soup.select_one('div.vWM94c'):
                        app_name = name_div.text.strip()
                        if app_name:
                            app_info.name = app_name
                            if link_element := soup.select_one('a[href*="/store/apps/details"]'):
                                app_info.link = f"https://play.google.com{link_element['href']}&hl=zh_TW"
                                app_info.found = True
                    else:
                        if name_div := soup.select_one('div.ubGTjb'):
                            app_name = name_div.text.strip()
                            if app_name:
                                app_info.name = app_name
                                if link_element := soup.select_one('a[href*="/store/apps/details"]'):
                                    app_info.link = f"https://play.google.com{link_element['href']}&hl=zh_TW"
                                    app_info.found = True                
                else:
                    logger.warning(f"Google Play returned status {response.status} for term '{search_term}'")
        except Exception as e:
            logger.error(f"Google Play search error for term '{search_term}': {e}")
        
        return app_info

    async def search_all_platforms(self, search_terms: List[str]) -> List[Dict]:
        results = []
        try:
            async with aiohttp.ClientSession() as session:
                tasks = []
                for term in search_terms:
                    # 首先搜尋 Apple Store
                    apple_result = await self.search_apple_store(session, term)
                    results.append(asdict(apple_result))
                    
                    # 使用 Apple Store 的結果來搜尋 Google Play
                    search_term_for_google = apple_result.name if apple_result.found else term
                    google_result = await self.search_google_play(session, search_term_for_google)
                    results.append(asdict(google_result))
        except Exception as e:
            logger.error(f"Error in search_all_platforms: {e}")
        
        return results
