from app.utils import redis_helper
from app.exceptions.http_exceptions import TooManyRequestsException
from fastapi import Request
from app.utils.common_util import get_device_id


def get_client_ip(request: Request) -> str:
    """실제 클라이언트 IP를 추출합니다 (ALB 고려)"""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    return request.client.host


def check_rate_limit(request: Request, max_requests: int, window_seconds: int, prefix: str = "rate_limit") -> None:
    client_ip = get_client_ip(request)
    key = f"{prefix}:ip:{client_ip}"

    if not redis_helper.rate_limiter.is_allowed(key, max_requests, window_seconds):
        remaining_time = redis_helper.rate_limiter.get_reset_time(key)
        raise TooManyRequestsException(f"요청이 너무 많습니다. {remaining_time}초 후에 다시 시도해주세요.")


def check_user_rate_limit(user_id: str, max_requests: int, window_seconds: int, prefix: str = "rate_limit") -> None:
    """user_id 기반 rate limiting을 체크합니다"""
    key = f"{prefix}:user:{user_id}"

    if not redis_helper.rate_limiter.is_allowed(key, max_requests, window_seconds):
        remaining_time = redis_helper.rate_limiter.get_reset_time(key)
        raise TooManyRequestsException(f"요청이 너무 많습니다. {remaining_time}초 후에 다시 시도해주세요.")
