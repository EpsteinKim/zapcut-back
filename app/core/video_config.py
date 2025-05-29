from pathlib import Path


class VideoConfig:
    # 비디오 크기 설정
    VIDEO_WIDTH = 1080
    VIDEO_HEIGHT = 1920

    # 배경 설정
    BACKGROUND_COLOR = (0, 0, 0)

    # 폰트 설정
    FONT_NAME = "NanumGothic.ttf"
    FONT_SIZE = 70

    # 캡션 설정
    CAPTION_WIDTH_RATIO = 0.9
    CAPTION_POSITION_RATIO = 0.7

    # 비디오 출력 설정
    OUTPUT_FPS = 30
    OUTPUT_PRESET = "ultrafast"
    OUTPUT_THREADS = 4

    # 기본 경로 설정
    BASE_PATH = Path.cwd()
    FONT_PATH = str(BASE_PATH / "fonts" / FONT_NAME)

    # 캡션 스타일 설정
    CAPTION_STYLE = {
        "color": "white",
        "stroke_color": "black",
        "stroke_width": 2,
        "method": "caption",
        "margin": (0, 0, 0, 10),
    }
