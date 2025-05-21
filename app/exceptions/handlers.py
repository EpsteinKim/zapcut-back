from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from .http_exceptions import BaseHTTPException

async def http_exception_handler(request: Request, exc: HTTPException):
    # BaseHTTPException인 경우 message 사용, 아닌 경우 detail 사용
    error_message = getattr(exc, 'message', exc.detail)
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": error_message,
            "data": getattr(exc, 'data', None)
        }
    ) 