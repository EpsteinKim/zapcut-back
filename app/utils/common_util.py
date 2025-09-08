import hashlib
from app.exceptions.http_exceptions import UnprocessableEntityException
import uuid
from app.core.config import get_settings

settings = get_settings()


def get_device_id(user_agent: str) -> str:
    if not user_agent:
        raise UnprocessableEntityException("User-Agent는 필수입니다.")

    return hashlib.md5(user_agent.encode()).hexdigest()


def get_random_uuid() -> str:
    return str(uuid.uuid4())


def is_admin(user_id: str) -> bool:
    allowlist = [uid.strip() for uid in settings.admin_user_ids.split(",") if uid.strip()]
    return user_id in allowlist
