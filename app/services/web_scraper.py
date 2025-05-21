import aiohttp
import asyncio
from bs4 import BeautifulSoup
from typing import List, Dict

class AsyncWebScraper:
    def __init__(self):
        self.session = None

    # async enter 구문 == 비동기를 사용할때 필요한 구문
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def fetch_page(self, url: str) -> str:
        async with self.session.get(url) as response:
            return await response.text()

    async def parse_page(self, html: str) -> Dict:
        soup = BeautifulSoup(html, 'html.parser')
        
        # 불필요한 태그들 제거
        for tag in soup.find_all(['script', 'style', 'noscript', 'meta', 'link']):
            tag.decompose()
            
        return {
            'title': soup.title.string if soup.title else '',
            'content': soup.get_text(strip=True)  # strip=True로 공백 제거
        }
    async def scrape_single_page(self, url: str) -> Dict:
        html = await self.fetch_page(url)
        return await self.parse_page(html)

    async def scrape_multiple_pages(self, urls: List[str]) -> List[Dict]:
        tasks = []
        for url in urls:
            task = asyncio.create_task(self.fetch_page(url))
            tasks.append(task)
        
        pages = await asyncio.gather(*tasks)
        
        parse_tasks = []
        for page in pages:
            task = asyncio.create_task(self.parse_page(page))
            parse_tasks.append(task)
        
        return await asyncio.gather(*parse_tasks)

# 사용 예시
async def main():
    urls = [
        'https://example.com/page1',
        'https://example.com/page2',
        'https://example.com/page3'
    ]
    
    async with AsyncWebScraper() as scraper:
        results = await scraper.scrape_multiple_pages(urls)
        for result in results:
            print(result) 