from enum import Enum
from datetime import datetime
from pydantic import BaseModel
from typing import List, TypeVar, Generic, ClassVar, Literal
from fastapi import Query

from app.core.config import BGM_PATH, FONT_PATH
from app.entity.user import User

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    message: str
    data: T | None = None

    # 기본 메시지 상수
    _OK_MESSAGE: ClassVar[str] = "요청이 성공적으로 처리되었습니다."
    _ERROR_MESSAGE: ClassVar[str] = "처리 중 오류가 발생했습니다."

    @classmethod
    def ok(cls, message: str | None = None) -> "ApiResponse[T]":
        return cls(message=message or cls._OK_MESSAGE)

    @classmethod
    def error(cls, message: str | None = None) -> "ApiResponse[T]":
        return cls(message=message or cls._ERROR_MESSAGE)

    @classmethod
    def with_data(cls, data: T, message: str | None = None) -> "ApiResponse[T]":
        return cls(message=message or cls._OK_MESSAGE, data=data)


class CurrentUserInfoPayload(BaseModel):
    sub: str
    impersonate_admin_user_id: str | None = None

    class Config:
        extra = "allow"


class CurrentUserInfo(BaseModel):
    user: User
    payload: CurrentUserInfoPayload


# Enum 대신 문자열 상수로 정의 (Google AI 스키마 호환성을 위해)
class AnimationEffect(BaseModel):
    NONE: ClassVar[str] = "NONE"
    SEQUENTIAL: ClassVar[str] = "SEQUENTIAL"
    LARGE_TEXT: ClassVar[str] = "LARGE_TEXT"
    SMOOTH_POP: ClassVar[str] = "SMOOTH_POP"


TransitionTypeModel = Literal[
    "ROTATE", "BLACK_WHITE", "SCALE", "BLUR", "SLIDE_DOWN", "SLIDE_UP", "SLIDE_LEFT", "SLIDE_RIGHT"
]


class TransitionType:
    ROTATE: ClassVar[str] = "ROTATE"
    BLACK_WHITE: ClassVar[str] = "BLACK_WHITE"
    SCALE: ClassVar[str] = "SCALE"
    BLUR: ClassVar[str] = "BLUR"
    SLIDE_DOWN: ClassVar[str] = "SLIDE_DOWN"
    SLIDE_UP: ClassVar[str] = "SLIDE_UP"
    SLIDE_LEFT: ClassVar[str] = "SLIDE_LEFT"
    SLIDE_RIGHT: ClassVar[str] = "SLIDE_RIGHT"


class FontFamily(BaseModel):
    JUA: ClassVar[str] = "JUA"
    MARU_BURI: ClassVar[str] = "MARU_BURI"
    PAPERLOGY: ClassVar[str] = "PAPERLOGY"

    _FONT_PATHS: ClassVar[dict[str, str]] = {
        "JUA": FONT_PATH + "/Jua-Regular.ttf",
        "MARU_BURI": FONT_PATH + "/MaruBuri-Regular.otf",
        "PAPERLOGY": FONT_PATH + "/Paperlogy-4Regular.ttf",
    }

    @classmethod
    def get_file_path(cls, font_type: str) -> str | None:
        """폰트 타입에 해당하는 파일 이름을 반환합니다."""
        return cls._FONT_PATHS.get(font_type)


class SoundEffect(BaseModel):
    LEVEL_UP: ClassVar[str] = "LEVEL_UP"


# 타입 정의를 위한 Literal 타입
TTSVoiceModel = Literal[
    "Achernar", "Callirrhoe", "Enceladus", "Fenrir", "Kore", "Iapetus", "Leda", "Sadaltager", "Zephyr"
]


# 상수 접근을 위한 클래스 (옵션)
class VoiceModelConstants:
    Achernar: ClassVar[str] = "Achernar"
    Callirrhoe: ClassVar[str] = "Callirrhoe"
    Enceladus: ClassVar[str] = "Enceladus"
    Fenrir: ClassVar[str] = "Fenrir"
    Kore: ClassVar[str] = "Kore"
    Iapetus: ClassVar[str] = "Iapetus"
    Leda: ClassVar[str] = "Leda"
    Sadaltager: ClassVar[str] = "Sadaltager"
    Zephyr: ClassVar[str] = "Zephyr"


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
    position: Literal["TOP", "BOTTOM", "CENTER"] = "CENTER"
    font_family: Literal["JUA", "MARU_BURI", "PAPERLOGY"] = "JUA"
    sound_effect: str | None = None  # SoundEffect의 값들 중 하나
    animation_effect: str | None = None  # AnimationEffect의 값들 중 하나
    color: str | None = None


class Scene(BaseModel):
    duration: float | None = None
    captions: List[CaptionInfo] | None = None
    transition_in_effects: List[TransitionTypeModel] | None = []
    transition_out_effects: List[TransitionTypeModel] | None = []
    description: str | None = None
    video_url: str | None = None
    image_url: str | None = None
    voice_url: str | None = None


class DB_ShortsScript(BaseModel):
    scenes: list[Scene]
    bgm_id: BGMTypeModel
    custom_bgm_url: str | None = None
    bgm_volume: int
    voice_model: TTSVoiceModel
    voice_temperature: float
    complete_video_url: str | None = None


class ShortsScript(DB_ShortsScript):
    id: int | None = None
    title: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ShortsScriptUpsertRequest(BaseModel):
    id: int | None = 0
    title: str | None = None
    shorts_json: DB_ShortsScript


class ShortsScriptSaveRequest(BaseModel):
    script: DB_ShortsScript


class ShortsScriptUpdateRequest(BaseModel):
    script_id: str
    script: DB_ShortsScript


class ShortsScriptDeleteRequest(BaseModel):
    script_id: str


class SceneAlter(BaseModel):
    text: str
    description: str


class ShortsScriptGenerateRequest(BaseModel):
    page_html: str | None = None
    user_prompt: str | None = None


class ShortsImageRequest(BaseModel):
    prompt: str


class ShortsVoiceRequest(BaseModel):
    text: str
    duration: float | None = None
    voice_model: TTSVoiceModel = VoiceModelConstants.Kore
    voice_temperature: float = 0.3


class ShortsVoiceSubClipRequest(BaseModel):
    voice_url: str
    text_scenes: list[str]


class ShortsMakeSyncedSceneRequest(BaseModel):
    scenes: list[Scene]
    audio_url: str


class ShortsTranscriptionRequest(BaseModel):
    audio_url: str
    text_scenes: list[str]
    regenerate: bool = False


# ShortsScript에 해당하는 부분
class ShortsVideoRequest(BaseModel):
    scenes: List[Scene]
    bgm_id: BGMTypeModel | None = None
    custom_bgm_url: str | None = None
    music_volume: float = 0.4


class LoginRequest(BaseModel):
    user_id: str
    password: str


class UserInfoResponse(BaseModel):
    user_id: str
    email: str
    name: str


class UserSignupRequest(BaseModel):
    user_id: str
    email: str
    phone: str
    name: str
    password: str


class EmailRequest(BaseModel):
    email: str


class EmailCodeVerifyRequest(BaseModel):
    email: str
    code: str


class UUIDRequest(BaseModel):
    email: str
    uuid: str


class PhoneRequest(BaseModel):
    phone: str


class PhoneCodeVerifyRequest(BaseModel):
    phone: str
    code: str


class ResetPasswordRequest(BaseModel):
    email: str
    new_password: str
    uuid: str


class GoogleAiSimpleCaptionInfo(BaseModel):
    text: str
    start_time: float
    end_time: float


class GoogleAiSimpleScene(BaseModel):
    captions: list[GoogleAiSimpleCaptionInfo]


class ImpersonateTicketRequest(BaseModel):
    target_user_id: str
