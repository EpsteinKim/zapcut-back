from moviepy import TextClip, ColorClip, CompositeVideoClip, AudioFileClip, VideoFileClip
from moviepy.audio.fx.MultiplyVolume import MultiplyVolume
from moviepy.audio.fx.AudioLoop import AudioLoop
from moviepy.audio.AudioClip import CompositeAudioClip
import os
import aiohttp

# import tempfile  # 제거
import uuid
from app.exceptions.http_exceptions import ServerException

from app.utils.os_processor import get_temp_dir


class VideoProcessor:
    def __init__(self, video_width: int, video_height: int):
        self.video_width = video_width
        self.video_height = video_height
        # self.temp_dir = tempfile.mkdtemp()  # 기존 코드
        self.temp_dir = get_temp_dir("video_processor")

    def create_background(self, duration: float) -> ColorClip:
        try:
            with ColorClip(
                size=(self.video_width, self.video_height), color=(0, 0, 0), duration=duration
            ) as background_clip:
                return background_clip
        except Exception as e:
            raise ServerException(f"배경 비디오 생성 실패: {str(e)}")

    def create_final_video(self, clips: list, duration: float, audio: CompositeAudioClip = None) -> CompositeVideoClip:
        final_video = CompositeVideoClip(clips)
        if audio:
            final_video = final_video.with_duration(duration).with_audio(audio)
        else:
            final_video = final_video.with_duration(duration)
        return final_video

    def save_video(self, video: CompositeVideoClip):
        output_path = os.path.join(self.temp_dir, f"shorts_video_{uuid.uuid4()}.mp4")
        video.write_videofile(output_path, codec="libx264", audio_codec="aac", threads=4, fps=24, audio_fps=24000)
        return output_path

    def __del__(self):
        if hasattr(self, "temp_dir") and os.path.exists(self.temp_dir):
            import shutil

            shutil.rmtree(self.temp_dir)
