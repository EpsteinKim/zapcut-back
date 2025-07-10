import os

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.core.config import get_settings, TEMP_DIR
from app.utils.cleanup_handler import initialize_cleanup_handler

import logging
from app.controller import shortsController, crawlingController
from app.exceptions.handlers import exception_handler
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import json
import asyncio
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


# 타임아웃 미들웨어 클래스
class TimeoutMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, timeout: int = 60):
        super().__init__(app)
        self.timeout = timeout

    async def dispatch(self, request: Request, call_next):
        try:
            # 요청 처리에 타임아웃 적용
            return await asyncio.wait_for(call_next(request), timeout=self.timeout)
        except asyncio.TimeoutError:
            return JSONResponse(
                status_code=408, content={"message": f"요청 처리 시간이 {self.timeout}초를 초과했습니다.", "data": None}
            )


app = FastAPI(
    title="ZAPCUT API",
)

# 타임아웃 미들웨어 추가 (1분 = 60초)
app.add_middleware(TimeoutMiddleware, timeout=120)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://zapcut.io", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.add_exception_handler(RequestValidationError, exception_handler)
app.add_exception_handler(HTTPException, exception_handler)
app.add_exception_handler(Exception, exception_handler)

app.include_router(shortsController.router, prefix="/api/v1", tags=["shortsController"])
app.include_router(crawlingController.router, prefix="/api/v1", tags=["crawlingController"])

# 로거 설정
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

cleanup_handler = initialize_cleanup_handler(TEMP_DIR, auto_cleanup_interval=3600, max_file_age_hours=24)
logger.info("🚀 ZAPCUT API 서비스 시작")


@app.get("/")
async def root():
    return {"message": "ZAPCUT API is running", "status": "healthy"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "zapcut-api"}
