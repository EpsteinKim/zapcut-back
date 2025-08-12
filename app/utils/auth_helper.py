from datetime import datetime, timedelta
from typing import Literal, Optional, Tuple
import hashlib

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import get_settings
from app.exceptions.http_exceptions import UnauthorizedException
from app.utils import redis_helper
from app.utils.common_util import get_random_uuid

# JWT 설정 로드
settings = get_settings()
SECRET_KEY = settings.secret_key

# 비밀번호 해싱을 위한 CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(client_hash_password: str, server_hash_password: str, timestamp: str) -> bool:
    hash_password = hashlib.sha256(f"{server_hash_password}{timestamp}".encode()).hexdigest()
    return client_hash_password == hash_password


# {sub: user_id, device_id: device_id}, token_type: "access_token" or "refresh_token"
# 토큰 생성 후 redis에 저장
def create_token(data: dict, token_type: Literal["access_token", "refresh_token"]) -> str:
    to_encode = data.copy()
    if token_type == "access_token":
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    else:
        expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    redis_helper.jwt.store_token(
        user_id=data["sub"], token=encoded_jwt, device_id=data["device_id"], token_type=token_type
    )
    return encoded_jwt


def decode_token(token: str, token_type: Literal["access_token", "refresh_token"]) -> dict:
    try:
        if redis_helper.jwt.is_blacklisted(token):
            raise UnauthorizedException("무효화된 토큰입니다.")

        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        redis_stored_token = redis_helper.jwt.get_token(
            user_id=payload["sub"], device_id=payload["device_id"], token_type=token_type
        )
        if redis_stored_token == token:
            return payload
        else:
            raise UnauthorizedException("무효화된 토큰입니다.")
    except UnauthorizedException as e:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"], options={"verify_exp": False})
            exp_timestamp = payload.get("exp", 0)
            current_timestamp = datetime.utcnow().timestamp()

            if exp_timestamp > current_timestamp:
                remaining_seconds = int(exp_timestamp - current_timestamp)
                redis_helper.jwt.blacklist(token, remaining_seconds)
            else:
                redis_helper.jwt.blacklist(token, 3600)
        except:
            redis_helper.jwt.blacklist(token, 3600)

        raise e


def create_impersonation_token(
    admin_user_id: str, target_user_id: str, device_id: str, reason: str | None = None, scope: str = "impersonation"
) -> tuple[str, str]:
    to_encode = {
        "sub": target_user_id,
        "device_id": device_id,
        "act": {"sub": admin_user_id},
        "scope": scope,
        "reason": reason or "",
        "jti": get_random_uuid(),
    }
    expire = datetime.utcnow() + timedelta(minutes=settings.impersonation_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    redis_helper.jwt.store_token(
        user_id=target_user_id, token=encoded_jwt, device_id=device_id, token_type="access_token"
    )
    return encoded_jwt, to_encode["jti"]
