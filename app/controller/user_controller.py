from fastapi import APIRouter, Depends, Form, Header, Response, Cookie, Request
from app.entity.user import User, UserResponse
from app.models.schemas import ApiResponse, EmailRequest
from app.core.dependencies import get_current_user, get_services, Services
from app.utils.auth_helper import create_access_token, create_refresh_token
from app.exceptions.http_exceptions import UnauthorizedException, BadRequestException, NotFoundException
from app.core.config import get_settings
from app.utils import redis_helper, cookie_helper
from app.models.schemas import ResetPasswordRequest, UserSignupRequest
from app.utils.common_util import get_device_id
from app.utils.rate_limit_util import check_rate_limit
import jwt

router = APIRouter(
    prefix="/user",
)

settings = get_settings()


@router.get("/me", response_model=ApiResponse[UserResponse])
async def read_users_me(current_user: User = Depends(get_current_user)):
    return ApiResponse.with_data(data=UserResponse.model_validate(current_user), message="현재 사용자 정보 조회 성공!")


@router.post("/token")
async def login_for_access_token(
    response: Response,
    user_id: str = Form(...),
    password: str = Form(...),
    ts: str = Header(...),
    user_agent: str = Header(...),
    service: Services = Depends(get_services),
):
    user = service.user.authenticate_user(service.session, user_id, password, ts)
    device_id = service.user.get_device_id(user_agent)

    access_token = create_access_token(data={"sub": user.user_id, "device_id": device_id})
    refresh_token = create_refresh_token(data={"sub": user.user_id, "device_id": device_id})
    cookie_helper.set_access_token_cookie(response, access_token, device_id)
    cookie_helper.set_refresh_token_cookie(response, refresh_token, device_id)

    return ApiResponse.ok()


@router.delete("/logout")
async def logout(
    request: Request,
    response: Response,
    user_agent: str = Header(...),
    service: Services = Depends(get_services),
):
    device_id = service.user.get_device_id(user_agent)

    # 현재 디바이스의 토큰들을 블랙리스트에 추가
    access_token = request.cookies.get(f"access_token_zcut_{device_id}")
    refresh_token = request.cookies.get(f"refresh_token_zcut_{device_id}")

    if access_token:
        service.user.blacklist_token(access_token, 60 * 30)  # 30분간 블랙리스트
    if refresh_token:
        service.user.blacklist_token(refresh_token, 60 * 60 * 24 * 7)  # 7일간 블랙리스트
        decoded = jwt.decode(refresh_token, settings.secret_key, algorithms=["HS256"], options={"verify_exp": False})
        if decoded:
            user_id = decoded.get("sub")
            redis_helper.jwt.delete_refresh_token(user_id, device_id)

    service.user.clear_auth_cookies(response, device_id)
    return ApiResponse.ok()


@router.delete("/logout/all")
async def logout_all_devices(
    current_user: User = Depends(get_current_user),
    service: Services = Depends(get_services),
):
    """모든 디바이스에서 로그아웃"""
    service.user.logout_all_devices(current_user.user_id)
    return ApiResponse.ok()


@router.post("/signup", response_model=ApiResponse)
def signup(
    user_signup_request: UserSignupRequest,
    user_agent: str = Header(...),
    service: Services = Depends(get_services),
):
    # device_id 생성
    device_id = get_device_id(user_agent)

    # 이메일 인증 완료 여부 확인
    if not redis_helper.email_verify.is_verified(user_signup_request.email, device_id):
        raise BadRequestException("이메일 인증 정보가 만료되었거나 존재하지 않습니다.")

    # 전화번호 인증 완료 여부 확인
    if not redis_helper.phone_verify.is_verified(user_signup_request.phone, device_id):
        raise BadRequestException("전화번호 인증 정보가 만료되었거나 존재하지 않습니다.")

    # 회원가입 처리
    service.user.create_user(service.session, user_signup_request)

    # 인증 완료 정보 삭제
    redis_helper.email_verify.del_verification_complete(user_signup_request.email, device_id)
    redis_helper.phone_verify.del_verification_complete(user_signup_request.phone, device_id)

    return ApiResponse.ok(message="회원가입이 성공적으로 완료되었습니다.")


@router.post("/find/id")
async def find_user_id_by_email(
    request: Request,
    api_request: EmailRequest,
    service: Services = Depends(get_services),
):
    # IP별 rate limiting 적용 (초당 1회 제한)
    check_rate_limit(request, max_requests=1, window_seconds=1, prefix="find_user_id")

    # 이메일로 사용자 찾기
    user = service.user.find_user_by_email(service.session, api_request.email)

    if not user:
        raise NotFoundException("해당 이메일로 등록된 사용자를 찾을 수 없습니다.")

    return ApiResponse.with_data(data={"user_id": user.user_id}, message="사용자 ID 조회 성공!")


@router.post("/reset-password")
async def reset_password(api_request: ResetPasswordRequest, service: Services = Depends(get_services)):
    service.user.reset_user_password(service.session, api_request)

    return ApiResponse.ok(message="비밀번호 재설정이 성공적으로 완료되었습니다.")


@router.delete
async def leave_user(
    current_user: User = Depends(get_current_user),
    service: Services = Depends(get_services),
):
    service.user.leave_user(service.session, current_user.user_id)
    return ApiResponse.ok("탈퇴 처리가 성공적으로 완료되었습니다.")
