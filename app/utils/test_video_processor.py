from moviepy import VideoFileClip, CompositeVideoClip, ColorClip, TextClip
from typing import List, Tuple
from app.models.schemas import SceneRequest
from moviepy.audio.AudioClip import CompositeAudioClip
from moviepy import AudioFileClip
from pathlib import Path
from app.exceptions.http_exceptions import ServerException
from app.core.service_locator import get_tts_service


class VideoProcessor:
    def __init__(self, width: int = 1080, height: int = 1920, background_color: tuple = (0, 0, 0)):
        self.width = width
        self.height = height
        self.background_color = background_color

    def resize_video(self, video_clip: VideoFileClip) -> VideoFileClip:
        """비디오 크기를 조정하면서 종횡비 유지"""
        clip_width, clip_height = video_clip.w, video_clip.h
        width_ratio = self.width / clip_width
        height_ratio = self.height / clip_height

        scale_ratio = min(width_ratio, height_ratio)
        new_width = int(clip_width * scale_ratio)
        new_height = int(clip_height * scale_ratio)

        x_center = (self.width - new_width) // 2
        y_center = (self.height - new_height) // 2

        return video_clip.resized(width=new_width, height=new_height).with_position((x_center, y_center))

    def create_background(self, duration: float) -> ColorClip:
        """배경 클립 생성"""
        return ColorClip(size=(self.width, self.height), color=self.background_color).with_duration(duration)

    def combine_clips(
        self, clips: List[VideoFileClip], duration: float, audio: CompositeAudioClip = None
    ) -> CompositeVideoClip:
        """최종 비디오 생성"""
        final_video = CompositeVideoClip(clips)
        return final_video.with_duration(duration).with_audio(audio)

    def save_video(self, video: CompositeVideoClip, output_path: str) -> None:
        """비디오 파일 저장"""
        video.write_videofile(
            output_path, fps=30, codec="libx264", audio=True, audio_codec="aac", preset="ultrafast", threads=4
        )

    def calculate_total_duration(self, scenes: List[SceneRequest], base_path: Path) -> float:
        """전체 비디오 길이 계산"""
        total_duration = 0.0
        for scene in scenes:
            video_path = str(base_path / scene.video_url)
            with VideoFileClip(video_path) as clip:
                total_duration += clip.duration
        return total_duration

    def prepare_scene_parameters(self, scenes: List[SceneRequest], base_path: Path) -> List[Tuple[SceneRequest, float]]:
        """씬 파라미터 준비"""
        scene_params = []
        current_time = 0.0
        for scene in scenes:
            scene_params.append((scene, current_time))
            with VideoFileClip(str(base_path / scene.video_url)) as clip:
                current_time += clip.duration
        return scene_params

    async def process_video_clip(
        self, scene: SceneRequest, current_time: float, base_path: Path, audio_processor, text_processor
    ) -> Tuple[List[VideoFileClip], List[TextClip], List[AudioFileClip], float]:
        """비디오 클립 처리"""
        video_clips, text_clips, audio_clips = [], [], []

        # 비디오 처리
        video_path = base_path / scene.video_url
        if not video_path.exists():
            raise ServerException(f"비디오 파일을 찾을 수 없습니다: {video_path}")

        video_clip = VideoFileClip(str(video_path))
        duration = video_clip.duration

        resized_clip = self.resize_video(video_clip)
        resized_clip = resized_clip.with_start(current_time).with_duration(duration)
        video_clips.append(resized_clip)

        # 전체 글자 수 계산
        total_chars = sum(len(caption) for caption in scene.captions)
        tts_service = get_tts_service()

        # 각 캡션 처리
        for i, caption in enumerate(scene.captions):
            current_duration = (
                (len(caption) / total_chars) * duration if total_chars > 0 else duration / len(scene.captions)
            )

            # TTS 처리
            # tts_url = await tts_service.get_download_speech_url(caption, current_duration)
            # tts_audio = await audio_processor.create_audio_clip_from_url(tts_url)

            start_time = current_time + sum(
                (len(prev_caption) / total_chars) * duration if total_chars > 0 else duration / len(scene.captions)
                for prev_caption in scene.captions[:i]
            )

            # tts_audio = tts_audio.with_start(start_time)
            # audio_clips.append(tts_audio)

            # 텍스트 처리
            text_clip = text_processor.create_text_clip(caption, current_duration, start_time)
            text_clips.append(text_clip)

        return video_clips, text_clips, audio_clips, duration
