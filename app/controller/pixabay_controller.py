from fastapi import APIRouter, Depends, Request
from typing import Literal
import aiohttp
from app.core.config import get_settings
from app.core.dependencies import get_current_user
from app.entity.user import User
from app.models.schemas import ApiResponse
from app.utils.rate_limit_util import check_user_rate_limit
from app.core.dependencies import Services, get_services

router = APIRouter(prefix="/pixabay", tags=["pixabay"])

settings = get_settings()


@router.get("/search-media")
async def search_pixabay(
    query: str,
    type: Literal["photo", "video"] = "photo",
    current_user: User = Depends(get_current_user),
):
    check_user_rate_limit(current_user.user_id, max_requests=1, window_seconds=3, prefix="pixabay_search")

    base_url = "https://pixabay.com/api/"
    params = {
        "key": settings.pixabay_api_key,
        "q": query,
        "image_type": type,
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(base_url, params=params) as response:
            result = await response.json()
            result = result["hits"]
            result = [
                {
                    "url": item["webformatURL"],
                }
                for item in result
            ]
    return ApiResponse.with_data(result)


@router.get("/recommend-media")
async def recommend_pixabay_media(
    description: str,
    image_type: Literal["photo", "video"] = "photo",
    current_user: User = Depends(get_current_user),
    services: Services = Depends(get_services),
):
    check_user_rate_limit(current_user.user_id, max_requests=1, window_seconds=3, prefix="recommend_media")

    summary = await services.google_ai.summarize(description)

    base_url = "https://pixabay.com/api/"
    params = {
        "key": settings.pixabay_api_key,
        "q": summary,
        "image_type": image_type,
    }

    print(summary)

    async with aiohttp.ClientSession() as session:
        async with session.get(base_url, params=params) as response:
            result = await response.json()
            result = result["hits"]
            result = [item["webformatURL"] for item in result]
    return ApiResponse.with_data(result)
