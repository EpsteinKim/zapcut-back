import os
from moviepy import TextClip
from app.core.config import ROOT_DIR
from typing import Tuple, List
from pathlib import Path


class TextProcessor:
    def __init__(self, video_width: int, video_height: int):
        self.video_width = video_width
        self.video_height = video_height
        self.font_path = str(Path(ROOT_DIR) / "fonts" / "NanumGothic.ttf")

    def create_text_clip(self, caption: str, duration: float, start_time: float) -> TextClip:
        text_clip = TextClip(
            text=caption,
            font=self.font_path,
            font_size=60,
            color="white",
            stroke_color="black",
            stroke_width=10,
            method="caption",
            size=(int(self.video_width * 0.9), None),
            margin=(0, 0, 0, 10),
        ).with_duration(duration)

        return text_clip.with_position(("center", int(self.video_height * 0.5))).with_start(start_time)

    def calculate_caption_durations(self, captions: List[str], total_duration: float) -> List[float]:
        if not captions:
            return []

        # 각 캡션의 길이에 비례하여 지속 시간 할당
        total_chars = sum(len(caption) for caption in captions)
        durations = []

        for caption in captions:
            if total_chars == 0:
                duration = total_duration / len(captions)
            else:
                duration = (len(caption) / total_chars) * total_duration
            durations.append(duration)

        return durations
