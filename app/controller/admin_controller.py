from fastapi import APIRouter, Depends, Header, Request, Response
from app.core.dependencies import get_current_user_info, Services, get_services
from app.entity.user import User
from app.models.schemas import ApiResponse, ImpersonateTicketRequest
from app.core.config import get_settings
from app.utils.common_util import get_device_id, is_admin
from app.utils import auth_helper
from app.utils import redis_helper, cookie_helper
from app.exceptions.http_exceptions import ForbiddenException, NotFoundException

router = APIRouter(prefix="/admin")

settings = get_settings()


@router.post("/impersonate")
async def issue_impersonation(
    request: Request,
    response: Response,
    body: ImpersonateTicketRequest,
    user_agent: str = Header(...),
    current_user_info=Depends(get_current_user_info),
    services: Services = Depends(get_services),
):
    forbidden_exception = ForbiddenException("관리자만 접근할 수 있습니다.")
    device_id = get_device_id(user_agent)

    admin_user_id = (
        current_user_info.payload.impersonate_admin_user_id
        if is_admin(current_user_info.payload.impersonate_admin_user_id)
        else current_user_info.user.user_id
    )

    if not is_admin(admin_user_id) or not request.cookies.get("is_admin_zcut"):
        raise forbidden_exception

    # 3. 대상 사용자 존재 확인
    user = services.user.find_user_by_user_id(services.session, body.target_user_id)
    if not user:
        raise NotFoundException("해당 사용자를 찾을 수 없습니다.")

    # 임퍼소네이션 대상자가 만약 관리자라면 임퍼소네이션 토큰 철회
    if current_user_info.payload.impersonate_admin_user_id == user.user_id and is_admin(admin_user_id):
        auth_helper.delete_impersonation_token(current_user_info.user.user_id, device_id)
        cookie_helper.delete_impersonate_token_cookie(response, device_id)
        if request.cookies.get("is_admin_zcut"):
            return ApiResponse.ok("임퍼소네이션 종료 확인, 토큰 철회 완료")
    # 4. 임퍼소네이션 토큰 생성
    token = auth_helper.create_impersonation_token(admin_user_id, user.user_id, device_id)

    cookie_helper.set_impersonate_token_cookie(response, token, device_id)

    return ApiResponse.ok("임퍼소네이션 토큰 발급 완료")
