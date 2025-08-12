from moviepy import TextClip
from typing import List, Union
from app.models.schemas import CaptionInfo, AnimationEffect, FontFamily
import os
from app.utils.os_processor import get_temp_dir


class TextProcessor:
    def __init__(self, video_width: int, video_height: int):
        self.video_width = video_width
        self.video_height = video_height
        self.base_text_config = {
            "font": FontFamily.get_file_path("JUA"),
            "font_size": 100,
            "color": "white",
            "stroke_color": "black",
            "stroke_width": 10,
            "method": "caption",
            "size": (int(self.video_width), int(self.video_height)),
        }

        self.temp_dir = get_temp_dir("text_processor")

    def create_text_clips(
        self,
        caption: CaptionInfo,
        current_time: float = 0,
    ) -> Union[TextClip, List[TextClip]]:

        animation_effect = caption.animation_effect or AnimationEffect.NONE

        animation_renderer = {
            AnimationEffect.SEQUENTIAL: self.sequential_text_clips,
            AnimationEffect.LARGE_TEXT: self.large_text_clip,
            AnimationEffect.SMOOTH_POP: self.smooth_pop_text_clip,
            AnimationEffect.NONE: (
                lambda caption, current_time: [
                    TextClip(**self.get_text_config_copy_with_style_effects(caption))
                    .with_start(current_time + caption.start_time)
                    .with_duration(caption.end_time - caption.start_time)
                ]
            ),
        }

        # 스타일 효과를 애니메이션 생성 시점에 적용하도록 수정
        base_text_clips = animation_renderer[animation_effect](caption, current_time)

        if animation_effect == AnimationEffect.NONE:
            base_text_clips = self.process_text_clip(base_text_clips, caption)

        return base_text_clips

    def get_text_config_copy_with_style_effects(self, caption: CaptionInfo) -> dict:
        config = self.base_text_config.copy()
        config["text"] = caption.text
        config["color"] = caption.color
        config["font"] = FontFamily.get_file_path(caption.font_family or "JUA")

        return config

    # config로 설정이 불가한 경우의 설정을 처리
    def process_text_clip(self, text_clip: TextClip, caption: CaptionInfo) -> TextClip:
        if caption.position == "TOP":
            # 상단에 80% 높이로 고정
            return text_clip.with_position(lambda t: ("center", t - 530))
        elif caption.position == "BOTTOM":
            # 하단에 80% 높이로 고정
            return text_clip.with_position(lambda t: ("center", t + 530))
        else:
            return text_clip.with_position(("center", "center"))

    def sequential_text_clips(self, caption: CaptionInfo, current_time: float) -> List[TextClip]:
        text_clips = []
        frame_interval = 2 / 24.0
        final_display_time = 0.2

        text = caption.text
        start_time = current_time + caption.start_time
        total_duration = caption.end_time - caption.start_time

        if total_duration <= final_display_time:
            config = self.get_text_config_copy_with_style_effects(caption)
            text_clip = TextClip(**config)
            text_clip = (
                text_clip.with_start(start_time).with_duration(total_duration).with_position(("center", "center"))
            )
            text_clip = self.process_text_clip(text_clip, caption)
            return [text_clip]

        available_time_for_animation = total_duration - final_display_time
        max_frames = int(available_time_for_animation / frame_interval)

        if max_frames <= 0:
            config = self.get_text_config_copy_with_style_effects(caption)
            text_clip = TextClip(**config)
            text_clip = text_clip.with_start(start_time).with_duration(total_duration)
            text_clip = self.process_text_clip(text_clip, caption)
            return [text_clip]

        copied_caption = caption.model_copy()
        for i in range(max_frames):
            progress = (i + 1) / max_frames
            chars_to_show = int(len(text) * progress)

            if chars_to_show > 0:
                group_text = text[:chars_to_show]
                group_start_time = start_time + (i * frame_interval)

                copied_caption.text = group_text
                config = self.get_text_config_copy_with_style_effects(copied_caption)
                text_clip = TextClip(**config)
                text_clip = text_clip.with_start(group_start_time).with_end(group_start_time + frame_interval)
                text_clip = self.process_text_clip(text_clip, caption)
                text_clips.append(text_clip)

        if text.strip():
            final_start_time = start_time + (max_frames * frame_interval)
            final_duration = final_display_time

            config = self.get_text_config_copy_with_style_effects(caption)
            final_clip = TextClip(**config)
            final_clip = final_clip.with_start(final_start_time).with_duration(final_duration)
            final_clip = self.process_text_clip(final_clip, caption)
            text_clips.append(final_clip)

        return text_clips

    def large_text_clip(self, caption: CaptionInfo, current_time: float) -> List[TextClip]:
        start_time = current_time + caption.start_time
        total_duration = caption.end_time - caption.start_time
        text_clips = []

        per_sec = 0.02
        until = 0.2
        start_scale = 0.8
        end_scale = 1.4
        keyframes = [
            (i * per_sec, start_scale + (end_scale - start_scale) * i / (int(until / per_sec) - 1))
            for i in range(int(until / per_sec))
        ]

        for i, (time_offset, scale) in enumerate(keyframes):
            if i < len(keyframes) - 1:
                next_time = keyframes[i + 1][0]
                duration = next_time - time_offset
            else:
                duration = total_duration - time_offset

            if duration > 0 and total_duration > time_offset:
                config = self.get_text_config_copy_with_style_effects(caption)
                config["font_size"] = int(config["font_size"] * scale)
                config["stroke_width"] = max(1, int(config["stroke_width"] * scale))
                text_clip = TextClip(**config)

                clip_start = start_time + time_offset
                actual_duration = min(duration, total_duration - time_offset)

                text_clip = text_clip.with_start(clip_start).with_duration(actual_duration)
                text_clip = self.process_text_clip(text_clip, caption)
                text_clips.append(text_clip)

        return text_clips

    def smooth_pop_text_clip(self, caption: CaptionInfo, current_time: float) -> List[TextClip]:
        start_time = current_time + caption.start_time
        total_duration = caption.end_time - caption.start_time
        text_clips = []

        # 0.2초 동안의 부드러운 애니메이션 키프레임
        keyframes = [
            (0.00, 0.8),  # 시작: 0.8배
            (0.02, 0.85),  # 0.02초: 0.85배
            (0.04, 0.9),  # 0.04초: 0.9배
            (0.06, 0.95),  # 0.06초: 0.95배
            (0.08, 1.0),  # 0.08초: 1.0배
            (0.10, 1.05),  # 0.10초: 1.05배
            (0.12, 1.1),  # 0.12초: 1.1배 (최대)
            (0.16, 1.05),  # 0.16초: 1.0배
            (0.20, 1.0),  # 0.20초: 1.0배 (최종)
        ]
        animation_duration = keyframes[-1][0]

        # 애니메이션 키프레임 생성 (0.2초 동안만)
        for i, (time_offset, scale) in enumerate(keyframes):
            if i < len(keyframes) - 1:
                next_time = keyframes[i + 1][0]
                duration = next_time - time_offset
            else:
                duration = 0.04  # 마지막 키프레임 지속시간

            if duration > 0 and total_duration > time_offset:
                config = self.get_text_config_copy_with_style_effects(caption)
                config["font_size"] = int(config["font_size"] * scale)
                config["stroke_width"] = max(1, int(config["stroke_width"] * scale))

                text_clip = TextClip(**config)

                clip_start = start_time + time_offset
                actual_duration = min(duration, total_duration - time_offset)

                text_clip = text_clip.with_start(clip_start).with_duration(actual_duration)
                text_clip = self.process_text_clip(text_clip, caption)

                text_clips.append(text_clip)

        # 0.2초 이후 나머지 시간은 기본 TextClip만 표시
        remaining_duration = total_duration - animation_duration
        if remaining_duration > 0:
            static_start = start_time + animation_duration
            config = self.get_text_config_copy_with_style_effects(caption)
            static_clip = TextClip(**config)
            static_clip = static_clip.with_start(static_start).with_duration(remaining_duration)
            static_clip = self.process_text_clip(static_clip, caption)
            text_clips.append(static_clip)

        # 전체 자막 시간이 0.2초보다 짧은 경우
        if total_duration <= animation_duration and not text_clips:
            config = self.get_text_config_copy_with_style_effects(caption)
            fallback_clip = TextClip(**config)
            fallback_clip = fallback_clip.with_start(start_time).with_duration(total_duration)
            fallback_clip = self.process_text_clip(fallback_clip, caption)
            text_clips.append(fallback_clip)

        return text_clips
