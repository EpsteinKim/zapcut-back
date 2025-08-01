import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        # 로그를 무시할 경로들
        self.ignored_paths = {
            "/api/v1/user/token/refresh",  # 토큰 리프레시 엔드포인트
            "/health",  # 헬스체크 엔드포인트
            "/api/v1/user/me",
        }

    async def dispatch(self, request: Request, call_next):
        # 무시할 경로인지 확인
        if request.url.path in self.ignored_paths:
            # 로그 없이 요청 처리
            response = await call_next(request)
            return response
        response = await call_next(request)
        return response
