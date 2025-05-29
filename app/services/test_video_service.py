from app.core.service_locator import get_tts_service
from moviepy import CompositeVideoClip, VideoFileClip
from typing import List
from app.models.schemas import SceneRequest
from app.utils.test_video_processor import VideoProcessor
from app.utils.test_audio_processor import AudioProcessor
from app.utils.test_text_processor import TextProcessor
from pathlib import Path
import os
import asyncio
from app.core.config import ROOT_DIR


class TestVideoService:
    def __init__(self):
        self.video_processor = VideoProcessor()
        self.audio_processor = AudioProcessor()
        self.text_processor = TextProcessor()
        self.base_path = Path.cwd()

    async def create_video(
        self,
        scenes: List[SceneRequest],
        background_music_path: str,
        music_volume: float = 0.5,
        tts_volume: float = 1.0,
    ) -> CompositeVideoClip:
        # 전체 duration 계산
        total_duration = self.video_processor.calculate_total_duration(scenes, self.base_path)

        # 배경 생성
        background = self.video_processor.create_background(total_duration)
        all_clips = [background]

        # 씬 처리
        all_audio_clips = []
        scene_params = self.video_processor.prepare_scene_parameters(scenes, self.base_path)

        results = await asyncio.gather(
            *[
                self.video_processor.process_video_clip(
                    scene, start_time, self.base_path, self.audio_processor, self.text_processor
                )
                for scene, start_time in scene_params
            ]
        )

        for video_clips, text_clips, audio_clips, _ in results:
            all_clips.extend(video_clips + text_clips)
            all_audio_clips.extend(audio_clips)

        # 배경 음악 처리
        background_music = self.audio_processor.process_background_music(
            str(Path(ROOT_DIR) / background_music_path), total_duration, music_volume
        )

        # 최종 오디오 생성
        final_audio = self.audio_processor.create_final_audio(all_audio_clips, background_music, tts_volume)

        # 최종 비디오 생성
        return self.video_processor.combine_clips(all_clips, total_duration, final_audio)

    def save_video(self, video: CompositeVideoClip, output_path: str) -> None:
        """비디오 저장"""
        self.video_processor.save_video(video, output_path)
