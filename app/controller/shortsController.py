from fastapi import APIRouter, Query, Response, Depends
from app.models.schemas import (
    Response,
    ShortsScriptRequest,
    ShortsVideoRequest,
    ShortsVoiceRequest,
    SceneWithData,
    CaptionInfo,
    ShortsImageRequest,
)
from fastapi import Depends
from app.core.dependencies import get_services, Services
from app.utils.io_processor import IOProcessor
from app.services.web_scraper import AsyncWebScraper, simple_scrape_single_page


router = APIRouter(prefix="/shorts")
io_processor = IOProcessor()


@router.get("/test")
async def test(url: str, services: Services = Depends(get_services)):
    content = services.crawling.crawl_website(url)
    return Response.with_data(content)


@router.get("/page/image")
async def get_page_image(url: str, services: Services = Depends(get_services)):
    image_url = services.crawling.crawl_website_image(url)
    return Response.with_data(image_url)


@router.post("/scripts")
async def get_shorts_scripts(request: ShortsScriptRequest, services: Services = Depends(get_services)):
    if request.page_image_url:
        video_script = await services.google_ai.generate_shorts_scripts(
            duration=f"{request.duration}s",
            title=request.title,
            description=request.description,
            page_image_url=request.page_image_url,
            additional_prompt=request.additional_prompt,
        )
    else:
        video_script = await services.google_ai.generate_shorts_scripts(
            duration=f"{request.duration}s",
            title=request.title,
            description=request.description,
            additional_prompt=request.additional_prompt,
        )

    return Response.with_data(video_script)


@router.post("/video")
async def create_shorts_video(request: ShortsVideoRequest, services: Services = Depends(get_services)):
    download_url = await services.video.create_video(request)
    return Response.with_data(download_url)


@router.post("/image")
async def get_shorts_image(request: ShortsImageRequest, services: Services = Depends(get_services)):
    (download_url, _) = await services.google_ai.generate_shorts_image(request.prompt)
    return Response.with_data(download_url)


@router.post("/voice")
async def get_shorts_voice(request: ShortsVoiceRequest, services: Services = Depends(get_services)):
    result = await services.google_ai.genereate_text_to_speech(
        text=request.text,
        duration=request.duration,
        voice_model=request.voice_model,
        voice_temperature=request.voice_temperature,
        speed_multiplier=1.2,
    )
    download_url = await io_processor.upload_file_s3(file_path=result["output_path"], ext="mp3")
    return Response.with_data(download_url)


@router.post("/voice/sync")
async def sync_shorts_voice(request: list[SceneWithData], services: Services = Depends(get_services)):
    sync_scene = await services.google_ai.sync_scene_voice(request)
    return Response.with_data(sync_scene)
