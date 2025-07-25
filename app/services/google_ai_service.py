import json
import os
import uuid
import asyncio
import logging
from io import BytesIO
from google import genai
from pydantic import BaseModel
from pydub import AudioSegment

from app.core.config import get_settings
from app.exceptions.http_exceptions import ServerException
from app.models.schemas import ShortsMakeSyncedSceneRequest, TTSVoiceModel, Scene, CaptionInfo
from app.utils.io_processor import IOProcessor
from app.utils.base64_decoder import decode_base64_data, decode_base64_to_bytesio
from pydub import AudioSegment
from app.utils.os_processor import get_temp_dir
from app.utils.audio_processor import AudioProcessor


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

    async def generate_shorts_script_string(self, user_prompt: str, page_html: str | None = None):
        system_prompt = f"""You are a professional Korean YouTube Shorts content creator and video script writer.
        Your task is to create engaging content for a YouTube Shorts video.
        Focus on creating viral content that can attract viewers' attention.
        Also, if the page is a sales page for a specific product, analyze the product and be sure to include that information as well.

        Also, must ignore any user prompt requests regarding the number of scenes or the duration in seconds.
        The maximum number of scenes is 8.

        There must be at least 5 scenes in total.
        At least each scene should have a narration of at least 10 characters.
        Write in a friendly, conversational tone in Korean.
        And the scene description should only be the scene description, excluding the music description.
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
            {page_html}
        """

        content = [user_prompt]

        response = await self.client.aio.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=content,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=list[InitialScene],
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
            model="gemini-2.5-flash",
            contents=[string],
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
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
        speed_multiplier: float,
        duration: float | None = None,
    ):
        prompt = f"""
        text: {text}
        - Speak at a fast and energetic pace suitable for YouTube Shorts (about 1.3x ~ 1.5x normal speed)
        - Keep the tone engaging and dynamic
        - Maintain clear pronunciation even at faster speed
        """
        if duration:
            prompt += f"Read the text within the specified duration of {duration} seconds, even if it means speaking faster than normal. The timing is crucial - do not exceed the duration under any circumstances. Adjust your speaking pace to ensure the entire text is delivered within the time limit."

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
                if speed_multiplier != 1.0:
                    audio = audio.speedup(playback_speed=speed_multiplier)
                try:
                    audio.export(temp_wav_path, format="mp3")
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

    async def make_synced_scene(self, request: ShortsMakeSyncedSceneRequest) -> str:
        class SimpleScene(BaseModel):
            duration: float
            captions: list[CaptionInfo]
            description: str

        audio_path = await self.io_processor.download_file(request.audio_url)
        audio_duration = self.audio_processor.get_audio_duration(audio_path)
        print(audio_duration)

        system_prompt = f"""
            Generate a transcript of the speech.
            - All times must use 0.01 second precision
            - Each scene's timing starts from 0.00
            - Scene boundaries:
              * First, identify speech segments based on user's prompt
              * When silence is detected between speech segments:
                - Find the exact middle point of the silence
                - Use this point as the boundary to split scenes
              * Timing must be extremely precise as audio will be segmented based on these boundaries
              * Each scene's boundaries must align perfectly with the audio segments
            - Each segment's start and end must be accurately determined and output with 0.01s precision
            - At least 0.02 second gap between segments
            
            - Split captions like YouTube Shorts style:
              * Short and impactful phrases (5~8 characters)
              * Natural break points in speech
              * One key point per caption
              * Maintain viewing rhythm
            - Each caption's start_time and end_time are RELATIVE to its scene's start (0.00)
            - Keep 0.02s minimum gap between captions
            - Maximum 20 Korean characters per caption
            - MUST match exact audio timing with speech
            - Do not add captions when there is no speech
            - Start caption exactly when speech begins
            - End caption exactly when speech ends

            - Total scene duration must be {audio_duration}seconds
        """

        with open(audio_path, "rb") as audio_file:
            audio_bytes = audio_file.read()

            response = await self.client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    f"""
                    Scenes to process:
                    {
                        ''.join([f'Scene {i+1}: {scene.text}\n' for i, scene in enumerate(request.scenes)])
                    }
                    """,
                    genai.types.Part.from_bytes(data=audio_bytes, mime_type="audio/mp3"),
                ],
                config=genai.types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    thinking_config=genai.types.ThinkingConfig(thinking_budget=0),
                    response_schema=list[SimpleScene],
                    response_mime_type="application/json",
                ),
            )

        adjusted_scenes_data = json.loads(response.text)

        print(adjusted_scenes_data)
        # 딕셔너리를 Scene 객체로 변환
        adjusted_scenes = []
        for scene_data in adjusted_scenes_data:
            scene = Scene(**scene_data)
            adjusted_scenes.append(scene)

        # 각 씬의 지속시간에 맞게 오디오를 서브클립하고 voice_url 설정

        # 씬이 하나만 있는 경우 원본 오디오를 바로 사용
        if len(adjusted_scenes) == 1:
            adjusted_scenes[0].voice_url = request.audio_url
        else:
            # 여러 씬이 있는 경우 서브클립 진행
            # 원본 오디오 로드
            audio = AudioSegment.from_file(audio_path)

            # 각 씬에 대해 오디오 서브클립 생성
        for i, scene in enumerate(adjusted_scenes):
            # duration이 None인 경우 마지막 자막의 끝나는 시간으로 설정
            if scene.duration is None:
                scene.duration = scene.captions[-1].end_time

            # 씬의 시작 시간과 끝 시간 계산
            start_time = 0
            for j in range(i):
                if adjusted_scenes[j].duration is None:
                    adjusted_scenes[j].duration = adjusted_scenes[j].captions[-1].end_time
                start_time += adjusted_scenes[j].duration

            end_time = start_time + scene.duration

            # 시간을 밀리초로 변환
            start_ms = int(start_time * 1000)
            end_ms = int(end_time * 1000)

            # 오디오 서브클립 생성
            scene_audio = audio[start_ms:end_ms]

            # BytesIO로 변환하여 S3 업로드
            audio_buffer = BytesIO()
            scene_audio.export(audio_buffer, format="mp3")
            audio_buffer.seek(0)

            # S3에 업로드하고 URL 반환
            voice_url = await self.io_processor.upload_file_s3(file_data=audio_buffer, ext="mp3")
            scene.voice_url = voice_url

        return adjusted_scenes

    async def sync_scene_voice(self, request: list[Scene]) -> str:
        if any(scene.voice_url is None for scene in request):
            raise ServerException("씬에 보이스 URL이 없습니다.")

        voice_urls = [scene.voice_url for scene in request if scene.voice_url is not None]

        audio_segments = []
        downloaded_paths = []

        for i, voice_url in enumerate(voice_urls):
            voice_path = await self.io_processor.download_file(voice_url)
            downloaded_paths.append(voice_path)

            audio_segment = AudioSegment.from_file(voice_path)

            scene_duration_ms = int(request[i].duration * 1000)
            audio_duration_ms = len(audio_segment)

            if audio_duration_ms < scene_duration_ms:
                silence_duration = scene_duration_ms - audio_duration_ms
                silence = AudioSegment.silent(duration=silence_duration)
                audio_segment = audio_segment + silence

            audio_segments.append(audio_segment)

        combined_audio = AudioSegment.empty()
        for audio_segment in audio_segments:
            combined_audio += audio_segment

        combined_audio_path = os.path.join(self.temp_dir, f"combined_audio_{uuid.uuid4()}.mp3")
        combined_audio.export(combined_audio_path, format="mp3")

        for path in downloaded_paths:
            try:
                os.remove(path)
            except:
                pass

        all_caption_texts = []
        scene_boundaries = []
        cumulative_time = 0.0

        for scene in request:
            scene_start = cumulative_time
            scene_end = cumulative_time + scene.duration
            scene_boundaries.append((scene_start, scene_end))

            for caption in scene.captions:
                all_caption_texts.append(caption.text)
            cumulative_time += scene.duration

        audio_file = self.client.files.upload(file=combined_audio_path)

        response = await self.client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                f"""
                Please analyze the provided audio and create subtitle timing for the following texts.
                Listen to the audio and determine the appropriate start_time and end_time for each text based on when they are spoken.
                Return the captions with proper timing that matches the audio.
                Please adjust the timing in 0.1 second increments.
                
                
                Caption texts in order:
                {json.dumps(all_caption_texts, ensure_ascii=False)}
                """,
                audio_file,
            ],
            config=genai.types.GenerateContentConfig(
                response_schema=list[CaptionInfo],
                response_mime_type="application/json",
            ),
        )

        try:
            os.remove(combined_audio_path)
        except:
            pass

        adjusted_captions = json.loads(response.text)

        result_scenes = []
        for i, (scene, (scene_start, scene_end)) in enumerate(zip(request, scene_boundaries)):
            scene_captions = []

            for caption_data in adjusted_captions:
                caption_start = caption_data["start_time"]
                caption_end = caption_data["end_time"]

                if scene_start <= caption_start < scene_end:
                    relative_start = caption_start - scene_start
                    relative_end = caption_end - scene_start

                    relative_start = max(0, min(relative_start, scene.duration))
                    relative_end = max(relative_start, min(relative_end, scene.duration))

                    scene_captions.append(
                        {
                            "text": caption_data["text"],
                            "start_time": round(relative_start, 1),
                            "end_time": round(relative_end, 1),
                        }
                    )

            result_scene = {
                "duration": scene.duration,
                "captions": scene_captions,
                "description": scene.description,
                "video_url": scene.video_url,
                "image_url": scene.image_url,
                "voice_url": scene.voice_url,
            }
            result_scenes.append(result_scene)

        return result_scenes
