from pydantic import BaseModel
from typing import List, TypeVar, Optional, Union, Generic

# 제네릭 사용 예시:
# from typing import TypeVar, Generic
# T = TypeVar('T')
# class GenericResponse(BaseModel, Generic[T]):
#     response: T
# 
# 사용 예시:
# response_str = GenericResponse[str](response="안녕하세요")
# response_int = GenericResponse[int](response=42)
# response_list = GenericResponse[List[str]](response=["태그1", "태그2"])

# nullable 필드 지정 방법:
# 1. Optional 사용
# class Example1(BaseModel):
#     name: Optional[str] = None
#
# 2. Union 사용
# class Example2(BaseModel):
#     name: Union[str, None] = None
#
# 3. 직접 None 허용
# class Example3(BaseModel):
#     name: str | None = None  # Python 3.10 이상 

T = TypeVar('T')

class Response(BaseModel, Generic[T]):
    message: str
    data: T | None = None


class TestRequest(BaseModel):
    url: str

class ChatRequest(BaseModel):
    prompt: str

class ChatResponse(Response[str]): pass

class ShortsRequest(BaseModel):
    htmlContent : str
    style: str = "informative"
    duration: str = "60s"

class ShortsResponse(BaseModel):
    title: str
    description: str
    hashtags: List[str]
    script: str

