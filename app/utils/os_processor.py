import os

from app.core.config import TEMP_DIR


def get_temp_dir(name: str):
    os.makedirs(TEMP_DIR, exist_ok=True)
    temp_dir = os.path.join(TEMP_DIR, f"{name}")
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir
