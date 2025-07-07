from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache

# 프로젝트 루트 디렉토리 설정
ROOT_DIR = Path.cwd() / "app"

FONT_PATH = str(Path(ROOT_DIR) / "assets" / "fonts")
BGM_PATH = str(Path(ROOT_DIR) / "assets" / "sounds" / "bgm")
EFFECT_PATH = str(Path(ROOT_DIR) / "assets" / "sounds" / "effect")


class Settings(BaseSettings):
    openai_api_key: str
    typecast_api_key: str
    google_ai_api_key: str

    proxy: str
    unlock_proxy: str
    bright_data_api_key: str

    class Config:
        env_file = str(ROOT_DIR / ".env")


@lru_cache()
def get_settings():
    return Settings()
