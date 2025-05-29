from fastapi import APIRouter, HTTPException, Query, Response, Depends
from app.models.schemas import (
    ShortsContentRequest,
    Response,
    ShortsSceneRequest,
    Scene,
    CombineShortsSceneRequest,
    ShortsScriptRequest,
)
from app.services.web_scraper import AsyncWebScraper
from fastapi import Depends
from app.exceptions.http_exceptions import ServerException
from app.core.dependencies import get_services, Services
from pydantic import BaseModel


router = APIRouter(prefix="/shorts")


@router.get("/scripts", response_model=Response)
async def get_shorts_scripts(
    request: ShortsScriptRequest = Depends(ShortsScriptRequest.from_query), services: Services = Depends(get_services)
):
    async with AsyncWebScraper() as scraper:
        result = await scraper.scrape_single_page(request.url)
    video_script = services.openai.generate_shorts_scripts(result["content"], f"{request.duration}s")
    return Response.with_data(video_script)


@router.post("/scene")
async def create_shorts_scene(request: ShortsSceneRequest, services: Services = Depends(get_services)):
    output_path = await services.video.create_shorts_scene(request)
    return Response.with_data(output_path)


@router.post("/combine")
async def combine_shorts_scene(request: CombineShortsSceneRequest, services: Services = Depends(get_services)):
    output_path = await services.video.combine_video(request)
    return Response.with_data(output_path)


@router.get("/image")
def get_shorts_image(prompt: str = Query(...), services: Services = Depends(get_services)):
    translated_description = services.openai.translate_to_english(prompt)
    image_url = services.openai.generate_shorts_image(translated_description)
    return Response.with_data(image_url)
