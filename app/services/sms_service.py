import aiohttp
from aiohttp_socks import ProxyConnector
from app.core.config import get_settings
from app.exceptions.http_exceptions import ServerException
from app.utils import redis_helper
import json


class SMSService:
    def __init__(self):
        self.settings = get_settings()
        self.aligo_api_key = self.settings.aligo_key
        self.aligo_user_id = "lodestar4u"
        self.aligo_sender = "010-7597-0292"
        self.aligo_send_url = "https://apis.aligo.in/send/"

    async def send_verify_code(self, phone_number: str) -> bool:
        send_count = redis_helper.phone_verify.increment_send_count(phone_number)
        if send_count > 5:
            remaining_time = redis_helper.phone_verify.get_send_count_ttl(phone_number)
            raise ServerException(f"5분 내 5회 이상 SMS 전송을 시도했습니다. {remaining_time}초 후 다시 시도해주세요.")

        verification_code = redis_helper.phone_verify.generate_verification_code()
        redis_helper.phone_verify.set_code(phone_number, verification_code)

        data = aiohttp.FormData()
        data.add_field("key", self.aligo_api_key)
        data.add_field("user_id", self.aligo_user_id)
        data.add_field("sender", self.aligo_sender)
        data.add_field("receiver", phone_number)
        data.add_field("msg", f"[ZAPCUT] 회원가입 인증번호[{verification_code}]를 화면에 입력해주세요.")
        # data.add_field("testmode_yn", "Y") # 테스트 모드 필요 시 주석 해제

        connector = ProxyConnector.from_url("socks5://54.180.39.0:9111") if self.settings.env == "dev" else None
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.post(self.aligo_send_url, data=data) as response:
                if response.status == 200:
                    # 응답 텍스트를 먼저 확인합니다.
                    response_text = await response.text()
                    json_response = json.loads(response_text)

                    if json_response.get("result_code") != "1":
                        raise ServerException(message="SMS 전송 실패: " + json_response.get("message"))
                else:
                    # HTTP 200이 아닌 경우에도 응답 텍스트를 확인합니다.
                    response_text = await response.text()

                    raise ServerException(message="SMS 전송 실패: " + response_text)

    async def verify_phone_code(self, phone_number: str, code: str) -> bool:
        stored_code = redis_helper.phone_verify.get_code(phone_number)
        if not stored_code:
            raise ServerException("인증코드가 만료되었거나 존재하지 않습니다.")
        if stored_code == code:
            redis_helper.phone_verify.del_code(phone_number)
            return True
        return False
