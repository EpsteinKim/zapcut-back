from fastapi import Depends
from functools import lru_cache
from app.services.google_ai_service import GoogleAIService
from app.services.video_service import VideoService
from app.services.video_service_ffmpeg import VideoServiceFFmpeg
from app.services.crawling_service import CrawlingService
import os


class Services:
    def __init__(self):
        if os.getenv("ENV") == "production":
            self.video = VideoService()
        else:
            self.video = VideoServiceFFmpeg()
        self.google_ai = GoogleAIService()
        self.crawling = CrawlingService()


@lru_cache()
def get_services() -> Services:
    return Services()
