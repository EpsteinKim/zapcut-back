from fastapi import APIRouter, Query, Response, Depends
from app.models.schemas import (
    Response,
    ShortsScriptRequest,
    ShortsMakeSyncedSceneRequest,
    ShortsVideoRequest,
    ShortsVoiceRequest,
    ShortsImageRequest,
    Scene,
)
from fastapi import Depends
from app.core.dependencies import get_services, Services
from app.utils.io_processor import IOProcessor
from app.services.web_scraper import AsyncWebScraper, simple_scrape_single_page


router = APIRouter(prefix="/shorts")
io_processor = IOProcessor()


@router.get("/test")
async def test(url: str, services: Services = Depends(get_services)):
    content = await services.crawling.crawl_website(url)
    return Response.with_data(content)


@router.get("/page/image")
async def get_page_image(url: str, services: Services = Depends(get_services)):
    image_url = services.crawling.crawl_website_image(url)
    return Response.with_data(image_url)


# @router.post("/scripts")
# async def get_shorts_scripts(request: ShortsScriptRequest, services: Services = Depends(get_services)):
#     if request.page_image_url:
#         video_script = await services.google_ai.generate_shorts_scripts(
#             duration=f"{request.duration}s",
#             user_prompt=request.user_prompt,
#             page_image_url=request.page_image_url,
#         )
#     else:
#         video_script = await services.google_ai.generate_shorts_scripts(
#             duration=f"{request.duration}s",
#             user_prompt=request.user_prompt,
#         )

#     return Response.with_data(video_script)


@router.post("/initial-scenes")
async def get_shorts_script_string(request: ShortsScriptRequest, services: Services = Depends(get_services)):
    if request.page_html:
        video_script = await services.google_ai.generate_shorts_script_string(
            duration=f"{request.duration}s",
            page_html=request.page_html,
            user_prompt=request.user_prompt,
        )
    else:
        video_script = await services.google_ai.generate_shorts_script_string(
            duration=f"{request.duration}s",
            user_prompt=request.user_prompt,
        )

    return Response.with_data(video_script)


@router.post("/video")
async def create_shorts_video(request: ShortsVideoRequest, services: Services = Depends(get_services)):
    download_url = await services.video.create_video(request)
    return Response.with_data(download_url)


@router.post("/image")
async def get_shorts_image(request: ShortsImageRequest, services: Services = Depends(get_services)):
    download_url = await services.google_ai.generate_shorts_image(request.prompt)
    return Response.with_data(download_url)


@router.post("/voice")
async def get_shorts_voice(request: ShortsVoiceRequest, services: Services = Depends(get_services)):
    output_path = await services.google_ai.genereate_text_to_speech(
        text=request.text,
        duration=request.duration,
        voice_model=request.voice_model,
        voice_temperature=request.voice_temperature,
        speed_multiplier=1.0,
    )
    download_url = await io_processor.upload_file_s3(file_path=output_path, ext="mp3")
    return Response.with_data(download_url)


@router.post("/synced-scene")
async def make_synced_scene(request: ShortsMakeSyncedSceneRequest, services: Services = Depends(get_services)):
    result = await services.google_ai.make_synced_scene(request)
    return Response.with_data(result)


@router.post("/voice/sync")
async def sync_shorts_voice(request: list[Scene], services: Services = Depends(get_services)):
    sync_scene = await services.google_ai.sync_scene_voice(request)
    return Response.with_data(sync_scene)
