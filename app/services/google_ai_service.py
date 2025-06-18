import json
import re
import base64
import numpy as np
import os
import uuid
import tempfile
from io import BytesIO
from google import genai
from pydantic import BaseModel

from app.core.config import get_settings
from app.models.schemas import CaptionInfo, Scene
from app.utils.io_processor import IOProcessor
from app.utils.base64_decoder import decode_base64_data, decode_base64_to_bytesio
from pydub import AudioSegment


class GoogleScheme(BaseModel):
    title: str
    scenes: list[Scene]


class GoogleAIService:
    def __init__(self):
        settings = get_settings()
        self.client = genai.Client(api_key=settings.google_ai_api_key)
        self.io_processor = IOProcessor()
        self.temp_dir = tempfile.gettempdir()

    def generate_shorts_scripts(
        self, duration: str, content: str | None = None, title: str | None = None, description: str | None = None
    ):
        system_prompt = f"""You are a professional Korean YouTube Shorts content creator and video script writer.
        Your task is to create engaging content for a YouTube Shorts video.
        You should create content that is optimized for short-form video format and can be visualized using Stable Diffusion.
        Focus on creating viral-worthy content that will engage viewers.

        For each time segment:
        - Write captions in an introductory style
        - Ensure natural flow of the overall story
        - Keep scenes short with quick transitions between them
        - Create as many scenes as possible
        - Include 2-4 captions per scene (except for the first scene)
        - Make screen transitions as fast as possible
        - Write in a friendly, conversational tone
        - Write in Korean (must be Korean)
        - Write descriptions in Korean (must be Korean)
        - Write descriptions that guide appropriate video content for each scene
        - Consider appropriate timing between captions for TTS
        - Video length (must match exactly): {duration}s
        - Do not use emojis
        - The time in captions is relative to the duration of the scene
        """

        user_prompt = f"""Create a YouTube Shorts video script based on the following content:
        
        """

        if title:
            user_prompt += f"""제목: {title}
            """

        if description:
            user_prompt += f"""설명: {description}
            """

        if content:
            user_prompt += f"""
            크롤링한 결과는 아래와 같습니다            
            {content}

            """

        user_prompt += f"""
            이것들을 바탕으로 영상 스크립트를 작성해주세요.
        """

        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[user_prompt],
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=2048,
                response_mime_type="application/json",
                response_schema=GoogleScheme,
            ),
        )

        # 정규표현식을 사용하여 'json' 텍스트 제거
        cleaned_text = re.sub(r"^```json\s*|\s*```$", "", response.text.strip())

        return json.loads(cleaned_text)

    def translate(self, string: str, language: str):
        system_prompt = f"""
        You are a professional translator specializing in image generation prompts. 
        Your task is to translate the input text into {language} while maintaining the visual elements and composition details.
        """

        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[string],
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=2048,
            ),
        )

        return response.text

    async def generate_shorts_image(self, user_prompt: str, user_id: int = 1):
        translated_prompt = self.translate(user_prompt, "English")
        response = self.client.models.generate_images(
            model="imagen-3.0-generate-002",
            prompt=translated_prompt,
            config=genai.types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="1:1",
            ),
        )

        for generated_image in response.generated_images:
            image_data = generated_image.image.image_bytes
            if isinstance(image_data, bytes):
                image = decode_base64_to_bytesio(image_data)
            else:
                image = BytesIO(image_data)

            download_url = await self.io_processor.upload_file_s3(user_id, image, "png")
            return (download_url, image)

    def genereate_text_to_speech(self, text: str, duration: float = None, speed_multiplier: float = 1.0):
        prompt = f"""
        You are a YouTube Shorts narrator. Your task is to read the given text within the specified duration while maintaining a natural and engaging tone. Focus on clear pronunciation and appropriate pacing to ensure the content is delivered effectively within the time constraint.
        {f"You must read the text within the specified duration of {duration} seconds, even if it means speaking faster than normal. The timing is crucial - do not exceed the duration under any circumstances. Adjust your speaking pace to ensure the entire text is delivered within the time limit." if duration is not None else ""}
        The text is: {text}
        """
        response = self.client.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=genai.types.SpeechConfig(
                    voice_config=genai.types.VoiceConfig(
                        prebuilt_voice_config=genai.types.PrebuiltVoiceConfig(
                            voice_name="Enceladus",
                        )
                    ),
                    language_code="ko-KR",
                ),
            ),
        )
        data = response.candidates[0].content.parts[0].inline_data.data
        audio_data = decode_base64_data(data)

        # WAV 파일로 저장
        temp_wav_path = os.path.join(self.temp_dir, f"tts_{uuid.uuid4()}.mp3")
        audio = AudioSegment(audio_data, sample_width=2, frame_rate=24000, channels=1)

        # 음성 속도 조절
        if speed_multiplier != 1.0:
            audio = audio.speedup(playback_speed=speed_multiplier)

        audio.export(temp_wav_path, format="mp3")

        return {"output_path": temp_wav_path, "fps": 24000}
