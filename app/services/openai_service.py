import base64
from io import BytesIO
import json
from openai import OpenAI
from app.core.config import get_settings
from app.exceptions.http_exceptions import UnprocessableEntityError
from app.models.schemas import ShortsResponse
import requests
import os
from pathlib import Path
from app.utils.io_processor import IOProcessor


class OpenAIService:
    def __init__(self):
        settings = get_settings()
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.io_processor = IOProcessor()

    async def generate_chat_response(self, prompt: str) -> str:
        system_prompt = f"""
        You are a professional Korean talk show host.
        your task is to just response in korean.
        """
        response = self.client.responses.create(
            model="o4-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
        )
        return response.output_text

    async def translate_to_english(self, string: str) -> str:
        if all(ord("가") <= ord(char) <= ord("힣") or char.isspace() or char in ".,!?()[]{}" for char in string):
            return string

        system_prompt = f"""
        You are a professional Korean to English translator specializing in image generation prompts.
        Your task is to translate the following Korean text into English, focusing on visual elements and avoiding text elements.
        Follow these guidelines:
        1. Translate only visual descriptions
        2. Remove or replace any text elements with visual alternatives
        3. Use clear, descriptive language suitable for image generation
        4. Focus on composition, colors, lighting, and visual elements
        5. Maintain the core visual concept while removing text references
        """
        response = self.client.responses.create(
            model="o4-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": string},
            ],
        )
        return response.output_text

    def generate_shorts_scripts(self, content: str, duration: str, style: str = "popular") -> ShortsResponse:
        if len(content) < 100:
            raise UnprocessableEntityError("정보가 너무 적거나, 접근할 수 없는 페이지입니다.", {"content": content})

        system_prompt = f"""You are a professional Korean YouTube Shorts content creator and video script writer.
        Your task is to create engaging content for a {duration} YouTube Shorts video in a {style} style.
        You should create content that is optimized for short-form video format and can be visualized using Stable Diffusion.
        Focus on creating viral-worthy content that will engage viewers.
        """

        user_prompt = f"""Create a YouTube Shorts video script based on the following content:
        
        {content}

        Please provide the following in a structured format:
        {{
            "title": "영상을 대표하는 매력적인 제목"
            "scene": [
                {{
                    "time": "0-2초",
                    "caption": [ {{"text": "영상에 들어 갈 음성 및 자막", "start_time": 영상이 시작되는 초, "end_time": 영상이 끝나는 초}} , ...]
                    "description": "해당 장면에 들어가면 좋을 썸네일 혹은 영상에 대한 상세 설명 및 묘사"
                }},
                {{
                    "time": "장면에 맞는 초 분배",
                    "caption": [ {{"text": "영상에 들어 갈 음성 및 자막", "start_time": 영상이 시작되는 초, "end_time": 영상이 끝나는 초}} , ...]
                    "description": "해당 장면에 들어가면 좋을 영상에 대한 상세 설명 및 묘사"
                }},
                ... (이런 형식으로 {duration} 동안 계속)
            ]
        
        }}
        
        각 시간대별로:
        - 캡션은 소개해주는 것처럼 작성
        - 전체적인 스토리 흐름이 자연스럽게 이어지도록 구성
        - 전체적으로 씬들이 짧음. 씬 간 전환은 최대한 스피드하게 하면 좋음
        - 첫번째 장면을 제외하고 caption은 2~4개
        - 화면 전환은 최대한 스피드하게 하면 좋음
        - 친근하게 설명하도록 작성
        - 한국어로 작성해주세요
        - 자막은 ~~ 합니다, 혹은 ~~ 알고 있어? 등으로 대화형으로 작성
        """

        response = self.client.responses.create(
            model="o4-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        return json.loads(response.output_text)

    def generate_shorts_image(self, user_prompt: str, user_id: int = 1):
        prompt = f"{user_prompt}"
        response = self.client.images.generate(
            model="gpt-image-1", prompt=prompt, size="1024x1024", output_format="png"
        )

        dumped = response.model_dump()
        base64_image = dumped["data"][0]["b64_json"]
        image_data = base64.b64decode(base64_image.split(",")[1] if "," in base64_image else base64_image)

        image_file = BytesIO(image_data)
        return self.io_processor.upload_file(user_id, image_file, "png")
