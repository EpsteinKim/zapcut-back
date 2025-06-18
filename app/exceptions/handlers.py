from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from .http_exceptions import BaseHTTPException, ServerException


async def exception_handler(request: Request, exc: Exception):
    # HTTPException이나 ServerException이 아닌 일반 예외를 ServerException으로 변환
    if not isinstance(exc, (HTTPException, ServerException)):
        exc = ServerException(str(exc))

    # ServerException의 경우 status_code가 이미 500으로 설정되어 있을 것입니다
    return JSONResponse(
        status_code=getattr(exc, "status_code", 500),
        content={"message": str(exc), "data": getattr(exc, "data", None)},
    )
