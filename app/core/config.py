from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache
import os

# 프로젝트 루트 디렉토리 설정
ROOT_DIR = Path.cwd()

FONT_PATH = str(ROOT_DIR / "app" / "assets" / "fonts")
BGM_PATH = str(ROOT_DIR / "app" / "assets" / "sounds" / "bgm")
EFFECT_PATH = str(ROOT_DIR / "app" / "assets" / "sounds" / "effect")

# 공통 temp 디렉토리 설정


# Docker 환경과 로컬 환경을 구분
if os.getenv("ENV") == "production":
    TEMP_DIR = str(ROOT_DIR / "app" / "temp")
else:
    TEMP_DIR = str(ROOT_DIR / "temp")


class Settings(BaseSettings):
    env: str = "dev"  # 기본값을 development로 설정
    openai_api_key: str
    google_ai_api_key: str

    client_host: str = "http://localhost:3000" if os.getenv("ENV") != "production" else "https://zapcut.io"

    proxy: str
    unlock_proxy: str
    bright_data_api_key: str

    # database
    database_url: str

    # JWT
    secret_key: str
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # email
    brevo_key: str

    # Aligo SMS
    aligo_key: str

    # Redis
    redis_host: str = "localhost" if os.getenv("ENV") != "production" else "zapcut-redis"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0

    class Config:
        env_file = str(ROOT_DIR / ".env")


@lru_cache()
def get_settings():
    return Settings()
