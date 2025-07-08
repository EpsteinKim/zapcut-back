from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from .http_exceptions import BaseHTTPException, ServerException
import logging

logger = logging.getLogger(__name__)


async def exception_handler(request: Request, exc: Exception):
    """모든 예외를 message 형식으로 통일하여 처리"""

    # RequestValidationError 처리 (FastAPI의 기본 검증 오류)
    if isinstance(exc, RequestValidationError):
        # 검증 오류 메시지를 사용자 친화적으로 변환
        error_messages = []
        for error in exc.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            message = error["msg"]
            error_messages.append(f"{field}: {message}")

        message = "입력 데이터 검증 실패: " + "; ".join(error_messages)
        status_code = 422
        data = {"validation_errors": exc.errors()}

    # HTTPException 처리 (FastAPI의 기본 HTTP 예외)
    elif isinstance(exc, HTTPException):
        message = exc.detail if hasattr(exc, "detail") else str(exc)
        status_code = exc.status_code
        data = None

    # 커스텀 예외 처리
    elif isinstance(exc, BaseHTTPException):
        message = exc.message
        status_code = exc.status_code
        data = getattr(exc, "data", None)

    # 기타 모든 예외를 ServerException으로 변환
    else:
        logger.error(f"처리되지 않은 예외 발생: {type(exc).__name__}: {str(exc)}")
        message = str(exc) if str(exc) else "알 수 없는 오류가 발생했습니다"
        status_code = 500
        data = None

    # 로깅
    logger.error(f"HTTP {status_code}: {message}")

    # 응답 형식 통일: 항상 message 필드 사용
    response_content = {"message": message}
    if data is not None:
        response_content["data"] = data

    return JSONResponse(
        status_code=status_code,
        content=response_content,
    )
