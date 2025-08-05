from datetime import datetime, timedelta
from typing import Optional, Tuple
import hashlib

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import get_settings
from app.exceptions.http_exceptions import UnauthorizedException
from app.utils import redis_helper

# JWT 설정 로드
settings = get_settings()
SECRET_KEY = settings.secret_key

# 비밀번호 해싱을 위한 CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(client_hash_password: str, server_hash_password: str, timestamp: str) -> bool:
    hash_password = hashlib.sha256(f"{server_hash_password}{timestamp}".encode()).hexdigest()
    return client_hash_password == hash_password


def create_access_token(data: dict) -> str:
    """토큰을 생성합니다."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return encoded_jwt


# {sub: user_id, device_id: device_id}
def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    redis_helper.jwt.store_refresh_token(data["sub"], encoded_jwt, data["device_id"])
    return encoded_jwt


def decode_refresh_token(token: str) -> dict:
    try:
        if redis_helper.jwt.is_blacklisted(token):
            raise UnauthorizedException("무효화된 토큰입니다.")
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
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
