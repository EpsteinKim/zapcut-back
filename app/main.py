from fastapi import FastAPI, HTTPException
from app.core.config import get_settings
from app.api.routes import chat, shorts, test
from app.exceptions.handlers import http_exception_handler

app = FastAPI(title=get_settings().app_name)

# 예외 핸들러 등록
app.add_exception_handler(HTTPException, http_exception_handler)

# 라우터 등록
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(shorts.router, prefix="/api/v1", tags=["shorts"])
app.include_router(test.router, prefix="/api/v1", tags=["test"])

@app.get("/")
async def root():
    return {"message": "Welcome to YouTube Shorts Generator API"}