from fastapi import HTTPException
import logging

# 로거 설정
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

# 콘솔 핸들러 설정
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)
formatter = logging.Formatter("\033[91m[%(levelname)s]\033[0m %(message)s")
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

type ErrorData = dict | str | None


class BaseHTTPException(HTTPException):
    def __init__(self, status_code: int, message: str, data: ErrorData = None):
        super().__init__(status_code=status_code, detail=message)
        self.message = message  # 메시지를 별도 속성으로 저장

        # 401 인증 오류는 로그 출력하지 않음 (정상적인 토큰 갱신 플로우)
        if status_code != 401:
            logger.error(f"HTTP {status_code}: {message}")

        if data is not None:
            self.data = data

    def __str__(self):
        return self.message


class BadRequestException(BaseHTTPException):
    """
    클라이언트의 요청이 잘못된 형식이거나 유효하지 않은 데이터를 포함할 때 사용
    예: 필수 필드 누락, 잘못된 데이터 형식, 유효성 검사 실패
    """

    def __init__(self, message: str = "잘못된 요청입니다", data: ErrorData = None):
        super().__init__(status_code=400, message=message, data=data)


class UnauthorizedException(BaseHTTPException):
    """
    인증이 필요한 리소스에 접근할 때 인증 정보가 없거나 유효하지 않을 때 사용
    예: 로그인하지 않은 사용자의 접근, 만료된 토큰
    """

    def __init__(self, message: str = "인증이 필요합니다", data: ErrorData = None):
        super().__init__(status_code=401, message=message, data=data)


class ForbiddenException(BaseHTTPException):
    """
    인증은 되었지만 해당 리소스에 대한 접근 권한이 없을 때 사용
    예: 일반 사용자가 관리자 전용 기능에 접근 시도
    """

    def __init__(self, message: str = "접근이 거부되었습니다", data: ErrorData = None):
        super().__init__(status_code=403, message=message, data=data)


class NotFoundException(BaseHTTPException):
    """
    요청한 리소스가 존재하지 않을 때 사용
    예: 존재하지 않는 사용자 ID로 조회, 삭제된 게시물 접근
    """

    def __init__(self, message: str = "요청한 리소스를 찾을 수 없습니다", data: ErrorData = None):
        super().__init__(status_code=404, message=message, data=data)


class MethodNotAllowedException(BaseHTTPException):
    """
    해당 엔드포인트에서 지원하지 않는 HTTP 메소드로 요청할 때 사용
    예: GET만 지원하는 엔드포인트에 POST 요청
    """

    def __init__(self, message: str = "허용되지 않은 메소드입니다", data: ErrorData = None):
        super().__init__(status_code=405, message=message, data=data)


class ConflictException(BaseHTTPException):
    """
    요청이 현재 서버의 상태와 충돌할 때 사용
    예: 이미 존재하는 사용자명으로 회원가입, 동시 편집 충돌
    """

    def __init__(self, message: str = "요청이 현재 서버의 상태와 충돌합니다", data: ErrorData = None):
        super().__init__(status_code=409, message=message, data=data)


class UnprocessableEntityException(BaseHTTPException):
    """
    요청은 올바른 형식이지만 의미적으로 처리할 수 없을 때 사용
    예: 유효성 검사 실패, 비즈니스 로직 위반
    """

    def __init__(self, message: str = "처리할 수 없는 입력입니다", data: ErrorData = None):
        super().__init__(status_code=422, message=message, data=data)


class TooManyRequestsException(BaseHTTPException):
    """
    클라이언트가 너무 많은 요청을 보냈을 때 사용
    예: API 요청 제한 초과, DDoS 방지
    """

    def __init__(self, message: str = "너무 많은 요청이 발생했습니다", data: ErrorData = None):
        super().__init__(status_code=429, message=message, data=data)


class ServerException(BaseHTTPException):
    """
    서버 내부에서 예상치 못한 오류가 발생했을 때 사용
    예: 데이터베이스 연결 실패, 외부 서비스 오류
    """

    def __init__(self, message: str = "서버 내부 오류가 발생했습니다", data: ErrorData = None):
        super().__init__(status_code=500, message=message, data=data)


class ServiceUnavailableException(BaseHTTPException):
    """
    서버가 일시적으로 요청을 처리할 수 없을 때 사용
    예: 서버 유지보수, 과부하 상태
    """

    def __init__(self, message: str = "서비스를 일시적으로 사용할 수 없습니다", data: ErrorData = None):
        super().__init__(status_code=503, message=message, data=data)
