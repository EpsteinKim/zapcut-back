import urllib.request
import ssl
import re
import base64

# import tempfile  # 제거
import os
import shutil
import httpx  # requests 대신 httpx 사용
from bs4 import BeautifulSoup
from html2image import Html2Image
from io import BytesIO
from app.core.config import get_settings, TEMP_DIR
from app.exceptions.http_exceptions import ServerException
from app.utils.base64_decoder import decode_base64_to_bytesio
from app.utils.io_processor import IOProcessor
import uuid
from app.utils.os_processor import get_temp_dir


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
                "custom_flags": ["--no-sandbox", "--disable-dev-shm-usage"],
            }
        else:
            option = {
                "custom_flags": ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
            }
        self.hti = Html2Image(
            **option,
        )
        self.io_processor = IOProcessor()

    def take_screenshot(self, html_content: str, width: int = 1280, height: int = 720) -> str:
        try:
            # 고유한 파일명 생성
            screenshot_id = str(uuid.uuid4())
            screenshot_filename = f"screenshot_{screenshot_id}.png"
            temp_dir = self.temp_dir
            screenshot_path = os.path.join(temp_dir, screenshot_filename)

            try:
                self.hti.size = (width, height)
                self.hti.output_path = temp_dir

                # Html2Image로 스크린샷 생성
                image_paths = self.hti.screenshot(
                    html_str=html_content,
                    save_as=screenshot_filename,
                    css_str="""
                    body { 
                        margin: 0; 
                        padding: 20px; 
                        font-family: Arial, sans-serif;
                        background-color: white;
                    }
                    """,
                )

                print(f"🔧 Html2Image 반환 경로들: {image_paths}")
                print(f"🔧 예상 파일 경로: {screenshot_path}")

                # 생성된 파일 확인 및 읽기
                if image_paths and len(image_paths) > 0:
                    # Html2Image가 반환한 첫 번째 경로 사용
                    actual_path = image_paths[0]
                    if os.path.isfile(actual_path):
                        with open(actual_path, "rb") as image_file:
                            image_data = image_file.read()
                            return base64.b64encode(image_data).decode("utf-8")

                # 예상 경로에서 파일 확인
                if os.path.isfile(screenshot_path):
                    with open(screenshot_path, "rb") as image_file:
                        image_data = image_file.read()
                        return base64.b64encode(image_data).decode("utf-8")

                # 디렉토리 내 모든 PNG 파일 확인
                for file in os.listdir(temp_dir):
                    if file.endswith(".png") and screenshot_id in file:
                        file_path = os.path.join(temp_dir, file)
                        if os.path.isfile(file_path):
                            with open(file_path, "rb") as image_file:
                                image_data = image_file.read()
                                return base64.b64encode(image_data).decode("utf-8")

                raise ServerException(f"스크린샷 파일을 찾을 수 없습니다. 디렉토리: {temp_dir}")

            finally:
                # 생성된 스크린샷 파일들 정리
                try:
                    if image_paths:
                        for path in image_paths:
                            if os.path.isfile(path):
                                os.remove(path)

                    # 예상 경로의 파일도 정리
                    if os.path.isfile(screenshot_path):
                        os.remove(screenshot_path)

                    # 해당 ID로 생성된 모든 파일 정리
                    for file in os.listdir(temp_dir):
                        if screenshot_id in file:
                            file_path = os.path.join(temp_dir, file)
                            if os.path.isfile(file_path):
                                os.remove(file_path)
                except Exception as cleanup_error:
                    print(f"⚠️ 파일 정리 중 에러: {cleanup_error}")

        except Exception as e:
            raise ServerException(f"Screenshot error: {e}")

    async def crawl_website_image(self, url: str, user_id: int = 1) -> str:
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
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post("https://api.brightdata.com/request", json=data, headers=headers)

            soup = BeautifulSoup(response.text, "html.parser")
            for element in soup(["noscript"]):
                element.decompose()
            cleaned_html = str(soup)
            screenshot_base64 = self.take_screenshot(cleaned_html)

            # base64 이미지를 BytesIO로 변환
            image_bytes = decode_base64_to_bytesio(screenshot_base64)

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
