import asyncio
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class TimeoutMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, default_timeout: int = 60):
        super().__init__(app)
        self.default_timeout = default_timeout
        # 경로별 타임아웃 설정 (초 단위)
        self.route_timeouts = {
            "/api/v1/shorts/video": 60 * 5,  # 비디오 생성 - 3분
            "/api/v1/shorts/synced-scene": 60 * 3,  # 동기화된 장면 생성 - 3분
            "/api/v1/shorts/script": 120,  # 스크립트 생성 - 2분
            "/api/v1/shorts/image": 120,  # 이미지 생성 - 2분
            "/api/v1/shorts/voice": 120,  # 음성 생성 - 2분
            "/api/v1/health": 5,  # 헬스체크 - 5초
        }

    async def dispatch(self, request: Request, call_next):
        # 요청 경로에 따른 타임아웃 설정
        timeout = self.route_timeouts.get(request.url.path, self.default_timeout)

        try:
            # 요청 처리에 타임아웃 적용
            return await asyncio.wait_for(call_next(request), timeout=timeout)
        except asyncio.TimeoutError:
            return JSONResponse(
                status_code=408, content={"message": f"요청 처리 시간이 {timeout}초를 초과했습니다.", "data": None}
            )
