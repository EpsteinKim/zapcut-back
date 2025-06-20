import os
from moviepy import ImageClip, TextClip
from moviepy.video import fx as vfx
from PIL import Image, ImageFont, ImageDraw, ImageFilter
import numpy as np
from app.core.config import ROOT_DIR
from typing import Tuple, List
from pathlib import Path
import math


class TextProcessor:
    def __init__(self, video_width: int, video_height: int):
        self.video_width = video_width
        self.video_height = video_height
        self.font_path = str(Path(ROOT_DIR) / "fonts" / "Jua-Regular.ttf")

    def create_text_clip(self, caption: str, start_time: float, end_time: float) -> TextClip:
        font_size = 100
        stroke_width = 10
        text_height = font_size + stroke_width * 2 * math.pi
        text_clip = TextClip(
            text=caption,
            font=self.font_path,
            font_size=font_size,
            color="white",
            stroke_color="black",
            stroke_width=stroke_width,
            method="caption",
            size=(int(self.video_width * 0.9), int(text_height)),
        )
        text_clip = text_clip.with_start(start_time).with_end(end_time)
        text_clip = text_clip.with_position(("center", "center"))
        return text_clip
