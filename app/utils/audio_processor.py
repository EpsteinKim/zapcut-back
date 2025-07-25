from moviepy import AudioFileClip
from app.core.config import EFFECT_PATH
from app.models.schemas import SoundEffect


class AudioProcessor:
    def __init__(self):
        pass

    def create_sound_effect_clip(self, current_time: float, sound_effect: SoundEffect):
        audio_clip = self.create_sound_effect(current_time, sound_effect)
        return audio_clip

    def create_sound_effect(self, current_time: float, sound_effect: SoundEffect):
        level_up_sound_path = EFFECT_PATH + f"/{sound_effect.value.lower()}.mp3"
        level_up_audio_clip = AudioFileClip(level_up_sound_path)
        level_up_audio_clip = level_up_audio_clip.with_start(current_time).with_duration(0.5).with_volume_scaled(0.3)
        return level_up_audio_clip

    def get_audio_duration(self, audio_path: str) -> float:
        """오디오 파일의 길이를 초 단위로 반환합니다."""
        try:
            with AudioFileClip(audio_path) as audio:
                return audio.duration
        except Exception as e:
            raise Exception(f"오디오 길이 측정 실패: {str(e)}")
