from fastapi import APIRouter, Depends
from app.models.schemas import ApiResponse
import aiohttp
import io
from app.exceptions.http_exceptions import ServerException
from app.utils.io_processor import IOProcessor
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/proxy", dependencies=[Depends(get_current_user)])

# S3 클라이언트 초기화 및 버킷 이름 관련 코드 제거
# S3_BUCKET_NAME = "YOUR_S3_BUCKET_NAME"

io_processor = IOProcessor()


@router.get("/image")
async def get_image(image_url: str):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url, allow_redirects=True) as response:
                response.raise_for_status()  # HTTP 오류에 대한 예외 발생 (4xx 또는 5xx)

        # 파일 이름 및 확장자 결정 (io_processor의 로직을 따르도록 간소화)
        file_extension = image_url.split(".")[-1].split("?")[0].split("#")[0]
        if not file_extension or len(file_extension) > 5 or not file_extension.isalnum():
            content_type = response.headers.get("content-type")
            if content_type:
                # mimetypes 모듈 사용 (io_processor 내부에서 사용됨)
                ext = io_processor._get_extension_from_content_type(content_type)
                if ext:  # '.' 포함되어 반환되므로 제거
                    file_extension = ext[1:]
                else:
                    file_extension = "jpg"  # 기본값
            else:
                file_extension = "jpg"  # 기본값

                # S3에 이미지 업로드 (io_processor 사용)
                content = await response.read()
                image_data = io.BytesIO(content)
                s3_url = await io_processor.upload_file_s3(file_data=image_data, ext=file_extension)

                return ApiResponse.with_data(s3_url)

    except aiohttp.ClientError as e:
        raise ServerException(str(e))
    except Exception as e:
        raise ServerException(str(e))
