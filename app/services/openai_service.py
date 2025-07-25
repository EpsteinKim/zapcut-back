import base64
from io import BytesIO
import json
from openai import OpenAI
from app.core.config import get_settings
from app.exceptions.http_exceptions import UnprocessableEntityError
from app.models.schemas import Response
from app.utils.base64_decoder import decode_base64_data
import requests
import os
from pathlib import Path
from app.utils.io_processor import IOProcessor


class OpenAIService:
    def __init__(self):
        settings = get_settings()
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.io_processor = IOProcessor()

    async def create_transcription(self, audio_url: str, text: str, duration: float):
        audio_path = await self.io_processor.download_file(audio_url)
        prompt = f"""
            text: {text}
            duration: {duration}
        """
        with open(audio_path, "rb") as audio_file:
            transcription = self.client.audio.transcriptions.create(
                prompt="",
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
            )

        print(transcription)
