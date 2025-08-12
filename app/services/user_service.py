from fastapi import Response, HTTPException
from sqlmodel import Session, select
from app.entity.user import User, UserCreate, UserResponse
from app.models.schemas import ResetPasswordRequest
from app.utils.auth_helper import (
    verify_password,
)
from app.exceptions.http_exceptions import (
    ConflictException,
    NotFoundException,
    UnauthorizedException,
    UnprocessableEntityException,
)
from app.core.config import get_settings
from app.utils import auth_helper, redis_helper
import hashlib
from typing import Literal
from jose import jwt
from datetime import datetime
from app.exceptions.http_exceptions import ServerException
import json

settings = get_settings()


class UserService:
    def __init__(self):
        pass

    def create_user(self, session: Session, user_create: UserCreate) -> User:
        # user_id 중복 확인
        existing_user = session.exec(select(User).where(User.user_id == user_create.user_id)).first()
        if existing_user:
            raise ConflictException("이미 존재하는 사용자 ID입니다.")

        # 이메일 중복 확인
        existing_email = session.exec(select(User).where(User.email == user_create.email)).first()
        if existing_email:
            raise ConflictException("이미 존재하는 이메일입니다.")

        try:
            # 비밀번호 해싱 및 사용자 생성
            db_user = User.model_validate(user_create)
            session.add(db_user)
            session.commit()
            session.refresh(db_user)
            return db_user
        except Exception as e:
            session.rollback()
            raise ServerException(f"사용자 생성 중 오류가 발생했습니다: {str(e)}")

    def reset_user_password(self, session: Session, request: ResetPasswordRequest):
        stored_uuid = redis_helper.find_account.get_value(request.email)
        if stored_uuid != request.uuid:
            raise UnauthorizedException("인증 정보가 일치하지 않습니다.")

        user = session.exec(select(User).where(User.email == request.email)).first()
        if not user:
            raise NotFoundException("해당 사용자를 찾을 수 없습니다.")

        redis_helper.find_account.delete_value(request.email)

        try:
            user.password = request.new_password
            session.commit()
        except Exception as e:
            session.rollback()
            raise ServerException("비밀번호 재설정 중 오류가 발생했습니다.", data=str(e))

    def leave_user(self, session: Session, user_id: str):
        user = session.exec(select(User).where(User.user_id == user_id)).first()
        if not user:
            raise NotFoundException("해당 사용자를 찾을 수 없습니다.")

        if user.status == "LEAVE":
            raise ConflictException("이미 탈퇴한 사용자입니다.")

        try:
            user.status = "LEAVE"
            redis_helper.jwt.delete_all_tokens(user_id, "access_token")
            redis_helper.jwt.delete_all_tokens(user_id, "refresh_token")
            session.commit()
        except Exception as e:
            session.rollback()
            raise ServerException("탈퇴 처리 중 오류가 발생했습니다.", data=str(e))

    def check_email_exist(self, session: Session, email: str) -> bool:
        existing_email = session.exec(select(User).where(User.email == email)).first()
        return existing_email is not None

    def check_phone_exist(self, session: Session, phone: str) -> bool:
        existing_phone = session.exec(select(User).where(User.phone == phone)).first()
        return existing_phone is not None

    def find_user_by_user_id(self, session: Session, user_id: str) -> User | None:
        return session.exec(select(User).where(User.user_id == user_id)).first()

    def find_user_by_email(self, session: Session, email: str) -> User | None:
        """이메일로 사용자 찾기"""
        return session.exec(select(User).where(User.email == email)).first()

    def authenticate_user(self, session: Session, user_id: str, password: str, ts: str) -> User:
        user = session.exec(select(User).where(User.user_id == user_id)).first()
        if not user:
            raise UnauthorizedException("아이디 또는 비밀번호가 올바르지 않습니다.")

        if not verify_password(client_hash_password=password, server_hash_password=user.password, timestamp=ts):
            raise UnauthorizedException("아이디 또는 비밀번호가 올바르지 않습니다.")

        # 멀티 디바이스 지원으로 기존 세션 무효화 제거
        return user

    def get_device_id(self, user_agent: str) -> str:
        if not user_agent:
            raise UnprocessableEntityException("비정상적인 요청입니다.")
        return hashlib.md5(user_agent.encode()).hexdigest()

    def clear_auth_cookies(self, response: Response, device_id: str):
        is_production = settings.env == "production"
        response.delete_cookie(
            key=f"access_token_zcut_{device_id}", path="/", domain=".zapcut.io" if is_production else None
        )
        response.delete_cookie(
            key=f"refresh_token_zcut_{device_id}", path="/", domain=".zapcut.io" if is_production else None
        )

    def blacklist_token(self, token: str, expires_delta: int):
        redis_helper.jwt.blacklist(token, expires_delta)

    def logout_all_devices(self, user_id: str):
        tokens = redis_helper.jwt.get_all_refresh_tokens(user_id)
        for token in tokens:
            try:
                payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"], options={"verify_exp": False})
                exp_timestamp = payload.get("exp", 0)
                current_timestamp = datetime.utcnow().timestamp()

                if exp_timestamp > current_timestamp:
                    remaining_seconds = int(exp_timestamp - current_timestamp)
                    redis_helper.jwt.blacklist(token, remaining_seconds)
                else:
                    redis_helper.jwt.blacklist(token, 3600)
            except:
                redis_helper.jwt.blacklist(token, 3600)

        redis_helper.jwt.delete_all_tokens(user_id, "refresh_token")
        redis_helper.jwt.delete_all_tokens(user_id, "access_token")
