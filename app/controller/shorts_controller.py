from fastapi import APIRouter, Depends
from app.models.schemas import (
    ApiResponse,
    ShortsScriptRequest,
    ShortsMakeSyncedSceneRequest,
    ShortsVideoRequest,
    ShortsVoiceRequest,
    ShortsImageRequest,
    Scene,
    ShortsTranscriptionRequest,
)
from fastapi import Depends
import asyncio
from app.core.dependencies import get_current_user, get_services, Services
from app.utils.io_processor import IOProcessor
from app.utils.video.audio_processor import AudioProcessor


router = APIRouter(prefix="/shorts", dependencies=[Depends(get_current_user)])
io_processor = IOProcessor()
audio_processor = AudioProcessor()


@router.get("/test")
async def test(url: str, services: Services = Depends(get_services)):
    content = await services.crawling.crawl_website(url)
    return ApiResponse.with_data(content)


@router.get("/page/image")
async def get_page_image(url: str, services: Services = Depends(get_services)):
    image_url = services.crawling.crawl_website_image(url)
    return ApiResponse.with_data(image_url)


@router.post("/initial-scenes")
async def get_initial_scenes(request: ShortsScriptRequest, services: Services = Depends(get_services)):
    if request.page_html:
        video_script = await services.google_ai.generate_initial_scenes(
            page_html=request.page_html,
            user_prompt=request.user_prompt,
        )
    else:
        video_script = await services.google_ai.generate_initial_scenes(
            user_prompt=request.user_prompt,
        )

    return ApiResponse.with_data(video_script)


@router.post("/video")
async def create_shorts_video(request: ShortsVideoRequest, services: Services = Depends(get_services)):
    download_url = await services.video.create_video(request)
    return ApiResponse.with_data(download_url)


@router.post("/image")
async def get_shorts_image(request: ShortsImageRequest, services: Services = Depends(get_services)):
    download_url = await services.google_ai.generate_shorts_image(request.prompt)
    return ApiResponse.with_data(download_url)


@router.post("/voice")
async def get_shorts_voice(request: ShortsVoiceRequest, services: Services = Depends(get_services)):
    output_path = await services.google_ai.genereate_text_to_speech(
        text=request.text,
        voice_model=request.voice_model,
        voice_temperature=request.voice_temperature,
        duration=request.duration,
    )
    download_url = await io_processor.upload_file_s3(file_path=output_path, ext="mp3")
    return ApiResponse.with_data(download_url)


@router.post("/transcript")
async def get_transcription(request: ShortsTranscriptionRequest, services: Services = Depends(get_services)):
    subclips_data = await audio_processor.get_audio_subclip(request.audio_url, request.text_scenes)

    tasks = []
    for subclip in subclips_data:
        tasks.append(
            services.google_ai.sync_scene_voice(
                text=subclip["text"], duration=subclip["duration"], voice_url=subclip["voice_url"]
            )
        )

    results = await asyncio.gather(*tasks)

    synced_scenes = []
    for i, result in enumerate(results):
        synced_scenes.append(
            Scene(
                duration=subclips_data[i]["duration"],
                voice_url=subclips_data[i]["voice_url"],
                captions=result["captions"],
            )
        )
    return ApiResponse.with_data(synced_scenes)


@router.post("/voice/sync")
async def sync_shorts_voice(request: list[Scene], services: Services = Depends(get_services)):
    sync_scene = await services.google_ai.sync_scene_voice(request)
    return ApiResponse.with_data(sync_scene)
