import os

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.controller import shortsController, test
from app.exceptions.handlers import exception_handler


app = FastAPI(title=get_settings().app_name)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 서빙 설정
app.mount("/static", StaticFiles(directory="static"), name="static")

# 예외 핸들러 등록
app.add_exception_handler(Exception, exception_handler)
app.add_exception_handler(RequestValidationError, exception_handler)

# 라우터 등록
app.include_router(shortsController.router, prefix="/api/v1", tags=["shortsController"])
app.include_router(test.router, prefix="/api/v1", tags=["test"])


@app.get("/")
async def root():
    return FileResponse("static/index.html")
