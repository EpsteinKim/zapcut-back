from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path

# 프로젝트 루트 디렉토리 경로 설정
ROOT_DIR = Path.cwd()

class Settings(BaseSettings):
    app_name: str = "YouTube Shorts Generator"
    openai_api_key: str
    
    class Config:
        env_file = str(ROOT_DIR / ".env")

@lru_cache()
def get_settings():
    return Settings() 