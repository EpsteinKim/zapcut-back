import os

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from app.core.config import TEMP_DIR
from app.utils.cleanup_handler import initialize_cleanup_handler

import logging
from app.controller import (
    shorts_controller,
    crawling_controller,
    proxy_controller,
    test_controller,
    user_controller,
    verification_controller,
    pixabay_controller,
    admin_controller,
)
from app.exceptions.handlers import exception_handler
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.timeout_middleware import TimeoutMiddleware
from app.middleware.logging_middleware import LoggingMiddleware
from app.core.database import create_db_and_tables


app = FastAPI(
    title="ZAPCUT API",
)


# 애플리케이션 시작 시 데이터베이스 테이블 생성
@app.on_event("startup")
def on_startup():
    create_db_and_tables()


# 로깅 미들웨어 추가 (특정 경로 로그 무시)
app.add_middleware(LoggingMiddleware)

# 타임아웃 미들웨어 추가 (1분 = 60초)
app.add_middleware(TimeoutMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://zapcut.io", "https://api.zapcut.io", "http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.add_exception_handler(RequestValidationError, exception_handler)
app.add_exception_handler(HTTPException, exception_handler)
app.add_exception_handler(Exception, exception_handler)


app.include_router(pixabay_controller.router, prefix="/api/v1", tags=["pixabay_controller"])
app.include_router(shorts_controller.router, prefix="/api/v1", tags=["shorts_controller"])
app.include_router(crawling_controller.router, prefix="/api/v1", tags=["crawling_controller"])
app.include_router(proxy_controller.router, prefix="/api/v1", tags=["proxy_controller"])
app.include_router(test_controller.router, prefix="/api/v1", tags=["test_controller"])
app.include_router(user_controller.router, prefix="/api/v1", tags=["user_controller"])
app.include_router(verification_controller.router, prefix="/api/v1", tags=["verification_controller"])
app.include_router(admin_controller.router, prefix="/api/v1", tags=["admin_controller"])

# 로거 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

cleanup_handler = initialize_cleanup_handler(TEMP_DIR, auto_cleanup_interval=60 * 5, max_file_age_seconds=60 * 20)
logger.info("🚀 ZAPCUT API 서비스 시작")


@app.get("/")
async def root():
    return {"message": "ZAPCUT API is running", "status": "healthy"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "zapcut-api"}
