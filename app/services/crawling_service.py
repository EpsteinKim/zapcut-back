import urllib.request
import ssl
import re
import base64
import tempfile
import os
import requests
from bs4 import BeautifulSoup
from html2image import Html2Image
from io import BytesIO
from app.core.config import get_settings
from app.exceptions.http_exceptions import ServerException
from app.utils.base64_decoder import decode_base64_to_bytesio
from app.utils.io_processor import IOProcessor


class CrawlingService:
    def __init__(self):
        self.unlock_proxy = get_settings().unlock_proxy
        self.hti = Html2Image(size=(1280, 720))
        self.io_processor = IOProcessor()

    def take_screenshot(self, html_content: str, width: int = 1280, height: int = 720) -> str:
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                self.hti.size = (width, height)
                self.hti.output_path = temp_dir
                image_paths = self.hti.screenshot(
                    html_str=html_content,
                    save_as="screenshot.png",
                    css_str="""
                    body { 
                        margin: 0; 
                        padding: 20px; 
                        font-family: Arial, sans-serif;
                        background-color: white;
                    }
                    """,
                )
                if image_paths and len(image_paths) > 0:
                    image_path = image_paths[0]
                    with open(image_path, "rb") as image_file:
                        image_data = image_file.read()
                        return base64.b64encode(image_data).decode("utf-8")
                else:
                    raise ServerException("스크린샷 생성에 실패했습니다.")
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
            response = requests.post("https://api.brightdata.com/request", json=data, headers=headers)
            soup = BeautifulSoup(response.text, "html.parser")
            for element in soup(["noscript", "script"]):
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
