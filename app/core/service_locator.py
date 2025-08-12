from functools import lru_cache
from app.services.openai_service import OpenAIService
from app.services.google_ai_service import GoogleAIService
from app.services.sms_service import SMSService
from app.services.shortscript_service import ShortScriptService
from app.utils.video.text_processor import TextProcessor
from app.utils.video.audio_processor import AudioProcessor
from app.utils.video.video_processor import VideoProcessor
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
def get_openai_service() -> OpenAIService:
    return OpenAIService()


@lru_cache()
def get_google_ai_service() -> GoogleAIService:
    return GoogleAIService()


@lru_cache()
def get_sms_service() -> SMSService:
    return SMSService()


@lru_cache()
def get_shortscript_service() -> ShortScriptService:
    return ShortScriptService()
