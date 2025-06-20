from fastapi import APIRouter, Query, Response, Depends
from app.models.schemas import (
    Response,
    ShortsSceneRequest,
    CombineShortsSceneRequest,
    ShortsScriptRequest,
    ShortsVideoRequest,
    ShortsVoiceRequest,
)
from fastapi import Depends
from app.core.dependencies import get_services, Services
from app.utils.io_processor import IOProcessor


router = APIRouter(prefix="/shorts")
io_processor = IOProcessor()


@router.post("/scripts")
def get_shorts_scripts(request: ShortsScriptRequest, services: Services = Depends(get_services)):
    video_script = services.google_ai.generate_shorts_scripts(
        duration=f"{request.duration}s",
        title=request.title,
        description=request.description,
    )
    return Response.with_data(video_script)


@router.post("/scene")
async def create_shorts_scene(request: ShortsSceneRequest, services: Services = Depends(get_services)):
    download_url = await services.video.create_shorts_scene(request)
    return Response.with_data(download_url)


@router.post("/combine")
async def combine_shorts_scene(request: CombineShortsSceneRequest, services: Services = Depends(get_services)):
    download_url = await services.video.combine_video(request)
    return Response.with_data(download_url)


@router.post("/video")
async def create_shorts_video(request: ShortsVideoRequest, services: Services = Depends(get_services)):
    download_url = await services.video.create_video(request)
    return Response.with_data(download_url)


@router.get("/image")
async def get_shorts_image(prompt: str = Query(...), services: Services = Depends(get_services)):
    (download_url, _) = await services.google_ai.generate_shorts_image(prompt)
    return Response.with_data(download_url)


@router.get("/voice")
async def get_shorts_voice(
    request: ShortsVoiceRequest = Depends(ShortsVoiceRequest.from_query), services: Services = Depends(get_services)
):
    result = services.google_ai.genereate_text_to_speech(request.text, request.duration, 1.2)
    download_url = await io_processor.upload_file_s3(1, file_path=result["output_path"], ext="mp3")
    return Response.with_data(download_url)
