from moviepy import (
    ColorClip,
    VideoFileClip,
    CompositeVideoClip,
    AudioFileClip,
    CompositeAudioClip,
    ImageClip,
)
from moviepy.video import fx as vfx
from app.models.schemas import ShortsVideoRequest, BGMType, Scene
from app.core.service_locator import get_google_ai_service
from app.utils.video_processor import VideoProcessor
from app.utils.audio_processor import AudioProcessor
from app.utils.text_processor import TextProcessor
from app.utils.io_processor import IOProcessor
from app.exceptions.http_exceptions import ServerException
from io import BytesIO
from PIL import Image
import numpy as np
import mimetypes
import asyncio
import logging
import uuid
from app.core.config import TEMP_DIR
from app.utils.os_processor import get_temp_dir
import os


class VideoService:
    def __init__(self):
        self.video_width = 1080
        self.video_height = 1920
        self.temp_dir = get_temp_dir("video_service")
        self.video_processor = VideoProcessor(self.video_width, self.video_height)
        self.audio_processor = AudioProcessor()
        self.text_processor = TextProcessor(self.video_width, self.video_height)
        self.io_processor = IOProcessor()

    def _is_gif_file(self, file_path: str) -> bool:
        # 확장자로 먼저 확인
        if file_path.lower().endswith(".gif"):
            return True

        # MIME 타입으로 확인
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type == "image/gif":
            return True

        # 파일 헤더로 확인
        try:
            with open(file_path, "rb") as f:
                header = f.read(6)
                return header.startswith(b"GIF87a") or header.startswith(b"GIF89a")
        except:
            return False

    async def _process_scene_media(self, scene, google_ai_service):
        if scene.video_url is not None:
            video_path = await self.io_processor.download_file(scene.video_url)
            target_clip = VideoFileClip(video_path)
            return target_clip, None
        elif scene.image_url is not None:
            image_path = await self.io_processor.download_file(scene.image_url)

            # GIF 파일인지 확인하고 적절히 처리
            if self._is_gif_file(image_path):
                target_clip = VideoFileClip(image_path).with_effects([vfx.Loop(duration=scene.duration)])
                return target_clip, None
            else:
                # 일반 이미지 처리
                with Image.open(image_path) as pil_image:
                    if pil_image.mode != "RGB":
                        pil_image = pil_image.convert("RGB")
                    image_array = np.array(pil_image)
                target_clip = ImageClip(image_array, duration=scene.duration)
                return target_clip, None
        else:
            (upload_url, image_buffer) = await google_ai_service.generate_shorts_image(scene.description)
            with Image.open(image_buffer) as pil_image:
                if pil_image.mode != "RGB":
                    pil_image = pil_image.convert("RGB")
                image_array = np.array(pil_image)
            target_clip = ImageClip(image_array, duration=scene.duration)
            return target_clip, upload_url

    async def _process_scene_voice(self, scene):
        if scene.voice_url:
            voice_path = await self.io_processor.download_file(scene.voice_url)
            audio_clip = AudioFileClip(voice_path)
            return audio_clip
        return None

    async def create_video(self, request: ShortsVideoRequest) -> str:
        google_ai_service = get_google_ai_service()
        video_clips = []
        text_clips = []
        audio_clips = []
        total_duration = sum(scene.duration for scene in request.scenes)

        background = ColorClip(size=(self.video_width, self.video_height), color=(0, 0, 0), duration=total_duration)
        video_clips.append(background)

        background_music = None
        if request.bgm_id == BGMType.CUSTOM and request.custom_bgm_url:
            music_path = await self.io_processor.download_file(request.custom_bgm_url)
            background_music = AudioFileClip(music_path)
        elif request.bgm_id != BGMType.NONE:
            music_path = BGMType.get_file_path(request.bgm_id)
            if music_path:
                background_music = AudioFileClip(music_path)

        if background_music:
            background_music = background_music.with_volume_scaled(request.music_volume).with_duration(total_duration)
            audio_clips.append(background_music)

        # 모든 scene의 미디어와 음성을 병렬로 처리
        media_tasks = [self._process_scene_media(scene, google_ai_service) for scene in request.scenes]
        voice_tasks = [self._process_scene_voice(scene) for scene in request.scenes]

        try:
            # 병렬 실행
            media_results = await asyncio.gather(*media_tasks)
            voice_results = await asyncio.gather(*voice_tasks)
        except Exception as e:
            logging.error(f"Critical error in parallel processing: {str(e)}")
            raise ServerException(
                message=f"병렬 처리 중 오류 발생: {str(e)}",
                data={"original_error": str(e), "error_type": e.__class__.__name__},
            )

        current_time = 0  # 합성 비디오를 만들기 위한 누적 시간

        for i, scene in enumerate(request.scenes):
            target_clip, upload_url = media_results[i]
            voice_clip = voice_results[i]

            target_clip = (
                target_clip.with_duration(scene.duration)
                .with_start(current_time)
                .with_end(current_time + scene.duration)
            )

            clip_width, clip_height = target_clip.w, target_clip.h
            width_ratio = self.video_width / clip_width
            height_ratio = self.video_height / clip_height

            scale_ratio = min(width_ratio, height_ratio)
            new_width = int(clip_width * scale_ratio)
            new_height = int(clip_height * scale_ratio)

            x_center = (self.video_width - new_width) // 2
            y_center = (self.video_height - new_height) // 2
            target_clip = target_clip.resized(width=new_width, height=new_height).with_position((x_center, y_center))
            video_clips.append(target_clip)

            if scene.captions:
                for caption in scene.captions:
                    text_clips.extend(
                        self.text_processor.create_text_clip(
                            caption=caption,
                            current_time=current_time,
                        )
                    )
                    if caption.sound_effect is not None:
                        audio_clips.append(
                            self.audio_processor.create_sound_effect_clip(
                                current_time + caption.start_time, caption.sound_effect
                            )
                        )

            if voice_clip:
                voice_clip = voice_clip.with_start(current_time)
                audio_clips.append(voice_clip)

            current_time += scene.duration

        final_audio_clip = CompositeAudioClip(audio_clips)

        final_video_clip = CompositeVideoClip(video_clips + text_clips)
        final_video_clip = final_video_clip.with_audio(final_audio_clip).with_duration(total_duration)
        output_path = self.video_processor.save_video(final_video_clip)

        try:
            download_url = await self.io_processor.upload_file_s3(file_path=output_path, ext="mp4")

            for clip in video_clips:
                clip.close()
            for clip in text_clips:
                clip.close()
            for clip in audio_clips:
                clip.close()

            final_video_clip.close()
            final_audio_clip.close()
            background.close()
            if os.path.exists(output_path):
                os.remove(output_path)
            if music_path and os.path.exists(music_path) and request.bgm_id == BGMType.CUSTOM:
                os.remove(music_path)

            return download_url
        except Exception as e:
            raise ServerException(
                message=f"파일 업로드 중 오류 발생: {str(e)}",
                data={"original_error": str(e), "error_type": e.__class__.__name__},
            )
