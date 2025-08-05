from fastapi import Response
from app.core.config import get_settings

settings = get_settings()


def set_access_token_cookie(response: Response, access_token: str, device_id: str):
    is_production = settings.env == "production"
    response.set_cookie(
        key=f"access_token_zcut_{device_id}",
        value=access_token,
        httponly=True,
        secure=is_production,
        max_age=settings.access_token_expire_minutes * 60,  # 30분
        samesite="none" if is_production else "lax",
        path="/",
    )


def set_refresh_token_cookie(response: Response, refresh_token: str, device_id: str):
    is_production = settings.env == "production"
    response.set_cookie(
        key=f"refresh_token_zcut_{device_id}",
        value=refresh_token,
        httponly=True,  # 보안을 위해 httponly 유지
        secure=is_production,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,  # 7일
        samesite="none" if is_production else "lax",
        path="/",
    )
