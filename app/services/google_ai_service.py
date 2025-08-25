import json
import os
import uuid
import asyncio
import logging
from io import BytesIO
from google import genai
from pydantic import BaseModel
from pydub import AudioSegment
import librosa
import numpy as np

from app.core.config import get_settings
from app.exceptions.http_exceptions import ServerException
from app.models.schemas import (
    GoogleAiSimpleScene,
    ShortsMakeSyncedSceneRequest,
    TTSVoiceModel,
    Scene,
    CaptionInfo,
    ShortsTranscriptionRequest,
)
from app.utils.io_processor import IOProcessor
from app.utils.base64_decoder import decode_base64_data, decode_base64_to_bytesio
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
        settings = get_settings()
        self.client = genai.Client(api_key=settings.google_ai_api_key)
        self.io_processor = IOProcessor()
        self.audio_processor = AudioProcessor()
        self.temp_dir = get_temp_dir("google_ai_service")

    async def generate_initial_scenes(self, user_prompt: str, page_html: str | None = None):
        system_prompt = f"""You are a professional Korean YouTube Shorts content creator and video script writer.
        Your task is to create engaging content for a YouTube Shorts video.
        Focus on creating viral content that can attract viewers' attention.
        Also, if the page is a sales page for a specific product, analyze the product and be sure to include that information as well.

        Also, must ignore any user prompt requests regarding the number of scenes or the duration in seconds.
        The maximum number of scenes is 8.
        Each scene's text length must be between 40 and 100 characters.
        Each scene's description length must be 200 characters or less

        There must be at least 5 scenes in total.
        At least each scene should have a narration of at least 10 characters.
        Write in a friendly, conversational tone in Korean.
        And the scene description should serve as a prompt for text-to-image (TTI) generation,  Do not include music descriptions.
        
        If there is no HTML, do not include imageUrl or videoUrl.
        """

        if page_html:
            user_prompt += f"""
            Please analyze the following HTML of the requested page and use it as a basis for your analysis.
            And please select and suggest images from the given HTML that would be good to include in each shorts script.
            But youtube related videos are not allowed to be included.
            Do not include images with an aspect ratio greater than 2:1.
            If there is no appropriate image, you can omit it.
            And please suggest different images for each scene.
            Description must be in Korean.
            {page_html}
        """

        content = [user_prompt]

        response = await self.client.aio.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=content,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=list[InitialScene],
                thinking_config=genai.types.ThinkingConfig(thinking_budget=0),
            ),
        )

        return json.loads(response.text)

    def translate(self, string: str, language: str):
        system_prompt = f"""
        Your task is to translate the input text into only {language} while maintaining the visual elements and composition details.
        Translate the input text to {language} only. Do not use any other language.
        The translation result must contain only {language}.
        Be careful not to mix English or other languages.
        """

        response = self.client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=[string],
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                thinking_config=genai.types.ThinkingConfig(thinking_budget=0),
                max_output_tokens=2048,
            ),
        )

        return response.text

    async def generate_shorts_image(self, user_prompt: str, max_retries=3):
        translated_prompt = self.translate(user_prompt, "English")

        translated_prompt = f"""
            - must not include Content that may appear violent
            - must not include Content that is excessively stimulating and could have negative effects on people

            {translated_prompt}
        """

        for attempt in range(max_retries):
            try:
                response = await self.client.aio.models.generate_images(
                    model="imagen-3.0-generate-002",
                    prompt=translated_prompt,
                    config=genai.types.GenerateImagesConfig(
                        number_of_images=1, aspect_ratio="1:1", person_generation="ALLOW_ADULT"
                    ),
                )

                if not response.generated_images:
                    raise Exception("No images generated from AI service")

                for generated_image in response.generated_images:
                    image_data = generated_image.image.image_bytes
                    if isinstance(image_data, bytes):
                        image = decode_base64_to_bytesio(image_data)
                    else:
                        image = BytesIO(image_data)

                    download_url = await self.io_processor.upload_file_s3(file_data=image, ext="png")
                    return download_url

            except Exception as e:
                logging.warning(str(e))
                if attempt == max_retries - 1:
                    raise ServerException(str(e))
                await asyncio.sleep(2 * (attempt + 1))  # 점진적 백오프

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

        max_retries = 3
        for attempt in range(max_retries):
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
                if attempt == max_retries - 1:
                    raise ServerException(f"TTS 생성에 {max_retries}번 시도 후 실패했습니다: {str(e)}")
                await asyncio.sleep(1)

    async def summarize_text(self, text: str):
        system_prompt = f"""
            You are an expert project title generator. 
            The following text will be used as the basis for a new project. 
            Your task is to create a concise, catchy, and relevant project title in Korean that best represents the content and purpose of the text. 
            Only return the title, without any additional explanation or formatting.
        """

        response = await self.client.aio.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=[system_prompt, text],
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                thinking_config=genai.types.ThinkingConfig(thinking_budget=0),
            ),
        )
        return response.text

    async def sync_scene_voice(self, text: str, duration: float, voice_url: str) -> str:

        system_prompt = f"""
            You are a professional YouTube Shorts caption generator. Create precise captions that sync with the provided voice audio.
            
            STRICT REQUIREMENTS:
            1. ALL text from the user's input must be included across the captions - no text should be omitted
            2. Each caption text must be EXACTLY 20 characters or less (including spaces and punctuation)
            3. Each caption must contain at least 4 meaningful characters (excluding spaces)
            4. If a caption would be too short (less than 4 non-space characters), combine it intelligently with adjacent text
            5. The total duration of all captions MUST exactly match the provided duration - this is non-negotiable
            6. REMOVE all commas(,), periods(.), and emojis from the captions, EXCEPT when they are part of a number (e.g., decimal points like 3.14 or thousand separators like 1,000 must be preserved).
            7. There must be at least a 0.02 second gap between the end of one caption and the start of the next caption. No captions should overlap in time.
            
            YOUTUBE SHORTS OPTIMIZATION:
            - Prioritize readability on mobile screens
            - Use natural Korean speech rhythm for timing
            - Consider viewer attention span and reading speed
        """

        user_prompt = f"""
            text: {text}
            duration: {duration}
        """

        voice_path = await self.io_processor.download_file(voice_url)
        with open(voice_path, "rb") as f:
            voice_data = f.read()
            voice_file = genai.types.Part.from_bytes(data=voice_data, mime_type="audio/mp3")

        response = await self.client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=[user_prompt, voice_file],
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=GoogleAiSimpleScene,
                thinking_config=genai.types.ThinkingConfig(thinking_budget=0),
            ),
        )

        return json.loads(response.text)

    async def summarize(self, text: str):
        system_prompt = f"""
            - Analyze the given text and identify its key concept words.
            - Return only 1 ~ 2 English words.
            - If you return 2 words, join them with a single "+" without spaces (e.g., pen+book).
            - If you return 1 word, output the single word only.
            - Output must contain only the words in English (no quotes, punctuation, or extra text).            
        """

        response = await self.client.aio.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=[system_prompt, text],
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                thinking_config=genai.types.ThinkingConfig(thinking_budget=0),
            ),
        )
        return response.text
