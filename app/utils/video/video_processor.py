from moviepy import *
from moviepy.audio.fx.MultiplyVolume import MultiplyVolume
from moviepy.audio.fx.AudioLoop import AudioLoop
from moviepy.audio.AudioClip import CompositeAudioClip
from moviepy.video import fx as vfx
import numpy as np
import os
from PIL import Image, ImageFilter
from typing import Literal

# import tempfile  # 제거
import uuid
from app.exceptions.http_exceptions import ServerException
from app.models.schemas import TransitionTypeModel, TransitionType
from app.utils.os_processor import get_temp_dir


class VideoProcessor:
    def __init__(self, video_width: int, video_height: int):
        self.video_width = video_width
        self.video_height = video_height
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

    def create_transition_clip(
        self,
        clip: VideoClip,
        type: Literal["in", "out"] = "in",
        duration: float = 0.5,
        transition_types: list[TransitionTypeModel] | None = [],
    ) -> VideoClip:
        if len(transition_types) == 0:
            return clip

        def combined_effect_function(get_frame, t):
            frame = get_frame(t)  # NumPy 배열 (현재 클립의 프레임)
            current_pil_img = Image.fromarray(frame)  # PIL 이미지로 변환

            # 트랜지션 진행률 및 이징 계산 (모든 효과에 공통)
            if type == "in":
                progress = min(1.0, max(0.0, t / duration))
            elif type == "out":
                progress_raw = (t - (clip.duration - duration)) / duration
                if t > clip.duration - 0.05:
                    progress = 1.0
                else:
                    progress = min(1.0, max(0.0, progress_raw))
            else:
                # 효과가 적용되지 않는 구간
                return frame

            # Step 1: 이미지 레벨 효과 적용
            if TransitionType.ROTATE in transition_types:
                current_pil_img = self._apply_rotate_effect(current_pil_img, progress, type)
            if TransitionType.SCALE in transition_types:
                current_pil_img = self._apply_scale_effect(current_pil_img, progress, type)
            if TransitionType.BLUR in transition_types:
                current_pil_img = self._apply_blur_effect(current_pil_img, progress, type)

            slide_type = [t for t in transition_types if "SLIDE" in t]
            if len(slide_type) >= 1:
                slide_type = slide_type[0]
                current_pil_img = self._apply_slide_effect(current_pil_img, progress, type, slide_type)
            final_frame_np = np.array(current_pil_img).astype(frame.dtype)

            return final_frame_np

        final_clip = clip.transform(combined_effect_function)
        if TransitionType.BLACK_WHITE in transition_types:
            final_clip = final_clip.with_effects([vfx.BlackAndWhite()])

        return final_clip

    # ease in out 효과 적용
    def _progress_to_eased_progress(self, progress: float, type: Literal["in", "out"]) -> float:
        if type == "in":
            return 1 - (1 - progress) ** 2  # Ease-out Quadratic
        elif type == "out":
            return progress**2  # Ease-in Quadratic
        else:
            return progress  # 효과 없는 구간

    def _apply_rotate_effect(self, pil_img: Image.Image, progress: float, type: Literal["in", "out"]) -> Image.Image:
        angle = -360  # 총 회전 각도 (필요시 파라미터화)
        current_angle = angle * self._progress_to_eased_progress(progress, type)
        return pil_img.rotate(current_angle, expand=True, resample=Image.Resampling.BICUBIC)

    def _apply_scale_effect(self, pil_img: Image.Image, progress: float, type: Literal["in", "out"]) -> Image.Image:
        # max_scale_factor = 1.2  # 최대 확대 비율 (필요시 파라미터화)

        if type == "in":
            current_scale = 0.3 + (1.0 - 0.3) * self._progress_to_eased_progress(progress, type)
        elif type == "out":
            current_scale = 1.0 + (0.3 - 1.0) * self._progress_to_eased_progress(progress, type)
        else:
            current_scale = 1.0  # 기본값

        original_width, original_height = pil_img.size
        new_width = int(original_width * current_scale)
        new_height = int(original_height * current_scale)

        # 0으로 나누는 오류 방지
        if new_width <= 0:
            new_width = 1
        if new_height <= 0:
            new_height = 1

        return pil_img.resize((new_width, new_height), Image.Resampling.BICUBIC)

    def _apply_blur_effect(self, pil_img: Image.Image, progress: float, type: Literal["in", "out"]) -> Image.Image:
        max_blur_radius = 50  # 최대 블러 강도 (필요시 파라미터화)

        if type == "in":
            current_blur_radius = max_blur_radius * (1 - self._progress_to_eased_progress(progress, type))
        elif type == "out":
            current_blur_radius = max_blur_radius * self._progress_to_eased_progress(progress, type)
        else:
            current_blur_radius = 0

        if current_blur_radius > 0:
            return pil_img.filter(ImageFilter.GaussianBlur(radius=current_blur_radius))
        else:
            return pil_img

    def _apply_slide_effect(
        self,
        pil_img: Image.Image,
        progress: float,
        type: Literal["in", "out"],
        transcription_type: Literal["SLIDE_DOWN", "SLIDE_UP", "SLIDE_LEFT", "SLIDE_RIGHT"],
    ) -> Image.Image:
        # 최종 출력 캔버스 생성 (비디오 해상도 크기)
        final_canvas = Image.new("RGB", (self.video_width, self.video_height), (0, 0, 0))  # 검은색 배경

        # pil_img를 final_canvas에 붙여넣을 위치 계산
        paste_x = 0
        paste_y = 0

        # 비디오 중앙 위치
        video_center_x = self.video_width / 2
        video_center_y = self.video_height / 2

        # 이미지의 중앙 위치
        image_center_x = pil_img.width / 2
        image_center_y = pil_img.height / 2

        progress_eased = self._progress_to_eased_progress(progress, type)

        if transcription_type == "SLIDE_DOWN":
            if type == "in":
                start_y_offset = -pil_img.height  # 완전히 화면 위로
                end_y_offset = video_center_y - image_center_y
            elif type == "out":
                start_y_offset = video_center_y - image_center_y
                end_y_offset = self.video_height  # 완전히 화면 아래로
            paste_y = start_y_offset + (end_y_offset - start_y_offset) * progress_eased
            paste_x = video_center_x - image_center_x
        elif transcription_type == "SLIDE_UP":
            if type == "in":
                start_y_offset = self.video_height  # 완전히 화면 아래로
                end_y_offset = video_center_y - image_center_y
            elif type == "out":
                start_y_offset = video_center_y - image_center_y
                end_y_offset = -pil_img.height  # 완전히 화면 위로
            paste_y = start_y_offset + (end_y_offset - start_y_offset) * progress_eased
            paste_x = video_center_x - image_center_x
        elif transcription_type == "SLIDE_LEFT":
            if type == "in":
                start_x_offset = self.video_width  # 완전히 화면 오른쪽으로
                end_x_offset = video_center_x - image_center_x
            elif type == "out":
                start_x_offset = video_center_x - image_center_x
                end_x_offset = -pil_img.width  # 완전히 화면 왼쪽으로
            paste_x = start_x_offset + (end_x_offset - start_x_offset) * progress_eased
            paste_y = video_center_y - image_center_y
        elif transcription_type == "SLIDE_RIGHT":
            if type == "in":
                start_x_offset = -pil_img.width  # 완전히 화면 왼쪽으로
                end_x_offset = video_center_x - image_center_x
            elif type == "out":
                start_x_offset = video_center_x - image_center_x
                end_x_offset = self.video_width  # 완전히 화면 오른쪽으로
            paste_x = start_x_offset + (end_x_offset - start_x_offset) * progress_eased
            paste_y = video_center_y - image_center_y

        final_canvas.paste(pil_img, (int(paste_x), int(paste_y)))
        return final_canvas

    def save_video(self, video: CompositeVideoClip):
        output_path = os.path.join(self.temp_dir, f"shorts_video_{uuid.uuid4()}.mp4")
        video.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            threads=4,
            fps=24,
            audio_fps=24000,
            logger=None,  # MoviePy 로그 비활성화
            ffmpeg_params=["-loglevel", "quiet"],  # FFmpeg 로그 비활성화
        )
        return output_path
