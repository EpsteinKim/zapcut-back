from aiohttp_socks import ProxyConnector
from fastapi import APIRouter, Depends
from app.models.schemas import (
    ApiResponse,
    ShortsScriptGenerateRequest,
    ShortsVideoRequest,
    ShortsVoiceRequest,
    ShortsImageRequest,
    Scene,
    ShortsTranscriptionRequest,
    GoogleAiSimpleScene,
    ShortsVoiceSubClipRequest,
    ShortsScript,
    ShortsScriptSaveRequest,
    ShortsScriptUpdateRequest,
    ShortsScriptDeleteRequest,
    ShortsScriptUpsertRequest,
)
from fastapi import Depends
import asyncio
from app.core.dependencies import get_current_user, get_services, Services
from app.entity.user import User
from app.utils.io_processor import IOProcessor
from app.utils.video.audio_processor import AudioProcessor
from app.core.config import get_settings
import aiohttp


router = APIRouter(prefix="/shorts", dependencies=[Depends(get_current_user)])
io_processor = IOProcessor()
audio_processor = AudioProcessor()
settings = get_settings()


@router.get("/script/{script_id}")
def get_script(
    script_id: str, current_user: User = Depends(get_current_user), services: Services = Depends(get_services)
):
    result = services.shortscript.get_script(services.session, current_user.id, script_id)
    if not result:
        return ApiResponse.error("스크립트를 찾을 수 없습니다.")
    return ApiResponse.with_data(result)


@router.get("/scripts")
def get_all_scripts(current_user: User = Depends(get_current_user), services: Services = Depends(get_services)):
    result = services.shortscript.get_all_scripts(services.session, current_user.id)
    return ApiResponse.with_data(result)


@router.get("/script/count")
def get_script_count(current_user: User = Depends(get_current_user), services: Services = Depends(get_services)):
    count = services.shortscript.get_script_count(services.session, current_user.id)
    return ApiResponse.with_data(count)


@router.post("/script")
async def upsert_script(
    request: ShortsScriptUpsertRequest,
    current_user: User = Depends(get_current_user),
    services: Services = Depends(get_services),
):
    result = await services.shortscript.upsert_script(services.session, current_user.id, request)
    return ApiResponse.with_data(result)


@router.delete("/script/{script_id}")
def delete_script(
    script_id: str, current_user: User = Depends(get_current_user), services: Services = Depends(get_services)
):
    success = services.shortscript.delete_script(services.session, current_user.id, script_id)
    if not success:
        return ApiResponse.error("스크립트를 찾을 수 없습니다.")
    return ApiResponse.ok("스크립트가 삭제되었습니다.")


@router.post("/initial-scenes")
async def get_initial_scenes(request: ShortsScriptGenerateRequest, services: Services = Depends(get_services)):
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
    if settings.env == "dev":
        connector = ProxyConnector.from_url("socks5://54.180.39.0:9111")
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.post(
                f"{settings.kube_api_base}/api/v1/shorts/video",
                json=request.model_dump(),
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return ApiResponse.with_data(data.get("data", data))
    else:
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


@router.post("/voice/subclip")
async def subclip_voice(request: ShortsVoiceSubClipRequest, services: Services = Depends(get_services)):
    subclips_data = await audio_processor.get_audio_subclip(request.voice_url, request.text_scenes)
    return ApiResponse.with_data(subclips_data)


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

    if request.regenerate:
        for i, result in enumerate(results):
            synced_scenes.append(
                GoogleAiSimpleScene(
                    duration=subclips_data[i]["duration"],
                    voice_url=subclips_data[i]["voice_url"],
                    captions=result["captions"],
                )
            )
    else:
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
