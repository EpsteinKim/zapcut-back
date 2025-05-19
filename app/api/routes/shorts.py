from fastapi import APIRouter, HTTPException
from app.models.schemas import ShortsRequest, ShortsResponse
from app.services.openai_service import OpenAIService

router = APIRouter()
openai_service = OpenAIService()

@router.post("/generate-shorts", response_model=ShortsResponse)
async def generate_shorts(request: ShortsRequest):
    try:
        content = await openai_service.generate_shorts_content(
            request.topic,
            request.style,
            request.duration
        )
        return ShortsResponse(**content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 