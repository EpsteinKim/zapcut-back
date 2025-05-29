from moviepy import TextClip
from pathlib import Path
import os
from app.core.config import ROOT_DIR


class TextProcessor:
    def __init__(self, width: int = 1080, height: int = 1920):
        self.width = width
        self.height = height
        self.font_path = str(Path(ROOT_DIR) / "fonts" / "NanumGothic.ttf")

    def _get_font_path(self) -> str:
        """폰트 경로 가져오기"""
        return self.font_path if os.path.exists(self.font_path) else "Arial"

    def create_text_clip(self, caption: str, duration: float, start_time: float) -> TextClip:
        """텍스트 클립 생성"""
        text_clip = TextClip(
            text=caption,
            font=self._get_font_path(),
            font_size=60,
            color="white",
            stroke_color="black",
            stroke_width=10,
            method="caption",
            size=(int(self.width * 0.9), None),
            margin=(0, 0, 0, 10),
        ).with_duration(duration)

        return text_clip.with_position(("center", int(self.height * 0.5))).with_start(start_time)
