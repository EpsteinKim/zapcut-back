from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache

# 프로젝트 루트 디렉토리 설정
ROOT_DIR = Path.cwd() / "app"
ENV_FILE = str(ROOT_DIR / ".env")

FONT_PATH = str(Path(ROOT_DIR) / "assets" / "fonts")
SOUND_PATH = str(Path(ROOT_DIR) / "assets" / "sounds")


class Settings(BaseSettings):
    app_name: str = "YouTube Shorts Generator"
    openai_api_key: str
    typecast_api_key: str
    google_ai_api_key: str

    class Config:
        env_file = str(ENV_FILE)


@lru_cache()
def get_settings():
    return Settings()
