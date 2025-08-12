from fastapi import APIRouter, Depends, Header, Request, Response
from app.core.dependencies import get_current_user, Services, get_services
from app.entity.user import User
from app.models.schemas import ApiResponse, ImpersonationIssueRequest, ImpersonationIssueResponse
from app.core.config import get_settings
from app.utils.common_util import get_device_id
from app.utils.auth_helper import create_impersonation_token
from app.utils import redis_helper, cookie_helper
from app.exceptions.http_exceptions import ForbiddenException, NotFoundException

router = APIRouter(prefix="/admin")

settings = get_settings()


def _is_admin(user_id: str) -> bool:
    allowlist = [uid.strip() for uid in settings.admin_user_ids.split(",") if uid.strip()]
    return user_id in allowlist


@router.post("/impersonations", response_model=ApiResponse[ImpersonationIssueResponse])
async def issue_impersonation(
    request: Request,
    response: Response,
    body: ImpersonationIssueRequest,
    user_agent: str = Header(...),
    current_user: User = Depends(get_current_user),
    services: Services = Depends(get_services),
):
    actor_user_id = getattr(request.state, "actor_user_id", current_user.user_id)
    if not _is_admin(actor_user_id):
        raise ForbiddenException("관리자만 접근할 수 있습니다.")

    user = services.user.find_user_by_user_id(services.session, body.target_user_id)

    if not user:
        raise NotFoundException("해당 사용자를 찾을 수 없습니다.")

    device_id = get_device_id(user_agent)
    token, jti = create_impersonation_token(actor_user_id, body.target_user_id, device_id, reason=body.reason)

    cookie_helper.set_access_token_cookie(response, token, device_id)
    redis_helper.impersonation.store_value(jti, settings.impersonation_token_expire_minutes * 60, token)

    data = ImpersonationIssueResponse(jti=jti, actor_user_id=actor_user_id, target_user_id=body.target_user_id)
    return ApiResponse.with_data(data=data, message="임퍼소네이션 토큰 발급 완료")


@router.delete("/impersonations/{jti}")
async def revoke_impersonation(jti: str):
    token = redis_helper.impersonation.get_value(jti)
    if token:
        ttl = redis_helper.impersonation.get_ttl(jti)
        if ttl and ttl > 0:
            redis_helper.jwt.blacklist(token, ttl)
        else:
            redis_helper.jwt.blacklist(token, 600)
        redis_helper.impersonation.delete_value(jti)
    return ApiResponse.ok("임퍼소네이션 토큰이 철회되었습니다.")
