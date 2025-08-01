import aiohttp
import json
import asyncio
from typing import Dict, Any, List
from app.core.config import get_settings
from app.exceptions.http_exceptions import ServerException
from app.utils import redis_helper
from aiohttp_socks import ProxyConnector
import uuid
from app.utils.common_util import get_random_uuid

settings = get_settings()


class EmailService:
    def __init__(self):
        self.api_key = settings.brevo_key
        self.base_url = "https://api.brevo.com/v3/smtp/email"

    async def send_via_brevo_with_template(self, to: str, model: Dict[str, Any]) -> None:
        template_id = model.pop("templateId", None)
        if not template_id:
            raise ValueError("templateId is required")

        request_body = {"to": [{"email": to}], "templateId": template_id, "params": model}

        headers = {"accept": "application/json", "content-type": "application/json", "api-key": self.api_key}

        max_retries = 3
        retry_delay = 3

        for attempt in range(max_retries + 1):
            try:
                # ProxyConnector를 메서드 내부에서 생성하여 각 요청마다 새로운 인스턴스를 사용
                connector = ProxyConnector.from_url("socks5://54.180.39.0:9111") if settings.env == "dev" else None

                async with aiohttp.ClientSession(connector=connector) as session:
                    async with session.post(
                        self.base_url,
                        json=request_body,
                        headers=headers,
                    ) as response:
                        if response.status == 201 or response.status == 200:
                            return await response.text()
                        else:
                            response_text = await response.text()
                            raise ServerException(f"({response.status}): {response_text}")

            except ServerException:
                raise
            except Exception as e:
                error_message = str(e).lower()
                if "tls" in error_message and attempt < max_retries:
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    raise ServerException(str(e))

    async def send_email_code(self, email: str) -> Dict[str, Any]:
        send_count = redis_helper.email_verify.increment_send_count(email)

        if send_count > 5:
            remaining_time = redis_helper.email_verify.get_send_count_ttl(email)
            raise ServerException(f"5분 내 5회 이상 인증메일을 요청했습니다. {remaining_time}초 후 다시 시도해주세요.")

        verification_code = redis_helper.email_verify.generate_verification_code()
        redis_helper.email_verify.set_code(email, verification_code)

        model = {"templateId": 14, "code": verification_code}

        await self.send_via_brevo_with_template(email, model)

        return {"message": "인증코드가 전송되었습니다.", "remaining_attempts": 5 - send_count}

    def verify_email_code(self, email: str, input_code: str) -> bool:
        stored_code = redis_helper.email_verify.get_code(email)

        if not stored_code:
            raise ServerException("인증코드가 만료되었거나 존재하지 않습니다.")

        if stored_code == input_code:
            redis_helper.email_verify.del_code(email)
            return True

        return False

    async def send_find_account_uuid(self, email: str, user_id: str):
        random_uuid = get_random_uuid()
        redis_helper.find_account.store_value(email, 600, random_uuid)
        redis_helper.find_account.store_value(f"{email}_searchable", 600, "1")

        model = {
            "templateId": 15,
            "resetUrl": f"{settings.client_host}/reset-password/{random_uuid}",
            "userId": user_id,
        }
        await self.send_via_brevo_with_template(email, model)
        return

    async def verify_find_account_uuid(self, email: str, uuid: str) -> bool:
        if not redis_helper.find_account.exists(email):
            return False

        stored_uuid = redis_helper.find_account.get_value(email)
        if stored_uuid != uuid:
            return False

        if redis_helper.find_account.exists(f"{email}_searchable"):
            redis_helper.find_account.delete_value(f"{email}_searchable")
            return True
