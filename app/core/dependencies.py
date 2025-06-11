from fastapi import Depends
from functools import lru_cache
from app.services.google_ai_service import GoogleAIService
from app.services.video_service import VideoService


class Services:
    def __init__(self):
        self.video = VideoService()
        self.google_ai = GoogleAIService()


@lru_cache()
def get_services() -> Services:
    return Services()
