import os
import shutil
import time
from datetime import datetime, timedelta

from app.core.config import TEMP_DIR


def get_temp_dir(name: str):
    try:
        os.makedirs(TEMP_DIR, exist_ok=True)
        temp_dir = os.path.join(TEMP_DIR, f"{name}")
        os.makedirs(temp_dir, exist_ok=True)

        # 디렉토리 권한 확인 및 설정
        if not os.access(temp_dir, os.W_OK):
            os.chmod(temp_dir, 0o755)

        return temp_dir
    except Exception as e:
        raise Exception(f"임시 디렉토리 생성 실패: {temp_dir} - {str(e)}")
