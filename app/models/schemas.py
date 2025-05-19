from pydantic import BaseModel
from typing import List

class ChatRequest(BaseModel):
    prompt: str

class ChatResponse(BaseModel):
    response: str

class ShortsRequest(BaseModel):
    topic: str
    style: str = "informative"
    duration: str = "60s"

class ShortsResponse(BaseModel):
    title: str
    description: str
    hashtags: List[str]
    script: str 