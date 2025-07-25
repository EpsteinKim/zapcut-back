from fastapi import APIRouter
from app.utils.io_processor import IOProcessor
from app.utils.audio_processor import AudioProcessor
from app.services.openai_service import OpenAIService
from app.core.service_locator import get_openai_service
from fastapi import Depends
from app.core.dependencies import get_services, Services

router = APIRouter()

io_processor = IOProcessor()
audio_processor = AudioProcessor()


@router.get("/test")
async def test(services: Services = Depends(get_services)):
    return await services.google_ai.get_transcription(
        "https://cdn.zapcut.io/expired/no_56342641736507781753349698991.mp3"
    )
