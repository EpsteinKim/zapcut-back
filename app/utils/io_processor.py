import os
import uuid
import aiohttp
import tempfile
from app.exceptions.http_exceptions import ServerException
import mimetypes
import requests
from io import BytesIO


class IOProcessor:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()

    def _get_extension_from_content_type(self, content_type: str) -> str:
        if not content_type:
            return ".tmp"

        # mimetypes 모듈을 사용하여 content-type에서 확장자 추출
        ext = mimetypes.guess_extension(content_type.split(";")[0].strip())
        return ext if ext else ".tmp"

    async def download_file(self, url: str, extension: str = "") -> str:
        if os.path.isfile(url):
            return url

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise ServerException(f"Failed to download file from {url}")

                    content_type = response.headers.get("Content-Type", "")
                    # 우선순위: 1) 사용자 지정 확장자 2) Content-Type 기반 확장자
                    file_extension = extension if extension else self._get_extension_from_content_type(content_type)

                    temp_file_path = os.path.join(self.temp_dir, f"temp_file_{uuid.uuid4()}{file_extension}")

                    # audio/mpeg 또는 audio/* 타입인 경우 특별 처리
                    if content_type.startswith("audio/"):
                        content = await response.read()
                        with open(temp_file_path, "wb") as f:
                            f.write(content)
                    else:
                        with open(temp_file_path, "wb") as f:
                            async for chunk in response.content.iter_chunked(8192):
                                f.write(chunk)
            return temp_file_path
        except Exception as e:
            if "temp_file_path" in locals() and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            raise ServerException(f"File download failed: {str(e)}")

    async def upload_file(self, user_id: int, file_data: BytesIO, ext: str = "tmp") -> str:
        presigned_url = (
            f"https://ttxbh6wm8f.execute-api.ap-northeast-2.amazonaws.com/prod/upload/{user_id}/no_file.{ext}"
        )
        try:
            content_type = mimetypes.guess_type(f"file{ext}")[0] or "application/octet-stream"
            response = requests.get(presigned_url, headers={"Content-Type": content_type})
            data = response.json()
            upload_url = data["uploadUrl"]
            object_url = upload_url.split("?")[0]

            upload_response = requests.put(upload_url, headers={"Content-Type": content_type}, data=file_data)

            if upload_response.status_code != 200:
                raise ServerException("파일 업로드에 실패했습니다.")

            return object_url
        except Exception as e:
            raise ServerException(f"파일 업로드 중 오류 발생: {str(e)}")

    def __del__(self):
        if hasattr(self, "temp_dir") and os.path.exists(self.temp_dir):
            import shutil

            shutil.rmtree(self.temp_dir)
