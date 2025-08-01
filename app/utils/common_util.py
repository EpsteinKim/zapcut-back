import hashlib
from app.exceptions.http_exceptions import UnprocessableEntityException
import uuid


def get_device_id(user_agent: str) -> str:
    if not user_agent:
        raise UnprocessableEntityException("User-Agent는 필수입니다.")

    return hashlib.md5(user_agent.encode()).hexdigest()


def get_random_uuid() -> str:
    return str(uuid.uuid4())
