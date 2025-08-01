from bs4 import BeautifulSoup
from app.exceptions.http_exceptions import ServerException
from playwright.async_api import async_playwright
import os


class CrawlingService:
    async def crawl_website_with_playwright(self, url: str) -> str:
        try:
            async with async_playwright() as p:
                if os.getenv("ENV") == "production":
                    browser = await p.chromium.launch(executable_path="/usr/bin/chromium")
                else:
                    browser = await p.chromium.launch()
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080},
                    extra_http_headers={
                        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
                        "Accept-Encoding": "gzip, deflate, br",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                        "Connection": "keep-alive",
                    },
                )
                page = await context.new_page()

                await page.goto(url, wait_until="networkidle", timeout=10000)
                html_content = await page.content()
                await browser.close()

                soup = BeautifulSoup(html_content, "html.parser")
                for tag in ["style", "script", "meta", "link", "input", "button", "iframe"]:
                    for tag_in_soup in soup.find_all(tag):
                        tag_in_soup.decompose()

                cleaned_html_content = str(soup)

                return cleaned_html_content
        except Exception as e:
            raise ServerException(str(e))
