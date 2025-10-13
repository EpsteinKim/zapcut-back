import json
import os
import uuid
import asyncio
import logging
from io import BytesIO
from google import genai
from openai import AsyncOpenAI
from openai import OpenAI as sync_openai
from pydantic import BaseModel
from pydub import AudioSegment
import librosa
import numpy as np

from app.core.config import get_settings
from app.exceptions.http_exceptions import ServerException
from app.models.constants import SystemPrompt
from app.models.schemas import (
    GoogleAiSimpleCaptionInfo,
    GoogleAiSimpleScene,
    ShortsMakeSyncedSceneRequest,
    TTSVoiceModel,
    Scene,
    CaptionInfo,
    ShortsTranscriptionRequest,
)
from app.utils.io_processor import IOProcessor
from app.utils.base64_decoder import decode_base64_data, decode_base64_to_bytesio, encode_audio_to_base64
from pydub import AudioSegment
from app.utils.os_processor import get_temp_dir
from app.utils.video.audio_processor import AudioProcessor


class GoogleScheme(BaseModel):
    title: str
    scenes: list[Scene]


class InitialScene(BaseModel):
    text: str
    description: str
    image_url: str = ""


class GoogleSchemeAlter(BaseModel):
    scenes: list[Scene]


class GoogleAIService:
    def __init__(self):
        self.settings = get_settings()
        self.open_router_client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1", api_key=self.settings.open_router_api_key
        )
        self.sync_open_router_client = sync_openai(
            api_key=self.settings.open_router_api_key, base_url="https://openrouter.ai/api/v1"
        )
        self.client = genai.Client(api_key=self.settings.google_ai_api_key)
        self.io_processor = IOProcessor()
        self.audio_processor = AudioProcessor()
        self.temp_dir = get_temp_dir("google_ai_service")

    async def generate_initial_scenes(self, user_prompt: str, page_html: str | None = None):
        system_prompt = SystemPrompt.INITIAL_SCENES

        schema = {
            "name": "InitialScenes",
            "schema": {
                "type": "array",
                "items": InitialScene.model_json_schema(),
            },
        }

        if page_html:
            user_prompt += f"""
            Please analyze the following HTML of the requested page and use it as a basis for your analysis.
            And please select and suggest images from the given HTML that would be good to include in each shorts script.
            But youtube related videos are not allowed to be included.
            Do not include images with an aspect ratio greater than 2:1.
            If there is no appropriate image, you can omit it.
            And please suggest different images for each scene.
            {page_html}
        """

        response = await self._get_open_router_response(
            prompt=user_prompt, model="google/gemini-2.5-flash", system_prompt=system_prompt, schema=schema
        )

        return json.loads(str(response))

    async def translate(self, string: str, language: str):
        system_prompt = SystemPrompt.TRANSLATE(language)

        response = await self._get_open_router_response(
            prompt=string, model="google/gemini-2.5-flash-lite", system_prompt=system_prompt
        )
        return response

    async def generate_shorts_image(self, user_prompt: str, max_retries=3):
        translated_prompt = await self.translate(user_prompt, "English")

        response = await self._get_open_router_response(
            prompt=str(translated_prompt), model="google/gemini-2.5-flash-image-preview", is_sync=True
        )
        return response

    async def genereate_text_to_speech(
        self,
        text: str,
        voice_model: TTSVoiceModel,
        voice_temperature: float,
        duration: float | None = None,
    ):
        prompt = f"""
        text: {text}
        - Speak at a fast and energetic pace suitable for YouTube Shorts (about 1.3x ~ 1.5x normal speed)
        - Keep the tone engaging and dynamic
        - Maintain clear pronunciation even at faster speed
        - Do not repeat any sentence or content more than once. If there is any duplicate, say it only once.
        """
        if duration:
            prompt += f"""
            Read the text within the specified duration of {duration} seconds, 
            even if it means speaking faster than normal. 
            The timing is crucial - do not exceed the duration under any circumstances.
            Adjust your speaking pace to ensure the entire text is delivered within the time limit.
            """

        try:
            response = await self.client.aio.models.generate_content(
                model="gemini-2.5-flash-preview-tts",
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    temperature=voice_temperature,
                    speech_config=genai.types.SpeechConfig(
                        voice_config=genai.types.VoiceConfig(
                            prebuilt_voice_config=genai.types.PrebuiltVoiceConfig(
                                voice_name=voice_model,
                            )
                        ),
                    ),
                ),
            )

            data = response.candidates[0].content.parts[0].inline_data.data
            audio_data = decode_base64_data(data)

            temp_wav_path = os.path.join(self.temp_dir, f"tts_audio_{uuid.uuid4()}.mp3")
            audio = AudioSegment(audio_data, sample_width=2, frame_rate=24000, channels=1)
            try:
                audio.export(temp_wav_path, format="mp3", parameters=["-q:a", "0"])
            except Exception as export_error:
                logging.error(f"audio.export 실패: {str(export_error)}")
                raise ServerException(f"오디오 export 실패: {str(export_error)}")

            # 파일이 생성되었는지 확인
            if not os.path.exists(temp_wav_path):
                raise ServerException(f"TTS 오디오 파일 생성 실패: {temp_wav_path}")

            logging.info(f"TTS 파일 생성 성공: {temp_wav_path}")
            return temp_wav_path

        except Exception as e:
            raise ServerException(f"TTS 생성에 실패했습니다", str(e))

    async def summarize_text(self, text: str):
        response = await self._get_open_router_response(
            prompt=text, model="google/gemini-2.5-flash-lite", system_prompt=SystemPrompt.TITLE_SUMMARY
        )
        return response

    async def sync_scene_voice(self, text: str, duration: float, voice_url: str) -> str:
        system_prompt = SystemPrompt.SYNC_SCENE_VOICE

        user_prompt = f"""
            text: {text}
            duration: {duration}
        """

        voice_path = await self.io_processor.download_file(voice_url)

        schema = {
            "name": "SimpleScene",
            "schema": {
                "type": "object",
                "properties": {
                    "captions": {
                        "type": "array",
                        "items": GoogleAiSimpleCaptionInfo.model_json_schema(),
                    },
                },
            },
        }
        response = await self._get_open_router_response(
            prompt=user_prompt,
            model="google/gemini-2.5-flash",
            system_prompt=system_prompt,
            schema=schema,
            audio_path=voice_path,
        )
        return json.loads(str(response))

    async def summarize(self, prompt: str, model: str):
        response = await self._get_open_router_response(
            prompt=prompt, model=model, system_prompt=SystemPrompt.TITLE_SUMMARY
        )
        return response

    async def _get_open_router_response(
        self,
        prompt: str,
        model: str,
        system_prompt: str = None,
        schema: dict = None,
        is_sync: bool = False,
        audio_path: str = None,
    ):
        messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]

        if audio_path:
            messages[0]["content"].append(
                {
                    "type": "input_audio",
                    "input_audio": {"data": encode_audio_to_base64(audio_path), "format": "mp3"},
                }
            )

        if system_prompt:
            messages.insert(0, {"role": "system", "content": system_prompt})

        other_kwargs = {}
        if schema:
            other_kwargs["response_format"] = {"type": "json_schema", "json_schema": schema}

        if is_sync:
            response = self.sync_open_router_client.chat.completions.create(
                model=model, messages=messages, **other_kwargs
            )

            if model == "google/gemini-2.5-flash-image-preview":
                message = response.choices[0].message
                if message.images:
                    for image in message.images:
                        image_url_data = image["image_url"]
                        url = image_url_data["url"]

                        if url.startswith("data:image"):
                            image_data = url.split(",")[1] if "," in url else url
                            if image_data.strip():
                                image_bytes = decode_base64_to_bytesio(image_data)
                                download_url = await self.io_processor.upload_file_s3(file_data=image_bytes, ext="png")
                                return download_url
            else:
                return response.choices[0].message.content
        else:
            try:
                response = await self.open_router_client.chat.completions.create(
                    model=model, messages=messages, **other_kwargs
                )
                return response.choices[0].message.content
            except Exception as e:
                raise ServerException(str(e))
