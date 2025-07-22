import os
import httpx  # requests 대신 httpx 사용
from bs4 import BeautifulSoup
from html2image import Html2Image
from app.core.config import get_settings
from app.exceptions.http_exceptions import ServerException
from app.utils.base64_decoder import decode_base64_to_bytesio
from app.utils.io_processor import IOProcessor
import uuid
from app.utils.os_processor import get_temp_dir
import io  # 추가
from playwright.async_api import async_playwright


class CrawlingService:
    def __init__(self):
        self.unlock_proxy = get_settings().unlock_proxy
        self.temp_dir = get_temp_dir("crawling_service")
        option = {
            "size": (1280, 720),
        }
        if os.getenv("ENV") == "production":
            option = {
                "browser_executable": "/usr/bin/chromium",
                "custom_flags": [
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-setuid-sandbox",
                ],
            }
        else:
            option = {
                "custom_flags": ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
            }
        self.hti = Html2Image(
            **option,
        )
        self.io_processor = IOProcessor()

    def take_screenshot(self, html_content: str, width: int = 1920, height: int = 1080) -> io.BytesIO:
        try:
            # 고유한 파일명 생성
            screenshot_id = str(uuid.uuid4())
            screenshot_filename = f"screenshot_{screenshot_id}.png"
            temp_dir = self.temp_dir
            screenshot_path = os.path.join(temp_dir, screenshot_filename)

            try:
                self.hti.size = (width, height)
                self.hti.output_path = temp_dir

                image_paths = self.hti.screenshot(
                    html_str=html_content,
                    save_as=screenshot_filename,
                )

                print(f"🔧 Html2Image 반환 경로들: {image_paths}")
                print(f"🔧 예상 파일 경로: {screenshot_path}")

                image_data = None

                if image_paths and len(image_paths) > 0:
                    actual_path = image_paths[0]
                    if os.path.isfile(actual_path):
                        with open(actual_path, "rb") as image_file:
                            image_data = image_file.read()

                if not image_data and os.path.isfile(screenshot_path):
                    with open(screenshot_path, "rb") as image_file:
                        image_data = image_file.read()

                if image_data:
                    return io.BytesIO(image_data)

                raise ServerException(f"스크린샷 파일을 찾을 수 없습니다. 디렉토리: {temp_dir}")

            finally:
                try:
                    if image_paths:
                        for path in image_paths:
                            if os.path.isfile(path):
                                os.remove(path)
                    if os.path.isfile(screenshot_path):
                        os.remove(screenshot_path)
                except Exception as cleanup_error:
                    print(f"⚠️ 파일 정리 중 에러: {cleanup_error}")

        except Exception as e:
            raise ServerException(f"Screenshot error: {e}")

    async def crawl_website_image(self, url: str) -> str:
        try:
            headers = {
                "Authorization": f"Bearer {get_settings().bright_data_api_key}",
                "Content-Type": "application/json",
            }
            data = {
                "zone": "web_unlocker1",
                "url": url,
                "format": "raw",
            }

            # 🔧 수정: requests.post 대신 httpx.AsyncClient 사용
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post("https://api.brightdata.com/request", json=data, headers=headers)

            soup = BeautifulSoup(response.text, "html.parser")
            for element in soup(["noscript"]):
                element.decompose()
            cleaned_html = str(soup)
            image_bytes = self.take_screenshot(cleaned_html)

            # S3에 업로드하고 URL 반환
            image_url = await self.io_processor.upload_file_s3(file_data=image_bytes, ext="png")

            return image_url
        except Exception as e:
            raise ServerException(f"Error: {e}")

    # 비동기 웹 크롤링 메서드
    async def crawl_website(self, url: str) -> str:
        try:
            headers = {
                "Authorization": f"Bearer {get_settings().bright_data_api_key}",
                "Content-Type": "application/json",
            }
            data = {
                "zone": "web_unlocker1",
                "url": url,
                "format": "raw",
            }
            # 🔧 수정: 비동기 HTTP 클라이언트 사용
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post("https://api.brightdata.com/request", json=data, headers=headers)
            return response.text
        except Exception as e:
            raise ServerException(f"Error: {e}")

    async def crawl_website_with_proxy(self, url: str) -> str:
        try:
            async with httpx.AsyncClient(proxy=get_settings().residential_proxy, timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.text
        except Exception as e:
            raise ServerException(f"Error: {e}")

    async def crawl_website_with_playwright(self, url: str) -> str:
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080},
                    ignore_https_errors=True,  # HTTPS 오류 무시
                    extra_http_headers={
                        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
                        "Accept-Encoding": "gzip, deflate, br",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                        "Connection": "keep-alive",
                    },
                )
                page = await context.new_page()

                await page.goto(url, wait_until="networkidle")
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
