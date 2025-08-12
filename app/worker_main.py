from fastapi import FastAPI
from app.controller import shorts_controller_worker

app = FastAPI(title="ZAPCUT Rendering Worker")

app.include_router(shorts_controller_worker.router, prefix="/api/v1", tags=["shorts_controller_worker"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "zapcut-render-worker"}
