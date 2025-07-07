import aiohttp
import asyncio
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Union
import logging
import time
import requests
import ssl
import random
from urllib.parse import quote, urlparse, urlunparse
from app.core.config import get_settings
import urllib.request


class AsyncWebScraper:
    def __init__(
        self,
        timeout: int = 60,
        delay_range: tuple = (1, 3),  # 요청 간 랜덤 딜레이 (초)
        max_retries: int = 3,  # 재시도 횟수
        max_content_size: int = 10 * 1024 * 1024,  # 최대 컨텐츠 크기 (기본 10MB)
        max_chunk_size: int = 1024 * 1024,  # 스트리밍 시 최대 누적 크기 (기본 1MB)
    ):

        self.session = None
        self.timeout = timeout
        self.delay_range = delay_range
        self.max_retries = max_retries
        self.max_content_size = max_content_size
        self.max_chunk_size = max_chunk_size
        self.last_request_time = 0

        settings = get_settings()
        self.proxy_config = {"http": settings.proxy, "https": settings.proxy}
        self.logger = logging.getLogger(__name__)

    # async enter 구문 == 비동기를 사용할때 필요한 구문
    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        # 더 현실적인 브라우저 헤더 설정 (429 에러 방지)
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }

        # 프록시 설정이 있는 경우 커넥터 생성
        connector = None
        if self.proxy_config:
            connector = aiohttp.TCPConnector(
                limit=10,  # 동시 연결 수 제한
                limit_per_host=2,  # 호스트당 연결 수 제한
                ttl_dns_cache=300,  # DNS 캐시 유지 시간
                use_dns_cache=True,
            )

        self.session = aiohttp.ClientSession(
            timeout=timeout, headers=headers, connector=connector, cookie_jar=aiohttp.CookieJar()  # 쿠키 유지
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def _wait_between_requests(self):
        """요청 간 랜덤 딜레이 적용 (429 에러 방지)"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.delay_range[0]:
            delay = random.uniform(self.delay_range[0], self.delay_range[1])
            await asyncio.sleep(delay)

        self.last_request_time = time.time()

    def _is_content_sufficient(self, content: str) -> bool:
        """DOM 컨텐츠가 충분한지 확인"""
        # 기본적인 HTML 구조가 있는지 확인
        if not content or len(content.strip()) < 100:
            return False

        # 주요 컨텐츠 태그들이 있는지 확인
        content_indicators = ["<body", "<main", "<article", "<div", "<p", "<h1", "<h2", "<h3"]
        return any(indicator in content.lower() for indicator in content_indicators)

    async def fetch_page_optimized(self, url: str) -> str:
        """최적화된 페이지 가져오기 - 429 에러 방지 및 재시도 로직"""

        for attempt in range(self.max_retries + 1):
            try:
                # 요청 간 딜레이 적용
                if attempt > 0:
                    delay = random.uniform(2**attempt, 2 ** (attempt + 1))  # 지수 백오프
                    self.logger.info(f"재시도 {attempt}/{self.max_retries}, {delay:.1f}초 대기 중...")
                    await asyncio.sleep(delay)
                else:
                    await self._wait_between_requests()

                # 프록시 설정을 요청에 추가
                request_kwargs = {}
                if self.proxy_config:
                    # URL 스키마에 따라 적절한 프록시 선택
                    if url.startswith("https://") and "https" in self.proxy_config:
                        request_kwargs["proxy"] = self.proxy_config["https"]
                    elif url.startswith("http://") and "http" in self.proxy_config:
                        request_kwargs["proxy"] = self.proxy_config["http"]
                    elif "http" in self.proxy_config:  # 기본값
                        request_kwargs["proxy"] = self.proxy_config["http"]

                # Referer 헤더 추가 (더 자연스러운 요청)
                extra_headers = {}
                if attempt > 0:  # 재시도 시에는 다른 헤더 사용
                    extra_headers.update(
                        {
                            "Referer": "https://www.google.com/",
                            "Sec-CH-UA": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                            "Sec-CH-UA-Mobile": "?0",
                            "Sec-CH-UA-Platform": '"macOS"',
                        }
                    )

                async with self.session.get(url, headers=extra_headers, **request_kwargs) as response:
                    self.logger.info(
                        f"시도 {attempt + 1}/{self.max_retries + 1} - 응답 상태: {response.status} for {url}"
                    )

                    if self.proxy_config:
                        self.logger.info(f"프록시 사용: {request_kwargs.get('proxy', 'N/A')}")

                    # Content-Length 헤더 확인으로 미리 크기 체크
                    content_length_header = response.headers.get("Content-Length")
                    if content_length_header:
                        try:
                            expected_size = int(content_length_header)
                            if expected_size > self.max_content_size:
                                self.logger.warning(
                                    f"응답 크기가 너무 큼: {expected_size} bytes, 최대: {self.max_content_size} bytes"
                                )
                                return ""
                            else:
                                self.logger.info(f"예상 응답 크기: {expected_size} bytes")
                        except ValueError:
                            pass

                    # 429 에러 처리
                    if response.status == 429:
                        retry_after = response.headers.get("Retry-After")
                        if retry_after:
                            try:
                                wait_time = int(retry_after)
                                self.logger.warning(f"429 에러 - Retry-After: {wait_time}초")
                                if attempt < self.max_retries:
                                    await asyncio.sleep(wait_time)
                                    continue
                            except ValueError:
                                pass

                        if attempt < self.max_retries:
                            self.logger.warning(f"429 에러 - 재시도 {attempt + 1}/{self.max_retries}")
                            continue
                        else:
                            raise Exception(f"요청이 너무 많습니다 (429). 잠시 후 다시 시도해주세요.")

                    if response.status != 200:
                        if attempt < self.max_retries and response.status in [500, 502, 503, 504]:
                            self.logger.warning(f"서버 에러 {response.status} - 재시도 중...")
                            continue
                        else:
                            self.logger.warning(f"비정상 응답 상태: {response.status} for {url}")
                            return ""

                    # 스트리밍으로 컨텐츠 읽기
                    content = ""
                    chunk_size = 8192  # 8KB씩 읽기
                    content_length = 0

                    async for chunk in response.content.iter_chunked(chunk_size):
                        chunk_text = chunk.decode("utf-8", errors="ignore")
                        content += chunk_text
                        content_length += len(chunk_text)

                        # DOM 컨텐츠가 충분하고 </body> 태그를 만나면 조기 종료
                        if self._is_content_sufficient(content) and "</body>" in content.lower():
                            self.logger.info(f"DOM 컨텐츠 로드 완료, 조기 종료: {url}")
                            break

                        # 최대 크기 제한 (스트리밍 중 누적 크기)
                        if content_length > self.max_chunk_size:
                            self.logger.info(f"스트리밍 최대 크기 도달, 처리 중단: {url} ({content_length} bytes)")
                            break

                    return content

            except asyncio.TimeoutError:
                if attempt < self.max_retries:
                    self.logger.warning(f"타임아웃 - 재시도 {attempt + 1}/{self.max_retries}")
                    continue
                else:
                    raise Exception(f"페이지 로딩 시간이 초과되었습니다 ({self.timeout}초)")
            except aiohttp.ClientError as e:
                if attempt < self.max_retries:
                    self.logger.warning(f"클라이언트 에러 - 재시도 {attempt + 1}/{self.max_retries}: {str(e)}")
                    continue
                else:
                    raise Exception(f"네트워크 연결 오류: {str(e)}")
            except Exception as e:
                if attempt < self.max_retries and "429" not in str(e):
                    self.logger.warning(f"예상치 못한 에러 - 재시도 {attempt + 1}/{self.max_retries}: {str(e)}")
                    continue
                else:
                    raise Exception(f"페이지를 가져오는 중 오류가 발생했습니다: {str(e)}")

        return ""  # 모든 재시도 실패

    async def fetch_page(self, url: str) -> str:
        """기존 방식 유지 (호환성)"""
        return await self.fetch_page_optimized(url)

    async def parse_page_optimized(self, html: str) -> str:
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

        return main_content[:5000]  # 컨텐츠 길이 제한

    async def parse_page(self, html: str) -> str:
        """기존 방식 유지 (호환성)"""
        return await self.parse_page_optimized(html)

    async def scrape_single_page(self, url: str) -> str:
        try:
            html = await self.fetch_page_optimized(url)

            if not html:
                return ""

            content = await self.parse_page_optimized(html)
            return content
        except Exception as e:
            self.logger.error(f"스크래핑 오류 {url}: {str(e)}")
            return ""


# 사용 예시
async def main():
    url = "https://example.com"

    # 기본 사용법 (config에서 자동으로 프록시 설정 가져옴)
    async with AsyncWebScraper() as scraper:
        content = await scraper.scrape_single_page(url)
        print(content)


async def simple_scrape_single_page(url: str) -> str:
    proxy = "http://brd-customer-hl_e9788747-zone-web_unlocker1:5y0rhncn8kb5@brd.superproxy.io:33335"

    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({"https": proxy, "http": proxy}),
        urllib.request.HTTPSHandler(context=ssl._create_unverified_context()),
    )

    try:
        print(opener.open(url).read().decode())
    except Exception as e:
        print(f"Error: {e}")
