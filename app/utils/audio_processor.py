from moviepy import AudioFileClip
from moviepy.audio.fx.MultiplyVolume import MultiplyVolume
from moviepy.audio.fx.AudioLoop import AudioLoop
from moviepy.audio.AudioClip import CompositeAudioClip
from typing import List


class AudioProcessor:
    def __init__(self):
        pass

    def process_background_music(self, music_path: str, total_duration: float, volume: float = 0.5) -> AudioFileClip:
        background_music = AudioFileClip(music_path)

        if background_music.duration > total_duration:
            background_music = background_music.subclipped(0, total_duration)
        else:
            background_music = background_music.with_effects([AudioLoop(duration=total_duration)])

        return background_music.with_effects([MultiplyVolume(volume)])

    def create_final_audio(
        self, audio_clips: List[AudioFileClip], background_music: AudioFileClip = None, tts_volume: float = 1.0
    ) -> CompositeAudioClip:
        final_clips = []

        # TTS 오디오 처리
        for audio_clip in audio_clips:
            if tts_volume != 1.0:
                audio_clip = audio_clip.with_effects([MultiplyVolume(tts_volume)])
            final_clips.append(audio_clip)

        # 배경음악 추가
        if background_music is not None:
            final_clips.append(background_music)

        return CompositeAudioClip(final_clips) if final_clips else None
