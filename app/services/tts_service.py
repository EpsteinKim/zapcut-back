import requests
import json
import time
from app.core.config import get_settings
from app.exceptions.http_exceptions import ServerException


class TTSService:
    def __init__(self):
        settings = get_settings()
        self.typecast_api_key = settings.typecast_api_key
        self.url = "https://typecast.ai/api/speak"
        self.headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.typecast_api_key}"}

    async def get_download_speech_url(self, text: str, duration: int = 60) -> str:
        payload = {
            "actor_id": "6596849ea3ecaa12a8b13989",
            "text": text,
            "lang": "auto",
            "tempo": 1,
            "volume": 100,
            "pitch": 0,
            "xapi_hd": True,
            "max_seconds": duration,
            "model_version": "latest",
            "xapi_audio_format": "mp3",
        }

        response = requests.post(self.url, headers=self.headers, json=payload)

        if response.status_code != 200:
            raise ServerException(f"TTS 생성 실패: {response.text}")

        result = response.json()

        getUrl = result["result"]["speak_v2_url"]

        getResponse = requests.get(getUrl, headers={"Authorization": f"Bearer {self.typecast_api_key}"})

        if getResponse.status_code != 200:
            raise ServerException(f"TTS 생성 실패: {getResponse.text}")

        getResult = getResponse.json()
        status = getResult["result"]["status"]

        # status가 done이나 failed가 아닐 경우 1초 간격으로 재시도
        while status not in ["done", "failed"]:
            time.sleep(1)
            getResponse = requests.get(getUrl, headers={"Authorization": f"Bearer {self.typecast_api_key}"})

            if getResponse.status_code != 200:
                raise ServerException(f"TTS 생성 실패: {getResponse.text}")

            getResult = getResponse.json()
            print(getResult)
            status = getResult["result"]["status"]

        if status == "failed":
            raise ServerException(str(getResult))

        print(getResult)
        return getResult["result"]["audio_download_url"]
