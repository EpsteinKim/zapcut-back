import json
import re
import base64
import numpy as np
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
    scene: list[Scene]


class GoogleAIService:
    def __init__(self):
        settings = get_settings()
        self.client = genai.Client(api_key=settings.google_ai_api_key)
        self.io_processor = IOProcessor()

    def generate_shorts_scripts(self, content: str, duration: str, style: str = "popular"):
        system_prompt = f"""You are a professional Korean YouTube Shorts content creator and video script writer.
        Your task is to create engaging content for a {duration} YouTube Shorts video in a {style} style.
        You should create content that is optimized for short-form video format and can be visualized using Stable Diffusion.
        Focus on creating viral-worthy content that will engage viewers.
        """

        user_prompt = f"""Create a YouTube Shorts video script based on the following content:
        
        {content}
        
        각 시간대별로:
        - 캡션은 소개해주는 것처럼 작성
        - 전체적인 스토리 흐름이 자연스럽게 이어지도록 구성
        - 전체적으로 씬들이 짧음. 씬 간 전환은 최대한 스피드하게 하면 좋음
        - 첫번째 장면을 제외하고 caption은 2~4개
        - 화면 전환은 최대한 스피드하게 하면 좋음
        - 친근하게 설명하도록 작성
        - 한국어로 작성해주세요
        - 자막은 ~~ 합니다, 혹은 ~~ 알고 있어? 등으로 대화형으로 작성
        - response.text에 앞에 json글자 제거해주세요.
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

            upload_url = await self.io_processor.upload_file_s3(user_id, image, "png")
            return (upload_url, image)

    def genereate_text_to_speech(self, text: str, speed_multiplier: float = 1.0):
        response = self.client.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents=text,
            config=genai.types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=genai.types.SpeechConfig(
                    voice_config=genai.types.VoiceConfig(
                        prebuilt_voice_config=genai.types.PrebuiltVoiceConfig(
                            voice_name="Achird",
                        )
                    ),
                    language_code="ko-KR",
                ),
            ),
        )
        data = response.candidates[0].content.parts[0].inline_data.data

        audio_data = decode_base64_data(data)

        audio = AudioSegment(audio_data, sample_width=2, frame_rate=24000, channels=1)

        # 음성 속도 조절
        if speed_multiplier != 1.0:
            # speedup() 메서드를 사용하여 음성 속도 조절 (pitch 유지)
            audio = audio.speedup(playback_speed=speed_multiplier)

        audio_array = np.array(audio.get_array_of_samples(), dtype=np.float32)

        if len(audio_array.shape) == 1:
            audio_array = audio_array.reshape(-1, 1)
        elif audio.channels == 2:
            audio_array = audio_array.reshape((-1, 2))

        audio_array = audio_array / (2**15)

        return {"audio_array": audio_array, "fps": audio.frame_rate, "duration": len(audio) / 1000.0}
