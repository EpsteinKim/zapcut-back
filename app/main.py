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

app = FastAPI(
    title="ZAPCUT API",
)

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
