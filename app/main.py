from fastapi import FastAPI
from app.core.config import get_settings
from app.api.routes import chat, shorts

app = FastAPI(title=get_settings().app_name)

# 라우터 등록
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(shorts.router, prefix="/api/v1", tags=["shorts"])

@app.get("/")
async def root():
    return {"message": "Welcome to YouTube Shorts Generator API hi"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 