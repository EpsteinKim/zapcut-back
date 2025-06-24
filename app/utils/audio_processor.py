from moviepy import AudioFileClip
from app.core.config import SOUND_PATH
from app.models.schemas import SoundEffect


class AudioProcessor:
    def __init__(self):
        pass

    def create_sound_effect_clip(self, current_time: float, sound_effect: SoundEffect):
        audio_clip = self.create_sound_effect(current_time, sound_effect)
        return audio_clip

    def create_sound_effect(self, current_time: float, sound_effect: SoundEffect):
        level_up_sound_path = SOUND_PATH + f"/{sound_effect.value.lower()}.mp3"
        level_up_audio_clip = AudioFileClip(level_up_sound_path)
        level_up_audio_clip = level_up_audio_clip.with_start(current_time).with_duration(0.5).with_volume_scaled(0.3)
        return level_up_audio_clip
