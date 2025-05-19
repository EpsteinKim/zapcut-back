from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    app_name: str = "YouTube Shorts Generator"
    openai_api_key: str = "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"
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings() 