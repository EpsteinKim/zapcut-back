from enum import Enum
from pydantic import BaseModel
from typing import List, TypeVar, Generic, ClassVar, Literal
from fastapi import Query

from app.core.config import BGM_PATH


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


# Enum 대신 문자열 상수로 정의 (Google AI 스키마 호환성을 위해)
class AnimationEffect(BaseModel):
    NONE: ClassVar[str] = "NONE"
    SEQUENTIAL: ClassVar[str] = "SEQUENTIAL"
    LARGE_TEXT: ClassVar[str] = "LARGE_TEXT"
    SMOOTH_POP: ClassVar[str] = "SMOOTH_POP"


class SoundEffect(BaseModel):
    LEVEL_UP: ClassVar[str] = "LEVEL_UP"


# 타입 정의를 위한 Literal 타입
TTSVoiceModel = Literal[
    "Achernar", "Callirrhoe", "Enceladus", "Fenrir", "Kore", "Lapetus", "Leda", "Sadaltager", "Zephyr"
]

# BGM 타입 정의
BGMTypeModel = Literal[
    "SUNGLASS_MAN",
    "CHEERING_APPLAUSE",
    "STRANGE_CURIOSITY",
    "RABBIT",
    "YOU_FIRST_DO",
    "SURFING_DANCE",
    "CUSTOM",
    "NONE",
]


# 상수 접근을 위한 클래스 (옵션)
class VoiceModelConstants:
    Achernar: ClassVar[str] = "Achernar"
    Callirrhoe: ClassVar[str] = "Callirrhoe"
    Enceladus: ClassVar[str] = "Enceladus"
    Fenrir: ClassVar[str] = "Fenrir"
    Kore: ClassVar[str] = "Kore"
    Lapetus: ClassVar[str] = "Lapetus"
    Leda: ClassVar[str] = "Leda"
    Sadaltager: ClassVar[str] = "Sadaltager"
    Zephyr: ClassVar[str] = "Zephyr"


class BGMType:
    SUNGLASS_MAN: ClassVar[str] = "SUNGLASS_MAN"
    CHEERING_APPLAUSE: ClassVar[str] = "CHEERING_APPLAUSE"
    STRANGE_CURIOSITY: ClassVar[str] = "STRANGE_CURIOSITY"
    RABBIT: ClassVar[str] = "RABBIT"
    YOU_FIRST_DO: ClassVar[str] = "YOU_FIRST_DO"
    SURFING_DANGER: ClassVar[str] = "SURFING_DANGER"
    CUSTOM: ClassVar[str] = "CUSTOM"
    NONE: ClassVar[str] = "NONE"

    # BGM 파일 경로 매핑
    _BGM_PATHS: ClassVar[dict[str, str]] = {
        "SUNGLASS_MAN": BGM_PATH + "/sunglass_man.mp3",
        "CHEERING_APPLAUSE": BGM_PATH + "/cheering_applause.mp3",
        "STRANGE_CURIOSITY": BGM_PATH + "/strange_curiosity.mp3",
        "RABBIT": BGM_PATH + "/rabbit.mp3",
        "YOU_FIRST_DO": BGM_PATH + "/you_first_do.mp3",
        "SURFING_DANCE": BGM_PATH + "/surfing_dance.mp3",  # 실제 파일명에 맞춤
        "CUSTOM": "",  # 커스텀은 별도 URL 사용
        "NONE": "",  # 배경음악 없음
    }

    @classmethod
    def get_file_path(cls, bgm_type: str) -> str | None:
        """BGM 타입에 해당하는 파일 경로를 반환합니다."""
        return cls._BGM_PATHS.get(bgm_type)

    @classmethod
    def get_all_bgm_info(cls) -> dict[str, str]:
        """모든 BGM 정보를 반환합니다."""
        return cls._BGM_PATHS.copy()

    @classmethod
    def is_valid_bgm_type(cls, bgm_type: str) -> bool:
        """유효한 BGM 타입인지 확인합니다."""
        return bgm_type in cls._BGM_PATHS


class CaptionInfo(BaseModel):
    text: str
    start_time: float
    end_time: float
    sound_effect: str | None = None  # SoundEffect의 값들 중 하나
    animation_effect: str | None = None  # AnimationEffect의 값들 중 하나
    color: str | None = None


class Scene(BaseModel):
    text: str | None = None  # 처음에 전체 싱크에서만 씀
    duration: float | None = None
    captions: List[CaptionInfo] | None = None
    description: str
    video_url: str | None = None
    image_url: str | None = None
    voice_url: str | None = None


class SceneAlter(BaseModel):
    text: str
    description: str


class ShortsScriptRequest(BaseModel):
    page_html: str | None = None
    user_prompt: str | None = None
    duration: int


class ShortsImageRequest(BaseModel):
    prompt: str


class ShortsVoiceRequest(BaseModel):
    text: str
    duration: float
    voice_model: TTSVoiceModel = VoiceModelConstants.Kore
    voice_temperature: float = 0.3


class ShortsMakeSyncedSceneRequest(BaseModel):
    scenes: list[Scene]
    audio_url: str


class ShortsVideoRequest(BaseModel):
    scenes: List[Scene]
    bgm_id: BGMTypeModel | None = None
    custom_bgm_url: str | None = None
    music_volume: float = 0.4
