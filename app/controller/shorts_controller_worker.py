from fastapi import APIRouter
from app.models.schemas import ApiResponse, ShortsVideoRequest
from app.services.video_service import VideoService

router = APIRouter(prefix="/shorts")

video_service = VideoService()


@router.post("/video")
async def create_shorts_video_worker(request: ShortsVideoRequest):
    download_url = await video_service.create_video(request)
    return ApiResponse.with_data(download_url)
