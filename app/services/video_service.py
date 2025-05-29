from moviepy import VideoFileClip, CompositeVideoClip, TextClip, AudioFileClip
from typing import List, Optional, Tuple
from app.models.schemas import SceneRequest, ShortsSceneRequest
from app.core.service_locator import get_tts_service
from app.utils.video_processor import VideoProcessor
from app.utils.audio_processor import AudioProcessor
from app.utils.text_processor import TextProcessor
from app.utils.io_processor import IOProcessor
import tempfile
import os
import shutil
import uuid
from app.exceptions.http_exceptions import ServerException
from dataclasses import dataclass
from io import BytesIO


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

    async def create_shorts_scene(self, request: ShortsSceneRequest) -> str:
        tts_service = get_tts_service()
        video_clips = []
        text_clips = []
        audio_clips = []

        total_duration = max(caption.end_time for caption in request.captions)
        background = self.processors.video.create_background(total_duration)
        video_clips.append(background)

        if request.video_url is None and request.image_url is None:
            raise ServerException("비디오 또는 이미지 URL이 필요합니다.")

        target_path = await self.processors.IO.download_file(
            request.video_url if request.video_url is not None else request.image_url
        )

        target_clip = VideoFileClip(target_path)

        # 비디오 크기 조정
        clip_width, clip_height = target_clip.w, target_clip.h
        width_ratio = self.video_width / clip_width
        height_ratio = self.video_height / clip_height

        scale_ratio = min(width_ratio, height_ratio)
        new_width = int(clip_width * scale_ratio)
        new_height = int(clip_height * scale_ratio)

        x_center = (self.video_width - new_width) // 2
        y_center = (self.video_height - new_height) // 2
        target_clip = target_clip.resized(width=new_width, height=new_height).with_position((x_center, y_center))
        # 비디오 크기 조정 끝

        target_clip = target_clip.with_duration(total_duration)
        video_clips.append(target_clip)

        for caption in request.captions:
            text_clip = self.processors.text.create_text_clip(
                caption=caption.text, duration=caption.end_time - caption.start_time, start_time=caption.start_time
            )
            text_clips.append(text_clip)

            try:
                tts_url = await tts_service.get_download_speech_url(caption.text, caption.end_time - caption.start_time)
                tts_path = await self.processors.IO.download_file(tts_url, "mp3")
                tts_audio = AudioFileClip(tts_path)
                tts_audio = tts_audio.with_start(caption.start_time)
                audio_clips.append(tts_audio)
            except Exception as e:
                print(f"TTS 생성 실패: {str(e)}")
                continue

        all_clips = video_clips + text_clips

        final_audio = None
        if audio_clips:
            final_audio = self.processors.audio.create_final_audio(audio_clips)

        final_video = self.processors.video.create_final_video(all_clips, total_duration, final_audio)

        output_path = os.path.join(self.temp_dir, f"shorts_scene_{uuid.uuid4()}.mp4")

        self.processors.video.save_video(final_video, output_path)

        with open(output_path, "rb") as f:
            video_bytes = f.read()
        video_buffer = BytesIO(video_bytes)

        try:
            upload_url = await self.processors.IO.upload_file(1, video_buffer, "mp4")
            return upload_url
        except Exception as e:
            raise ServerException(f"파일 업로드 실패: {str(e)}")

    def __del__(self):
        if hasattr(self, "temp_dir") and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
