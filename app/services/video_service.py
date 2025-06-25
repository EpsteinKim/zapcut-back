from moviepy import (
    ColorClip,
    VideoFileClip,
    CompositeVideoClip,
    AudioFileClip,
    CompositeAudioClip,
    ImageClip,
)
from moviepy.video import fx as vfx
from app.models.schemas import ShortsVideoRequest
from app.core.service_locator import get_google_ai_service
from app.utils.video_processor import VideoProcessor
from app.utils.audio_processor import AudioProcessor
from app.utils.text_processor import TextProcessor
from app.utils.io_processor import IOProcessor
import tempfile
import os
import shutil
from app.exceptions.http_exceptions import ServerException
from dataclasses import dataclass
from io import BytesIO
from PIL import Image
import numpy as np
import mimetypes


@dataclass
class Processors:
    video: VideoProcessor
    audio: AudioProcessor
    text: TextProcessor
    IO: IOProcessor


class VideoService:
    def __init__(self):
        self.video_width = 1080
        self.video_height = 1920
        self.temp_dir = tempfile.mkdtemp()
        self.processors = Processors(
            video=VideoProcessor(self.video_width, self.video_height),
            audio=AudioProcessor(),
            text=TextProcessor(self.video_width, self.video_height),
            IO=IOProcessor(),
        )

    def __del__(self):
        if hasattr(self, "temp_dir") and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _is_gif_file(self, file_path: str) -> bool:
        """GIF 파일인지 확인"""
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

    async def create_video(self, request: ShortsVideoRequest) -> str:
        google_ai_service = get_google_ai_service()
        video_clips = []
        text_clips = []
        audio_clips = []
        total_duration = sum(scene.duration for scene in request.scenes)

        background = ColorClip(size=(self.video_width, self.video_height), color=(0, 0, 0), duration=total_duration)
        video_clips.append(background)
        if request.background_music_url:
            music_path = await self.processors.IO.download_file(request.background_music_url)
            background_music = AudioFileClip(music_path).with_volume_scaled(0.3).with_duration(total_duration)
            audio_clips.append(background_music)

        current_time = 0  # 합성 비디오를 만들긴 위한 누적 시간
        used_image_urls = []
        for scene in request.scenes:
            if scene.video_url is not None:
                video_path = await self.processors.IO.download_file(scene.video_url)
                target_clip = VideoFileClip(video_path)
            elif scene.image_url is not None:
                image_path = await self.processors.IO.download_file(scene.image_url)

                # GIF 파일인지 확인하고 적절히 처리
                if self._is_gif_file(image_path):
                    target_clip = VideoFileClip(image_path).with_effects([vfx.Loop(duration=scene.duration)])
                else:
                    # 일반 이미지 처리
                    pil_image = Image.open(image_path)
                    if pil_image.mode != "RGB":
                        pil_image = pil_image.convert("RGB")
                    image_array = np.array(pil_image)
                    target_clip = ImageClip(image_array, duration=scene.duration)
            else:
                (upload_url, image_buffer) = await google_ai_service.generate_shorts_image(scene.description)
                pil_image = Image.open(image_buffer)
                if pil_image.mode != "RGB":
                    pil_image = pil_image.convert("RGB")
                image_array = np.array(pil_image)
                target_clip = ImageClip(image_array, duration=scene.duration)
                used_image_urls.append(upload_url)

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
                        self.processors.text.create_text_clip(
                            caption=caption,
                            current_time=current_time,
                        )
                    )
                    if caption.sound_effect is not None:
                        audio_clips.append(
                            self.processors.audio.create_sound_effect_clip(
                                current_time + caption.start_time, caption.sound_effect
                            )
                        )

            if scene.voice_url:
                voice_path = await self.processors.IO.download_file(scene.voice_url)
                audio_clip = AudioFileClip(voice_path)
                audio_clip = audio_clip.with_start(current_time)
                audio_clips.append(audio_clip)

            current_time += scene.duration

        final_audio_clip = CompositeAudioClip(audio_clips)

        final_video_clip = CompositeVideoClip(video_clips + text_clips)
        final_video_clip = final_video_clip.with_audio(final_audio_clip).with_duration(total_duration)
        output_path = self.processors.video.save_video(final_video_clip)

        with open(output_path, "rb") as f:
            video_bytes = f.read()
        video_buffer = BytesIO(video_bytes)

        try:
            download_url = await self.processors.IO.upload_file_s3(1, file_data=video_buffer, ext="mp4")

            for clip in video_clips:
                clip.close()
            for clip in text_clips:
                clip.close()
            for clip in audio_clips:
                clip.close()

            final_video_clip.close()
            final_audio_clip.close()
            background.close()

            return download_url
        except Exception as e:
            raise ServerException(f"파일 업로드 실패: {str(e)}")
