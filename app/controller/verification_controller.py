from fastapi import APIRouter, Depends, Request, Header
from app.models.schemas import (
    EmailRequest,
    EmailCodeVerifyRequest,
    ApiResponse,
    PhoneCodeVerifyRequest,
    PhoneRequest,
    UUIDRequest,
)
from app.core.dependencies import get_services
from app.core.dependencies import Services
from app.exceptions.http_exceptions import ServerException
from app.utils import redis_helper
from app.utils.common_util import get_device_id
from app.utils.rate_limit_util import check_rate_limit
from app.exceptions.http_exceptions import NotFoundException

router = APIRouter(prefix="/verify", tags=["verify"])


@router.post("/email/code")
async def send_email_code(request: EmailRequest, service: Services = Depends(get_services)):
    await service.email.send_email_code(request.email)
    return ApiResponse.ok()


@router.post("/email")
async def verify_email_code(
    email_verify_request: EmailCodeVerifyRequest,
    user_agent: str = Header(...),
    service: Services = Depends(get_services),
):
    is_verified = service.email.verify_email_code(email_verify_request.email, email_verify_request.code)

    if is_verified:
        # 인증 완료 시 Redis에 정보 저장
        device_id = get_device_id(user_agent)
        redis_helper.email_verify.set_verification_complete(email_verify_request.email, device_id, user_agent)
        return ApiResponse.ok("인증이 완료되었습니다.")
    else:
        raise ServerException("인증코드가 일치하지 않습니다.")


@router.post("/email/exist")
def check_email_exist(request: EmailRequest, service: Services = Depends(get_services)):
    is_exist = service.user.check_email_exist(request.email)

    if is_exist:
        return ApiResponse.error(message="이미 존재하는 이메일입니다.")
    else:
        return ApiResponse.ok(message="사용 가능한 이메일입니다.")


@router.post("/phone/exist")
def check_phone_exist(request: PhoneRequest, service: Services = Depends(get_services)):
    is_exist = service.user.check_phone_exist(request.phone)

    if is_exist:
        return ApiResponse.error(message="이미 존재하는 전화번호입니다.")
    else:
        return ApiResponse.ok(message="사용 가능한 전화번호입니다.")


@router.post("/phone/code")
async def send_phone_code(request: PhoneRequest, service: Services = Depends(get_services)):
    await service.sms.send_verify_code(request.phone)
    return ApiResponse.ok()


@router.post("/phone")
async def verify_phone_code(
    request: PhoneCodeVerifyRequest,
    user_agent: str = Header(...),
    service: Services = Depends(get_services),
):
    is_verified = await service.sms.verify_phone_code(request.phone, request.code)

    if is_verified:
        # 인증 완료 시 Redis에 정보 저장
        device_id = get_device_id(user_agent)
        redis_helper.phone_verify.set_verification_complete(request.phone, device_id, user_agent)
        return ApiResponse.ok("인증이 완료되었습니다.")
    else:
        raise ServerException("인증코드가 일치하지 않습니다.")


@router.post("/reset-password/send-uuid")
async def send_reset_password_uuid(
    request: Request, ApiRequest: EmailRequest, service: Services = Depends(get_services)
):
    # IP별 rate limiting 적용 (초당 1회 제한)
    check_rate_limit(request, max_requests=1, window_seconds=1, prefix="find_user_password")

    # 이메일로 사용자 찾기
    user = service.user.find_user_by_email(service.session, ApiRequest.email)
    if not user:
        raise NotFoundException("해당 이메일로 등록된 사용자를 찾을 수 없습니다.")
    await service.email.send_find_account_uuid(ApiRequest.email, user.user_id)

    return ApiResponse.ok("이메일 인증 메일이 전송되었습니다.")


@router.post("/reset-password/check-uuid")
async def verify_find_account_uuid(request: UUIDRequest, service: Services = Depends(get_services)):
    is_verified = await service.email.verify_find_account_uuid(request.email, request.uuid)

    if is_verified:
        return ApiResponse.ok("인증이 완료되었습니다.")
    else:
        raise ServerException("인증코드가 일치하지 않습니다.")
