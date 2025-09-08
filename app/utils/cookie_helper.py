from fastapi import Response
from app.core.config import get_settings

settings = get_settings()


def with_default_cookie_config(response: Response, key: str, value: str, max_age: int, httponly: bool = True):
    """보안 설정이 적용된 쿠키 설정"""
    is_production = settings.env == "production"
    default_config = {
        "secure": is_production,
        "samesite": "none" if is_production else "lax",
        "path": "/",
    }
    response.set_cookie(key=key, value=value, max_age=max_age, httponly=httponly, **default_config)


def set_access_token_cookie(response: Response, access_token: str, device_id: str):
    with_default_cookie_config(
        response=response,
        key=f"access_token_zcut_{device_id}",
        value=access_token,
        max_age=settings.access_token_expire_minutes * 60,
        httponly=True,
    )


def delete_access_token_cookie(response: Response, device_id: str):
    response.delete_cookie(key=f"access_token_zcut_{device_id}", path="/")


def set_refresh_token_cookie(response: Response, refresh_token: str, device_id: str):
    with_default_cookie_config(
        response=response,
        key=f"refresh_token_zcut_{device_id}",
        value=refresh_token,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        httponly=True,
    )


def delete_refresh_token_cookie(response: Response, device_id: str):
    response.delete_cookie(key=f"refresh_token_zcut_{device_id}", path="/")


def set_is_admin_cookie(response: Response):
    with_default_cookie_config(
        response=response, key="is_admin_zcut", value=str(True).lower(), max_age=3600 * 24 * 30, httponly=False
    )


def delete_is_admin_cookie(response: Response):
    response.delete_cookie(key="is_admin_zcut", path="/")


def set_impersonate_token_cookie(response: Response, impersonate_token: str, device_id: str):
    with_default_cookie_config(
        response=response,
        key=f"impersonate_token_zcut_{device_id}",
        value=impersonate_token,
        max_age=settings.impersonation_token_expire_minutes * 60,
        httponly=True,
    )


def delete_impersonate_token_cookie(response: Response, device_id: str):
    response.delete_cookie(key=f"impersonate_token_zcut_{device_id}", path="/")
