from fastapi import APIRouter, Response, Depends
from app.exceptions.http_exceptions import ServerException
from app.models.schemas import ShortsRequest, ShortsResponse, ShortsContentRequest
from app.core.dependencies import get_services, Services

router = APIRouter(prefix="/video")


@router.post("/create-shorts", response_model=ShortsResponse)
async def create_shorts(request: ShortsRequest, services: Services = Depends(get_services)):
    try:
        output_path = await services.video.create_shorts(request)
        return Response(output_path)
    except Exception as e:
        raise ServerException(str(e))


async def create_shorts_scene(request: ShortsContentRequest, services: Services = Depends(get_services)):
    try:
        output_path = await services.video.create_shorts_scene(request)
        return Response(output_path)
    except Exception as e:
        raise ServerException(status_code=500, detail=str(e))
