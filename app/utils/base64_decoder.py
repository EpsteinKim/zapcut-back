import base64
from typing import Union
from io import BytesIO


def decode_base64_data(data: Union[str, bytes]) -> bytes:
    if isinstance(data, (str, bytes)):
        try:
            if isinstance(data, str):
                return base64.b64decode(data)
            else:
                # bytes인 경우 base64 디코딩 시도
                return base64.b64decode(data)
        except Exception:
            # 디코딩 실패시 원본 데이터 사용
            return data if isinstance(data, bytes) else data.encode()
    else:
        # 다른 타입인 경우 그대로 반환 (bytes로 변환 시도)
        return data if isinstance(data, bytes) else str(data).encode()


def decode_base64_to_bytesio(data: Union[str, bytes]) -> BytesIO:
    decoded_data = decode_base64_data(data)
    return BytesIO(decoded_data)
