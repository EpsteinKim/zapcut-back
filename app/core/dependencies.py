from app.utils.audio_processor import AudioProcessor
from app.utils.io_processor import IOProcessor
from app.utils.text_processor import TextProcessor
from app.utils.video_processor import VideoProcessor
from fastapi import Depends
from app.services.tts_service import TTSService
from app.services.openai_service import OpenAIService
from app.services.test_video_service import TestVideoService
from app.services.video_service import VideoService
from functools import lru_cache


class Services:
    def __init__(self):
        self.tts = TTSService()
        self.openai = OpenAIService()
        self.test_video = TestVideoService()
        self.video = VideoService()


@lru_cache()
def get_services() -> Services:
    return Services()
