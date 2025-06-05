from pydantic import BaseModel
from typing import List, TypeVar, Generic, ClassVar
from fastapi import Query

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

T = TypeVar("T")


class Response(BaseModel, Generic[T]):
    message: str
    data: T | None = None

    # 기본 메시지 상수
    _OK_MESSAGE: ClassVar[str] = "요청이 성공적으로 처리되었습니다."
    _ERROR_MESSAGE: ClassVar[str] = "처리 중 오류가 발생했습니다."

    @classmethod
    def ok(cls) -> "Response[T]":
        return cls(message=cls._OK_MESSAGE)

    @classmethod
    def error(cls, message: str | None = None) -> "Response[T]":
        return cls(message=message or cls._ERROR_MESSAGE)

    @classmethod
    def with_data(cls, data: T, message: str | None = None) -> "Response[T]":
        return cls(message=message or cls._OK_MESSAGE, data=data)


class CaptionInfo(BaseModel):
    text: str
    start_time: float
    end_time: float


class Scene(BaseModel):
    duration: float
    captions: List[CaptionInfo]
    description: str


class SceneWithData(Scene):
    video_url: str | None = None
    image_url: str | None = None


class ShortsScriptRequest(BaseModel):
    url: str
    duration: int

    @classmethod
    def from_query(
        cls, url: str = Query(..., description="스크랩할 URL"), duration: int = Query(..., description="영상 길이(초)")
    ) -> "ShortsScriptRequest":
        return cls(url=url, duration=duration)


class SceneRequest(BaseModel):
    captions: List[str]
    image_url: str | None = None
    video_url: str | None = None


class ShortsVideoRequest(BaseModel):
    scenes: List[SceneWithData]
    background_music_url: str | None = None  # 배경 음악 URL (선택적)
    music_volume: float | None = 0.5  # 배경 음악 볼륨 (0.0 ~ 1.0, 기본값 0.5)


class ShortsSceneRequest(BaseModel):
    video_url: str | None = None
    image_url: str | None = None
    captions: List[CaptionInfo]


class CombineShortsSceneRequest(BaseModel):
    scene_urls: List[str]  # video_urls (이미 만들어진 url들)
    background_music_url: str | None = None
