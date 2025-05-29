from functools import lru_cache
from app.services.tts_service import TTSService
from app.services.openai_service import OpenAIService
from app.utils.text_processor import TextProcessor
from app.utils.audio_processor import AudioProcessor
from app.utils.video_processor import VideoProcessor
from app.utils.io_processor import IOProcessor
from dataclasses import dataclass

# 순환참조 방지 목적


@dataclass
class Processors:
    text: TextProcessor
    audio: AudioProcessor
    video: VideoProcessor
    IO: IOProcessor


@lru_cache()
def get_tts_service() -> TTSService:
    return TTSService()


@lru_cache()
def get_openai_service() -> OpenAIService:
    return OpenAIService()
