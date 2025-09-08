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
from app.exceptions.http_exceptions import UnauthorizedException, UnprocessableEntityException, NotFoundException
import os
from app.services.user_service import UserService
import hashlib
from typing import Optional
from app.core.config import get_settings
from app.utils import cookie_helper
from app.utils.common_util import get_device_id, is_admin
from datetime import timedelta
from pydantic import BaseModel
from app.models.schemas import CurrentUserInfo

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


async def get_current_user_info(
    request: Request,
    response: Response,
    session: Session = Depends(get_session),
    user_agent: str = Header(...),
) -> CurrentUserInfo:
    credentials_exception = UnauthorizedException("인증 정보를 확인할 수 없습니다.")

    if not user_agent:
        raise UnprocessableEntityException("비정상적인 요청입니다.")

    device_id = get_device_id(user_agent)

    impersonate_token = request.cookies.get(f"impersonate_token_zcut_{device_id}")

    access_token = request.cookies.get(f"access_token_zcut_{device_id}")

    if not access_token and not impersonate_token:
        # refresh_token이 존재하는 경우 확인하고 새로운 access_token 발급
        refresh_token = request.cookies.get(f"refresh_token_zcut_{device_id}")

        if not refresh_token:
            raise credentials_exception

        try:
            refresh_payload = auth_helper.decode_token_and_verify(refresh_token, device_id, "refresh_token")
            user_id = refresh_payload.get("sub")

            if not user_id:
                raise credentials_exception

            user = session.exec(select(User).where(User.user_id == user_id)).first()
            if user is None:
                raise credentials_exception

            new_access_token = auth_helper.create_token(user.user_id, device_id, "access_token")
            cookie_helper.set_access_token_cookie(response, new_access_token, device_id)

            access_token = new_access_token
        except UnauthorizedException:
            if refresh_token:
                redis_helper.jwt.blacklist(refresh_token, timedelta(days=settings.refresh_token_expire_days))
                cookie_helper.delete_refresh_token_cookie(response, device_id)
            raise
        except Exception:
            raise credentials_exception

    try:

        if impersonate_token:
            try:
                payload = auth_helper.decode_token_and_verify(impersonate_token, device_id, "impersonation_token")
                admin_user_id = payload.get("impersonate_admin_user_id")
            except UnauthorizedException:
                cookie_helper.delete_impersonate_token_cookie(response, device_id)
                raise

            if not is_admin(admin_user_id):
                cookie_helper.delete_impersonate_token_cookie(response, device_id)
                raise UnauthorizedException("누구세요? 누구세요? 누구세요? 누구세요? 누구세요? 누구세요?")
        else:
            payload = auth_helper.decode_token_and_verify(access_token, device_id, "access_token")

        user_id: str = payload.get("sub")

        if not user_id:
            raise credentials_exception
    except UnauthorizedException:
        raise
    except Exception:
        raise credentials_exception

    user = session.exec(select(User).where(User.user_id == user_id)).first()

    is_impersonate = payload.get("impersonate_admin_user_id") is not None

    if user is None:
        raise NotFoundException("해당 사용자를 찾을 수 없습니다.")

    if not is_impersonate and user.status == "LEAVE":
        raise UnauthorizedException("탈퇴한 사용자입니다.")

    admin_list = [uid.strip() for uid in settings.admin_user_ids.split(",") if uid.strip()]
    if user.user_id in admin_list or is_impersonate:
        cookie_helper.set_is_admin_cookie(response)
    else:
        cookie_helper.delete_is_admin_cookie(response)

    return CurrentUserInfo(user=user, payload=payload)
