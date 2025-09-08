import aiohttp
from fastapi import APIRouter
from app.exceptions.http_exceptions import ServerException
from app.utils.io_processor import IOProcessor
from app.utils.video.audio_processor import AudioProcessor
from app.services.openai_service import OpenAIService
from app.core.service_locator import get_openai_service
from fastapi import Depends
from app.core.dependencies import get_current_user_info, get_services, Services
from app.models.schemas import ApiResponse

router = APIRouter(prefix="/test", dependencies=[Depends(get_current_user_info)])

io_processor = IOProcessor()
audio_processor = AudioProcessor()


@router.get("/test")
async def test(url: str, services: Services = Depends(get_services)):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, allow_redirects=True) as response:
                response.raise_for_status()  # HTTP 오류에 대한 예외 발생 (4xx 또는 5xx)

        # 파일 이름 및 확장자 결정 (io_processor의 로직을 따르도록 간소화)
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
