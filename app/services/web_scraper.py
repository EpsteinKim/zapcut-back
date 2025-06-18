import aiohttp
import asyncio
from bs4 import BeautifulSoup
from typing import List, Dict
import logging
import time
import re


class AsyncWebScraper:
    def __init__(self, timeout: int = 60):  # 타임아웃을 30초로 단축
        self.session = None
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)

    # async enter 구문 == 비동기를 사용할때 필요한 구문
    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        # 더 빠른 처리를 위한 헤더 설정
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        self.session = aiohttp.ClientSession(timeout=timeout, headers=headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def _is_content_sufficient(self, content: str) -> bool:
        """DOM 컨텐츠가 충분한지 확인"""
        # 기본적인 HTML 구조가 있는지 확인
        if not content or len(content.strip()) < 100:
            return False

        # 주요 컨텐츠 태그들이 있는지 확인
        content_indicators = ["<body", "<main", "<article", "<div", "<p", "<h1", "<h2", "<h3"]
        return any(indicator in content.lower() for indicator in content_indicators)

    async def fetch_page_optimized(self, url: str) -> str:
        """최적화된 페이지 가져오기 - DOM 컨텐츠 로드되면 바로 처리"""
        try:
            async with self.session.get(url) as response:
                self.logger.info(f"응답 상태: {response.status} for {url}")

                if response.status != 200:
                    self.logger.warning(f"비정상 응답 상태: {response.status} for {url}")
                    return ""

                # 스트리밍으로 컨텐츠 읽기
                content = ""
                chunk_size = 8192  # 8KB씩 읽기
                content_length = 0
                max_content_length = 1024 * 1024  # 1MB 제한

                async for chunk in response.content.iter_chunked(chunk_size):
                    chunk_text = chunk.decode("utf-8", errors="ignore")
                    content += chunk_text
                    content_length += len(chunk_text)

                    # DOM 컨텐츠가 충분하고 </body> 태그를 만나면 조기 종료
                    if self._is_content_sufficient(content) and "</body>" in content.lower():
                        self.logger.info(f"DOM 컨텐츠 로드 완료, 조기 종료: {url}")
                        break

                    # 최대 크기 제한
                    if content_length > max_content_length:
                        self.logger.info(f"최대 크기 도달, 처리 중단: {url}")
                        break

                return content

        except asyncio.TimeoutError:
            raise Exception(f"페이지 로딩 시간이 초과되었습니다 ({self.timeout}초)")
        except aiohttp.ClientError as e:
            raise Exception(f"네트워크 연결 오류: {str(e)}")
        except Exception as e:
            raise Exception(f"페이지를 가져오는 중 오류가 발생했습니다: {str(e)}")

    async def fetch_page(self, url: str) -> str:
        """기존 방식 유지 (호환성)"""
        return await self.fetch_page_optimized(url)

    async def parse_page_optimized(self, html: str) -> Dict:
        """최적화된 파싱 - 주요 컨텐츠만 추출"""
        soup = BeautifulSoup(html, "html.parser")

        # 불필요한 태그들 제거
        for tag in soup.find_all(["script", "style", "noscript", "meta", "link", "nav", "footer", "header", "aside"]):
            tag.decompose()

        # 주요 컨텐츠 영역 우선 추출
        main_content = ""
        content_selectors = [
            "main",
            "article",
            '[role="main"]',
            ".content",
            ".main-content",
            ".article-content",
            ".post-content",
            "#content",
            "#main",
        ]

        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                main_content = " ".join([elem.get_text(strip=True) for elem in elements])
                break

        # 주요 컨텐츠가 없으면 전체 텍스트 사용
        if not main_content:
            main_content = soup.get_text(strip=True)

        # 제목 추출 개선
        title = ""
        title_selectors = ["h1", "title", ".title", ".headline", '[class*="title"]']
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem and title_elem.get_text(strip=True):
                title = title_elem.get_text(strip=True)
                break

        return {
            "title": title,
            "content": main_content[:5000],  # 컨텐츠 길이 제한
        }

    async def parse_page(self, html: str) -> Dict:
        """기존 방식 유지 (호환성)"""
        return await self.parse_page_optimized(html)

    async def scrape_single_page(self, url: str) -> Dict:
        try:
            html = await self.fetch_page_optimized(url)

            if not html:
                return {"title": "", "content": "", "error": "페이지 내용이 비어있습니다"}

            result = await self.parse_page_optimized(html)
            return result
        except Exception as e:
            return {"title": "", "content": "", "error": str(e)}

    async def scrape_multiple_pages(self, urls: List[str]) -> List[Dict]:
        """병렬 처리로 여러 페이지 스크래핑"""
        # 동시 처리 제한 (너무 많은 요청 방지)
        semaphore = asyncio.Semaphore(5)

        async def scrape_with_semaphore(url):
            async with semaphore:
                return await self.scrape_single_page(url)

        tasks = [scrape_with_semaphore(url) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=True)


# 사용 예시
async def main():
    urls = ["https://example.com/page1", "https://example.com/page2", "https://example.com/page3"]

    async with AsyncWebScraper() as scraper:
        results = await scraper.scrape_multiple_pages(urls)
        for result in results:
            print(result)
