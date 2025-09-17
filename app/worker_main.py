from fastapi import FastAPI
from pydantic import BaseModel
from app.models.schemas import ShortsVideoRequest
from app.services.video_service import VideoService

app = FastAPI(title="ZAPCUT Video Renderer")


@app.get("/")
async def root():
    return {"message": "ZAPCUT Video Renderer is running", "status": "healthy"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "zapcut-video-renderer"}


# http://k8s-zapcutre-zapcutre-ebac054c8b-f777e591bcf6d2e8.elb.ap-northeast-2.amazonaws.com
@app.post("/api/v1/shorts/video")
async def create_shorts_video(request: ShortsVideoRequest):
    service = VideoService()
    download_url = await service.create_video(request)
    return {"data": download_url}
