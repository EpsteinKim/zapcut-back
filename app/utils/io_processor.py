import os
import uuid
import aiohttp

# import tempfile  # 제거
from app.exceptions.http_exceptions import ServerException
import mimetypes
import requests
from io import BytesIO
from PIL import Image
from app.utils.os_processor import get_temp_dir

# from app.core.config import get_settings

# settings = get_settings()


class IOProcessor:
    def __init__(self):
        # self.temp_dir = tempfile.mkdtemp()  # 기존 코드
        self.temp_dir = get_temp_dir("io_processor")

    async def download_file(self, url: str) -> str:
        if os.path.isfile(url):
            return url

        temp_file_path = None
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise ServerException(f"Failed to download file from {url}, status: {response.status}")

                    content_type = response.headers.get("Content-Type", "")
                    content_length = response.headers.get("Content-Length")
                    expected_size = int(content_length) if content_length else None

                    url_ext = url.split(".")[-1].split("?")[0].split("#")[0]
                    if len(url_ext) <= 5 and url_ext.isalnum():
                        file_extension = f".{url_ext}"
                    else:
                        file_extension = self._get_extension_from_content_type(content_type)

                    temp_file_path = os.path.join(self.temp_dir, f"temp_file_{uuid.uuid4()}{file_extension}")

                    with open(temp_file_path, "wb") as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)

                    # 파일 무결성 검증
                    if not self._verify_file_integrity(temp_file_path, expected_size, content_type):
                        if os.path.exists(temp_file_path):
                            os.remove(temp_file_path)
                        raise ServerException(f"다운로드된 파일이 손상되었거나 올바르지 않습니다: {url}")

                    return temp_file_path

        except Exception as e:
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            raise ServerException(f"File download failed: {str(e)}")

    async def upload_file_s3(self, file_data: BytesIO = None, file_path: str = None, ext: str = "tmp") -> str:
        if file_data is None and file_path is None:
            raise ServerException("file_data 또는 file_path 중 하나는 반드시 제공되어야 합니다.")

        if file_path is not None:
            try:
                with open(file_path, "rb") as f:
                    file_data = BytesIO(f.read())
            except Exception as e:
                raise ServerException(f"파일을 읽는 중 오류 발생: {str(e)}")

        presigned_url = (
            f"https://j5tz0t1es8.execute-api.ap-northeast-2.amazonaws.com/prod/upload/expired_plan/no_file.{ext}"
        )
        try:
            content_type = mimetypes.guess_type(f"file.{ext}")[0] or "application/octet-stream"

            # Get presigned URL and upload file using single session
            async with aiohttp.ClientSession() as session:
                # Get presigned URL
                async with session.get(presigned_url, headers={"Content-Type": content_type}) as response:
                    if response.status != 200:
                        raise ServerException("Failed to get presigned URL")
                    data = await response.json()

                upload_url = data["uploadUrl"]
                object_url = upload_url.split("?")[0].replace("s3.ap-northeast-2.amazonaws.com/", "")

                # Upload file
                file_data.seek(0)  # Reset file pointer to beginning
                file_content = file_data.read()  # Read entire content into memory
                file_data.close()  # Explicitly close the BytesIO object after reading

                async with session.put(
                    upload_url, headers={"Content-Type": content_type}, data=file_content
                ) as upload_response:
                    if upload_response.status != 200:
                        raise ServerException("파일 업로드에 실패했습니다.")

            return object_url
        except Exception as e:

            raise ServerException(f"파일 업로드 중 오류 발생: {str(e)}")

    def _get_extension_from_content_type(self, content_type: str) -> str:
        if not content_type:
            return ".tmp"

        # mimetypes 모듈을 사용하여 content-type에서 확장자 추출
        ext = mimetypes.guess_extension(content_type.split(";")[0].strip())
        return ext if ext else ".tmp"

    def _verify_file_integrity(self, file_path: str, expected_size: int = None, content_type: str = None) -> bool:
        """다운로드된 파일의 무결성을 검증"""
        try:
            if not os.path.exists(file_path):
                return False

            file_size = os.path.getsize(file_path)

            # 파일이 비어있는지 확인
            if file_size == 0:
                return False

            # Content-Length와 실제 파일 크기 비교
            if expected_size and abs(file_size - expected_size) > 100:  # 100바이트 오차 허용
                return False

            # 파일 시그니처 확인
            with open(file_path, "rb") as f:
                header = f.read(20)

                # 이미지 파일인 경우 추가 검증
                if content_type and content_type.startswith("image/"):
                    return self._verify_image_file(file_path, header)

                # 오디오 파일인 경우
                elif content_type and content_type.startswith("audio/"):
                    return self._verify_audio_file(header)

                # 일반적인 파일 시그니처 확인
                return self._verify_file_signature(header)

        except Exception as e:
            return False

    def _verify_image_file(self, file_path: str, header: bytes) -> bool:
        # 이미지 파일 시그니처 확인
        image_signatures = [
            b"\xff\xd8\xff",  # JPEG
            b"\x89PNG\r\n\x1a\n",  # PNG
            b"GIF87a",  # GIF87a
            b"GIF89a",  # GIF89a
            b"RIFF",  # WebP (RIFF 뒤에 WEBP가 옴)
            b"\x00\x00\x01\x00",  # ICO
        ]

        has_valid_signature = any(header.startswith(sig) for sig in image_signatures)
        if not has_valid_signature:
            return False

        # PIL로 이미지 검증
        try:
            with Image.open(file_path) as img:
                img.verify()  # 이미지 무결성 검증
                return True
        except Exception as e:
            return False

    def _verify_audio_file(self, header: bytes) -> bool:
        audio_signatures = [
            b"ID3",  # MP3 with ID3
            b"\xff\xfb",  # MP3
            b"\xff\xf3",  # MP3
            b"\xff\xf2",  # MP3
            b"RIFF",  # WAV, WEBM
            b"fLaC",  # FLAC
            b"OggS",  # OGG
        ]

        return any(header.startswith(sig) for sig in audio_signatures)

    def _verify_file_signature(self, header: bytes) -> bool:
        html_indicators = [b"<!DOCTYPE", b"<html", b"<HTML", b"<head", b"<HEAD"]
        if any(header.lower().startswith(indicator.lower()) for indicator in html_indicators):
            return False

        return True
