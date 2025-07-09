import os
import shutil
import time
from datetime import datetime, timedelta

from app.core.config import TEMP_DIR


def get_temp_dir(name: str):
    os.makedirs(TEMP_DIR, exist_ok=True)
    temp_dir = os.path.join(TEMP_DIR, f"{name}")
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir


def clear_temp_dir_contents(dir_path: str):
    """
    임시폴더의 내용만 삭제하는 함수
    폴더 자체는 유지하고 내부 파일/폴더만 삭제
    """
    # 폴더가 존재하지 않으면 아무것도 하지 않음
    if not os.path.exists(dir_path):
        return

    # 폴더 내부의 모든 파일과 폴더 삭제
    for item in os.listdir(dir_path):
        item_path = os.path.join(dir_path, item)
        try:
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.unlink(item_path)  # 파일 또는 심볼릭 링크 삭제
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)  # 디렉토리 삭제
        except Exception as e:
            print(f"Error deleting {item_path}: {e}")


def get_file_age_hours(file_path: str) -> float:
    try:
        mtime = os.path.getmtime(file_path)
        current_time = time.time()
        age_seconds = current_time - mtime
        return age_seconds / 3600
    except Exception:
        return 0.0


def cleanup_old_files(dir_path: str, max_age_hours: int = 24):
    if not os.path.exists(dir_path):
        return

    current_time = time.time()
    deleted_count = 0

    for root, dirs, files in os.walk(dir_path):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                mtime = os.path.getmtime(file_path)
                age_hours = (current_time - mtime) / 3600

                if age_hours > max_age_hours:
                    os.unlink(file_path)
                    deleted_count += 1
                    print(f"Deleted old file: {file_path} (age: {age_hours:.1f}h)")
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")

        for dir_name in dirs:
            dir_path_full = os.path.join(root, dir_name)
            try:
                if not os.listdir(dir_path_full):
                    os.rmdir(dir_path_full)
                    print(f"Removed empty directory: {dir_path_full}")
            except Exception:
                pass

    if deleted_count > 0:
        print(f"Cleaned up {deleted_count} old files from {dir_path}")
