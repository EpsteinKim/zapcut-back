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


def get_password_hash(password: str) -> str:
    """비밀번호를 해싱합니다. (DB 저장용)"""
    return hashlib.sha256(f"{password}{SECRET_KEY}".encode()).hexdigest()


def create_token(data: dict, expires_delta: timedelta) -> str:
    """토큰을 생성합니다."""
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return encoded_jwt


def create_access_token(data: dict) -> str:
    """액세스 토큰을 생성합니다."""
    return create_token(data=data, expires_delta=timedelta(minutes=settings.access_token_expire_minutes))


def create_refresh_token(data: dict) -> str:
    refresh_token = create_token(data=data, expires_delta=timedelta(days=settings.refresh_token_expire_days))
    device_id = data.get("device_id")
    redis_helper.jwt.store_refresh_token(data["sub"], refresh_token, device_id)
    return refresh_token


def decode_unsafe_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=["HS256"], options={"verify_exp": False})
    except:
        return None


def decode_token(token: str) -> dict:
    try:
        if redis_helper.jwt.is_blacklisted(token):
            raise UnauthorizedException("무효화된 토큰입니다.")

        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError:
        raise UnauthorizedException("유효하지 않은 인증 토큰입니다.")


def decode_refresh_token(token: str, user_id: str, device_id: str) -> dict:
    try:
        payload = decode_token(token)
        if payload["sub"] != user_id or payload["device_id"] != device_id:
            raise UnauthorizedException("유효하지 않은 리프레시 토큰입니다.")
        return payload
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
