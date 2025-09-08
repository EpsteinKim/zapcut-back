from redis import Redis
from app.core.config import get_settings
from datetime import timedelta
import json
import random
import string
from typing import Literal, Optional
import time

settings = get_settings()

redis_client = Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    password=settings.redis_password,
    db=settings.redis_db,
    decode_responses=True,
)


class TokenHelper:
    @staticmethod
    def store_token(
        user_id: str,
        token: str,
        device_id: str,
        token_type: Literal["access_token", "refresh_token", "impersonation_token"],
    ) -> None:
        if token_type == "access_token":
            expiry = timedelta(minutes=settings.access_token_expire_minutes)
        elif token_type == "refresh_token":
            expiry = timedelta(days=settings.refresh_token_expire_days)
        elif token_type == "impersonation_token":
            expiry = timedelta(minutes=settings.impersonation_token_expire_minutes)

        redis_client.setex(f"{token_type}:{user_id}:{device_id}", int(expiry.total_seconds()), token)

    def exists_token(
        user_id: str, device_id: str, token_type: Literal["access_token", "refresh_token", "impersonation_token"]
    ) -> bool:
        return redis_client.exists(f"{token_type}:{user_id}:{device_id}")

    @staticmethod
    def get_token(
        user_id: str, device_id: str, token_type: Literal["access_token", "refresh_token", "impersonation_token"]
    ) -> str | None:
        return redis_client.get(f"{token_type}:{user_id}:{device_id}")

    @staticmethod
    def delete_token(
        user_id: str, device_id: str, token_type: Literal["access_token", "refresh_token", "impersonation_token"]
    ) -> None:
        redis_client.delete(f"{token_type}:{user_id}:{device_id}")

    @staticmethod
    def get_all_tokens(
        user_id: str, token_type: Literal["access_token", "refresh_token", "impersonation_token"]
    ) -> list[str]:
        pattern = f"{token_type}:{user_id}:*"
        keys = redis_client.keys(pattern)
        tokens = []
        for key in keys:
            token = redis_client.get(key)
            if token:
                tokens.append(token)
        return tokens

    @staticmethod
    def delete_all_tokens(
        user_id: str, token_type: Literal["access_token", "refresh_token", "impersonation_token"]
    ) -> None:
        pattern = f"{token_type}:{user_id}:*"
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)

    @staticmethod
    def is_blacklisted(token: str) -> bool:
        return redis_client.exists(f"blacklist:{token}")

    @staticmethod
    def blacklist(token: str, expires_delta: int) -> None:
        redis_client.setex(f"blacklist:{token}", expires_delta, "1")


class SimpleHelper:
    def __init__(self, prefix: str, window_seconds: int | None = None):
        self.prefix = prefix
        self.rate_limit_seconds = window_seconds if window_seconds else 60

    # value 관련 메서드
    def store_value(self, identifier: str, time_seconds: int, value: str) -> None:
        redis_client.setex(f"{self.prefix}:{identifier}", time_seconds, value)

    def get_value(self, identifier: str) -> str | None:
        return redis_client.get(f"{self.prefix}:{identifier}")

    def delete_value(self, identifier: str) -> None:
        redis_client.delete(f"{self.prefix}:{identifier}")

    def exists(self, identifier: str) -> bool:
        return redis_client.exists(f"{self.prefix}:{identifier}")

    def get_ttl(self, identifier: str) -> int:
        return redis_client.ttl(f"{self.prefix}:{identifier}")

    # count 관련 메서드
    def increment_count(self, identifier: str) -> int:
        redis_key = f"{self.prefix}_count:{identifier}"
        count = redis_client.incr(redis_key)
        if count == 1:
            redis_client.expire(redis_key, self.rate_limit_seconds)
        return count

    def get_count(self, identifier: str) -> int:
        count = redis_client.get(f"{self.prefix}_count:{identifier}")
        return int(count) if count else 0

    def delete_count(self, identifier: str) -> None:
        redis_client.delete(f"{self.prefix}_count:{identifier}")

    def exists_count(self, identifier: str) -> bool:
        return redis_client.exists(f"{self.prefix}_count:{identifier}")

    def get_count_ttl(self, identifier: str) -> int:
        return redis_client.ttl(f"{self.prefix}_count:{identifier}")


class BaseVerificationHelper:
    def __init__(self, prefix: str):
        self.prefix = prefix

    def generate_verification_code(self) -> str:
        return "".join(random.choices(string.digits, k=6))

    def set_code(self, identifier: str, code: str) -> None:
        redis_client.setex(f"{self.prefix}_verification:{identifier}", 180, code)  # 3분 만료

    def get_code(self, identifier: str) -> str | None:
        return redis_client.get(f"{self.prefix}_verification:{identifier}")

    def del_code(self, identifier: str) -> None:
        redis_client.delete(f"{self.prefix}_verification:{identifier}")

    def increment_send_count(self, identifier: str) -> int:
        key = f"{self.prefix}_send_count:{identifier}"
        count = redis_client.incr(key)
        if count == 1:
            redis_client.expire(key, 600)  # 10분 만료
        return count

    def get_send_count(self, identifier: str) -> int:
        count = redis_client.get(f"{self.prefix}_send_count:{identifier}")
        return int(count) if count else 0

    def get_send_count_ttl(self, identifier: str) -> int:
        """send_count 키의 남은 시간을 반환합니다."""
        return redis_client.ttl(f"{self.prefix}_send_count:{identifier}")

    def set_verification_complete(self, identifier: str, device_id: str) -> None:
        """인증 완료 정보 저장 (10분 만료)"""
        key = f"{self.prefix}_verified:{identifier}:{device_id}"
        redis_client.setex(key, 600, "1")  # 10분 만료, 단순히 "1" 값만 저장

    def get_verification_complete(self, identifier: str, device_id: str) -> bool:
        """인증 완료 정보 조회"""
        key = f"{self.prefix}_verified:{identifier}:{device_id}"
        return redis_client.exists(key)

    def del_verification_complete(self, identifier: str, device_id: str) -> None:
        """인증 완료 정보 삭제"""
        key = f"{self.prefix}_verified:{identifier}:{device_id}"
        redis_client.delete(key)

    def is_verified(self, identifier: str, device_id: str) -> bool:
        """인증 완료 여부 확인"""
        return redis_client.exists(f"{self.prefix}_verified:{identifier}:{device_id}")


class RateLimiter:
    def __init__(self, prefix: str = "rate_limit"):
        self.prefix = prefix

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        redis_key = f"{self.prefix}:{key}"
        current_count = redis_client.get(redis_key)

        if current_count is None:
            # 첫 번째 요청
            redis_client.setex(redis_key, window_seconds, 1)
            return True

        count = int(current_count)
        if count >= max_requests:
            return False

        # 요청 수 증가
        redis_client.incr(redis_key)
        return True

    def get_remaining_requests(self, key: str) -> int:
        redis_key = f"{self.prefix}:{key}"
        current_count = redis_client.get(redis_key)
        if current_count is None:
            return 0
        return int(current_count)

    def get_reset_time(self, key: str) -> int:
        redis_key = f"{self.prefix}:{key}"
        return redis_client.ttl(redis_key)

    def reset(self, key: str) -> None:
        redis_key = f"{self.prefix}:{key}"
        redis_client.delete(redis_key)


jwt = TokenHelper()
email_verify = BaseVerificationHelper("email")
phone_verify = BaseVerificationHelper("phone")
rate_limiter = RateLimiter()
find_account = SimpleHelper("find_account")
