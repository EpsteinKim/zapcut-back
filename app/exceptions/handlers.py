from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from .http_exceptions import BaseHTTPException, ServerException
import logging

logger = logging.getLogger(__name__)


async def exception_handler(request: Request, exc: Exception):
    status_code = 500
    message = "서버 내부 오류가 발생했습니다"
    data = None

    if isinstance(exc, RequestValidationError):
        status_code = 422
        error_messages = []
        for error in exc.errors():
            field = " -> ".join(str(loc) for loc in error["loc"][1:])
            msg = error["msg"]
            if field:
                error_messages.append(f"{field}: {msg}")
            else:
                error_messages.append(msg)
        message = "입력 데이터가 올바르지 않습니다"
        data = error_messages

    elif isinstance(exc, BaseHTTPException):
        status_code = exc.status_code
        message = exc.message
        data = getattr(exc, "data", None)

    elif isinstance(exc, HTTPException):
        status_code = exc.status_code
        message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)

    else:
        status_code = 500
        message = str(exc) if str(exc) else "서버 내부 오류가 발생했습니다"
        logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(status_code=status_code, content={"message": message, "data": data})
