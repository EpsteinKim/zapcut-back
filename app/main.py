import os

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

from fastapi import FastAPI
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

app = FastAPI(
    title="ZAPCUT API",
)

# CORS 미들웨어
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 통합 예외 핸들러 등록 (모든 예외를 message 형식으로 처리)
app.add_exception_handler(Exception, exception_handler)

# 라우터 등록
app.include_router(shortsController.router, prefix="/api/v1", tags=["shortsController"])
app.include_router(crawlingController.router, prefix="/api/v1", tags=["crawlingController"])

# 로거 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 종료 시 정리 핸들러 초기화
cleanup_handler = initialize_cleanup_handler(TEMP_DIR)
logger.info("🚀 ZAPCUT API 서비스 시작")


@app.get("/")
async def root():
    return {"message": "ZAPCUT API is running", "status": "healthy"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "zapcut-api"}


@app.get("/deployment-info")
async def get_deployment_info():
    """배포 정보 및 환경 정보를 반환합니다."""
    try:
        # 환경 변수에서 배포 정보 가져오기
        deployment_date = os.getenv("DEPLOYMENT_DATE", "Unknown")
        environment = os.getenv("ENVIRONMENT", "Unknown")

        # 서버 시작 시간 (프로세스 시작 시간 추정)
        import psutil
        import os

        try:
            process = psutil.Process(os.getpid())
            start_time = datetime.fromtimestamp(process.create_time())
            server_start_time = start_time.strftime("%Y-%m-%d %H:%M:%S")
        except:
            server_start_time = "Unknown"

        return {
            "service": "zapcut-api",
            "status": "healthy",
            "deployment_info": {
                "deployment_date": deployment_date,
                "environment": environment,
                "server_start_time": server_start_time,
            },
            "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "server_info": {"python_version": os.sys.version, "pid": os.getpid()},
        }
    except Exception as e:
        return {
            "service": "zapcut-api",
            "status": "healthy",
            "deployment_info": {
                "error": str(e),
                "deployment_date": "Unknown",
                "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
        }
