from fastapi import Depends, Cookie, Header, Request, Response
from functools import lru_cache
from app.services.google_ai_service import GoogleAIService
from app.services.video_service import VideoService
from app.services.crawling_service import CrawlingService
from app.services.email_service import EmailService
from app.services.sms_service import SMSService
from app.services.shortscript_service import ShortScriptService
from app.utils import auth_helper
from app.utils import redis_helper
from app.entity.user import User
from sqlmodel import Session, select
from app.core.database import engine
from app.exceptions.http_exceptions import UnauthorizedException, UnprocessableEntityException
import os
from app.services.user_service import UserService
import hashlib
from typing import Optional
from app.core.config import get_settings
from app.utils import cookie_helper
from app.utils.common_util import get_device_id
from datetime import timedelta

settings = get_settings()


class Services:
    def __init__(self, session: Session):
        self.video = VideoService()
        self.google_ai = GoogleAIService()
        self.crawling = CrawlingService()
        self.user = UserService()  # session 제거
        self.email = EmailService()
        self.sms = SMSService()
        self.shortscript = ShortScriptService()
        self._session = session  # session을 별도로 저장

    @property
    def session(self):
        return self._session


def get_session():
    with Session(engine) as session:
        yield session


@lru_cache()
def get_services(session: Session = Depends(get_session)) -> Services:
    return Services(session)


async def get_current_user(
    request: Request,
    response: Response,
    session: Session = Depends(get_session),
    user_agent: str = Header(...),
) -> User:
    credentials_exception = UnauthorizedException("인증 정보를 확인할 수 없습니다.")

    if not user_agent:
        raise UnprocessableEntityException("비정상적인 요청입니다.")

    device_id = get_device_id(user_agent)

    access_token = request.cookies.get(f"access_token_zcut_{device_id}")

    if not access_token:
        # refresh_token이 존재하는 경우 확인하고 새로운 access_token 발급
        refresh_token = request.cookies.get(f"refresh_token_zcut_{device_id}")

        if not refresh_token:
            raise credentials_exception

        try:
            refresh_payload = auth_helper.decode_token(refresh_token, token_type="refresh_token")
            user_id = refresh_payload.get("sub")
            token_device_id = refresh_payload.get("device_id")

            if not user_id or token_device_id != device_id:
                raise credentials_exception

            user = session.exec(select(User).where(User.user_id == user_id)).first()
            if user is None:
                raise credentials_exception

            new_access_token = auth_helper.create_token(
                data={"sub": user.user_id, "device_id": device_id}, token_type="access_token"
            )
            cookie_helper.set_access_token_cookie(response, new_access_token, device_id)
            access_token = new_access_token
        except UnauthorizedException:
            if refresh_token:
                redis_helper.jwt.blacklist(refresh_token, timedelta(days=settings.refresh_token_expire_days))
            raise
        except Exception:
            raise credentials_exception

    try:
        payload = auth_helper.decode_token(access_token, token_type="access_token")
        user_id: str = payload.get("sub")
        token_device_id: str = payload.get("device_id")

        if not user_id or token_device_id != device_id:
            raise credentials_exception

        act = payload.get("act")
        if isinstance(act, dict):
            actor_sub = act.get("sub")
            if actor_sub:
                setattr(request.state, "actor_user_id", actor_sub)

    except UnauthorizedException:
        raise
    except Exception:
        raise credentials_exception

    user = session.exec(select(User).where(User.user_id == user_id)).first()
    if user is None:
        raise credentials_exception

    if user.status == "LEAVE":
        raise UnauthorizedException("탈퇴한 사용자입니다.")

    return user
