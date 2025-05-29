from moviepy.audio.AudioClip import CompositeAudioClip
from moviepy import AudioFileClip
from moviepy.audio.fx.MultiplyVolume import MultiplyVolume
from moviepy.audio.fx.AudioLoop import AudioLoop
from typing import List
import aiohttp
import os
import tempfile
import uuid
from app.exceptions.http_exceptions import ServerException


class AudioProcessor:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()

    async def create_audio_clip_from_url(self, url: str) -> AudioFileClip:
        """URL에서 오디오 클립 생성"""
        temp_audio_path = None
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise ServerException(f"Failed to download audio from {url}")

                    temp_audio_path = os.path.join(self.temp_dir, f"temp_audio_{uuid.uuid4()}.mp3")
                    audio_data = await response.read()

                    with open(temp_audio_path, "wb") as f:
                        f.write(audio_data)

                    audio_clip = AudioFileClip(temp_audio_path)

                    if os.path.exists(temp_audio_path):
                        os.remove(temp_audio_path)

                    return audio_clip
        except Exception as e:
            if temp_audio_path and os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
            raise e

    def process_background_music(self, music_path: str, total_duration: float, volume: float) -> AudioFileClip:
        """배경 음악 처리"""
        background_music = AudioFileClip(music_path)
        if background_music.duration > total_duration:
            background_music = background_music.subclipped(0, total_duration)
        else:
            background_music = background_music.with_effects([AudioLoop(duration=total_duration)])

        return background_music.with_effects([MultiplyVolume(volume)])

    def create_final_audio(
        self, audio_clips: List[AudioFileClip], background_music: AudioFileClip, tts_volume: float
    ) -> CompositeAudioClip:
        """최종 오디오 생성"""
        for audio_clip in audio_clips:
            audio_clip = audio_clip.with_effects([MultiplyVolume(tts_volume)])
        if background_music:
            audio_clips.append(background_music)
        return CompositeAudioClip(audio_clips)

    def __del__(self):
        """임시 디렉토리 정리"""
        if hasattr(self, "temp_dir") and os.path.exists(self.temp_dir):
            import shutil

            shutil.rmtree(self.temp_dir)
