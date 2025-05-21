from pydantic_settings import BaseSettings
from functools import lru_cache
from .constants import ROOT_DIR, ENV_FILE

class Settings(BaseSettings):
    app_name: str = "YouTube Shorts Generator"
    openai_api_key: str
    
    class Config:
        env_file = str(ENV_FILE)

@lru_cache()
def get_settings():
    return Settings() 