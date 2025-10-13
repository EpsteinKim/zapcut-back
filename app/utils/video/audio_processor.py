from moviepy import AudioFileClip
from app.core.config import EFFECT_PATH, ROOT_DIR
from app.models.schemas import SoundEffect, Scene
import librosa
import numpy as np
from typing import List, Dict, Tuple, Any
from app.utils.io_processor import IOProcessor
from pydub import AudioSegment
from io import BytesIO


class AudioProcessor:
    def __init__(self):
        self.io_processor = IOProcessor()
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
            audio = AudioSegment.from_file(audio_path)
            return len(audio) / 1000.0  # 밀리초를 초로 변환
        except Exception as e:
            raise Exception(f"오디오 길이 측정 실패: {str(e)}")

    async def get_audio_subclip(self, audio_url: str, text_scenes: list[str]) -> List[Dict[str, Any]]:
        # 1개의 원소만 있는 경우 바로 처리
        audio_path = await self.io_processor.download_file(audio_url)
        if len(text_scenes) == 1:
            total_audio_duration = self.get_audio_duration(audio_path)
            return [
                {
                    "text": text_scenes[0],
                    "voice_url": audio_url,
                    "duration": round(total_audio_duration, 2),
                }
            ]
        else:
            y, sr = librosa.load(audio_path)
            audio = AudioSegment.from_file(audio_path)
            times = librosa.times_like(
                librosa.feature.rms(y=y, frame_length=512, hop_length=256), sr=sr, hop_length=256
            )

            # 전체 오디오에서 RMS로 긴 묵음 구간(씬 경계)만 먼저 찾기
            S = librosa.feature.rms(y=y, frame_length=512, hop_length=256)
            threshold = np.mean(S) * 0.4
            speech_frames = S[0] > threshold

            long_silence_ranges = []
            silence_start = None
            for i, is_speech in enumerate(speech_frames):
                if not is_speech:
                    if silence_start is None:
                        silence_start = i
                elif silence_start is not None:
                    silence_duration = times[i] - times[silence_start]
                    if silence_duration >= 0.3:
                        long_silence_ranges.append((silence_start, i))
                    silence_start = None
            if silence_start is not None and len(times) - silence_start >= int(0.3 * sr / 256):
                long_silence_ranges.append((silence_start, len(times) - 1))

            # 씬 경계 계산 (씬 개수 = num_subclips)
            max_idx = len(times) - 1
            if len(long_silence_ranges) >= len(text_scenes) - 1:
                sorted_silences = sorted(long_silence_ranges, key=lambda x: times[x[1]] - times[x[0]], reverse=True)[
                    : len(text_scenes) - 1
                ]
                sorted_silences.sort(key=lambda x: x[0])
                scene_boundaries = [0]
                for silence in sorted_silences:
                    # 묵음 구간의 중간 지점을 씬 경계로 설정
                    mid_point_idx = int((silence[0] + silence[1]) / 2)
                    scene_boundaries.append(mid_point_idx)
                    # scene_boundaries.append(silence[0]) # 이전 상태로 되돌리기
                scene_boundaries.append(max_idx)
            else:
                scene_boundaries = [min(max_idx, int(i * max_idx / len(text_scenes))) for i in range(len(text_scenes))]
                scene_boundaries.append(max_idx)

            subclips_data = []
            total_audio_duration = self.get_audio_duration(audio_path)

            for i in range(len(text_scenes)):
                scene_start_idx = scene_boundaries[i]
                scene_end_idx = scene_boundaries[i + 1]
                scene_start = times[scene_start_idx]
                scene_end = times[min(scene_end_idx, len(times) - 1)]

                # Prevent negative duration or out-of-bounds
                if scene_start >= scene_end:
                    scene_end = scene_start + 1.0  # Ensure at least 1 second duration for robustness

                start_ms = int(scene_start * 1000)
                end_ms = int(scene_end * 1000)
                scene_audio = audio[start_ms:end_ms]

                # S3 업로드
                audio_buffer = BytesIO()
                scene_audio.export(audio_buffer, format="mp3")
                audio_buffer.seek(0)
                voice_url = await self.io_processor.upload_file_s3(file_data=audio_buffer, ext="mp3")

                scene_duration = round(scene_end - scene_start, 2)
                # 마지막 씬이고 총 지속시간이 부족한 경우 지속시간 조정
                if i == len(text_scenes) - 1:
                    current_total_duration = sum([s["duration"] for s in subclips_data]) + scene_duration
                    if current_total_duration < total_audio_duration:
                        scene_duration = round(scene_duration + (total_audio_duration - current_total_duration), 2)
                subclips_data.append(
                    {
                        "text": text_scenes[i],
                        "voice_url": voice_url,
                        "duration": scene_duration,
                    }
                )

            return subclips_data
