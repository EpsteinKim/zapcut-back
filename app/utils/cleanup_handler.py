import os
import shutil
import signal
import sys
import atexit
import threading
import logging
import time
from typing import Optional
import uuid
from app.utils.redis_helper import redis_client

logger = logging.getLogger(__name__)


def cleanup_old_files(dir_path: str, max_age_seconds: int = 3600):
    if not os.path.exists(dir_path):
        return

    current_time = time.time()
    deleted_count = 0

    for root, dirs, files in os.walk(dir_path):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                mtime = os.path.getmtime(file_path)
                age_seconds = current_time - mtime

                if age_seconds > max_age_seconds:
                    os.unlink(file_path)
                    deleted_count += 1
            except Exception as e:
                logger.error(f"❌ 파일 처리 중 오류 발생 {file_path}: {e}")

    if deleted_count > 0:
        logger.info(f"🧹 {dir_path}에서 오래된 파일 {deleted_count}개 정리 완료")


class CleanupHandler:
    def __init__(self, temp_dir: str, auto_cleanup_interval: int = 60 * 5, max_file_age_seconds: int = 60 * 20):
        self.temp_dir = temp_dir
        self.auto_cleanup_interval = auto_cleanup_interval
        self.max_file_age_seconds = max_file_age_seconds
        self._cleanup_done = False
        self._cleanup_lock = threading.Lock()
        self._auto_cleanup_thread = None
        self._stop_auto_cleanup = threading.Event()
        self._lock_key = "cleanup:leader"
        self._lock_owner = str(uuid.uuid4())
        self._lock_ttl = max(self.auto_cleanup_interval * 2, 300)
        self._is_leader = False
        self._setup_handlers()
        self._start_auto_cleanup()

    def _setup_handlers(self):
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGQUIT, self._signal_handler)
        signal.signal(signal.SIGHUP, self._signal_handler)
        atexit.register(self._atexit_handler)
        logger.info("🧹 CleanupHandler 초기화 완료")

    def _acquire_lock(self) -> bool:
        try:
            ok = redis_client.set(self._lock_key, self._lock_owner, nx=True, ex=self._lock_ttl)
            return bool(ok)
        except Exception as e:
            logger.error(f"❌ 분산 락 획득 실패: {str(e)}")
            return False

    def _refresh_lock(self) -> bool:
        try:
            val = redis_client.get(self._lock_key)
            if val == self._lock_owner:
                redis_client.expire(self._lock_key, self._lock_ttl)
                return True
            return False
        except Exception as e:
            logger.error(f"❌ 분산 락 갱신 실패: {str(e)}")
            return False

    def _release_lock(self):
        try:
            val = redis_client.get(self._lock_key)
            if val == self._lock_owner:
                redis_client.delete(self._lock_key)
        except Exception as e:
            logger.error(f"❌ 분산 락 해제 실패: {str(e)}")

    def _start_auto_cleanup(self):
        self._is_leader = self._acquire_lock()
        if not self._is_leader:
            logger.info("ℹ️ 다른 워커가 자동 정리를 담당 중")
            return
        self._auto_cleanup_thread = threading.Thread(
            target=self._auto_cleanup_worker, daemon=True, name="AutoCleanupWorker"
        )
        self._auto_cleanup_thread.start()
        logger.info(
            f"🔄 자동 정리 스레드 시작 (간격: {self.auto_cleanup_interval}초, 최대 보존: {self.max_file_age_seconds}초)"
        )

    def _auto_cleanup_worker(self):
        while not self._stop_auto_cleanup.is_set():
            try:
                if self._stop_auto_cleanup.wait(self.auto_cleanup_interval):
                    break
                if not self._refresh_lock():
                    if self._acquire_lock():
                        self._is_leader = True
                    else:
                        self._is_leader = False
                if not self._is_leader:
                    continue
                logger.info(f"🧹 자동 정리 실행 중... (최대 보존: {self.max_file_age_seconds}초)")
                cleanup_old_files(self.temp_dir, self.max_file_age_seconds)
                logger.info("✅ 자동 정리 완료")
            except Exception as e:
                logger.error(f"❌ 자동 정리 중 오류 발생: {str(e)}")
                time.sleep(60)

    def stop_auto_cleanup(self):
        self._stop_auto_cleanup.set()
        if self._auto_cleanup_thread and self._auto_cleanup_thread.is_alive():
            self._auto_cleanup_thread.join(timeout=5)
            logger.info("🛑 자동 정리 스레드 중지됨")
        if self._is_leader:
            self._release_lock()

    def cleanup_temp_directory(self):
        with self._cleanup_lock:
            if self._cleanup_done:
                return
            self._cleanup_done = True
        try:
            if os.path.exists(self.temp_dir):
                logger.info(f"🧹 TEMP_DIR 정리 중: {self.temp_dir}")
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        for root, dirs, files in os.walk(self.temp_dir, topdown=False):
                            for file in files:
                                file_path = os.path.join(root, file)
                                try:
                                    os.chmod(file_path, 0o777)
                                    os.remove(file_path)
                                except Exception as e:
                                    logger.warning(f"⚠️ 파일 삭제 실패: {file_path} - {str(e)}")
                        break
                    except Exception as e:
                        if attempt < max_retries - 1:
                            logger.warning(f"⚠️ TEMP_DIR 정리 재시도 {attempt + 1}/{max_retries}: {str(e)}")
                            time.sleep(1)
                        else:
                            raise e
            else:
                logger.info("ℹ️ TEMP_DIR이 존재하지 않습니다")
        except Exception as e:
            logger.error(f"❌ TEMP_DIR 정리 실패: {str(e)}")

    def _signal_handler(self, signum, frame):
        signal_name = {
            signal.SIGTERM: "SIGTERM",
            signal.SIGINT: "SIGINT",
            signal.SIGQUIT: "SIGQUIT",
            signal.SIGHUP: "SIGHUP",
        }.get(signum, f"Signal {signum}")
        logger.info(f"🛑 서비스 종료 신호 수신: {signal_name}")
        self.stop_auto_cleanup()
        self.cleanup_temp_directory()
        sys.exit(0)

    def _atexit_handler(self):
        logger.info("🔄 프로그램 종료 시 정리 실행")
        self.cleanup_temp_directory()
        if self._is_leader:
            self._release_lock()

    def manual_cleanup(self):
        logger.info("🔧 수동 정리 실행")
        self.cleanup_temp_directory()

    def manual_cleanup_old_files(self):
        logger.info(f"🔧 수동 오래된 파일 정리 실행 (최대 보존: {self.max_file_age_seconds}초)")
        cleanup_old_files(self.temp_dir, self.max_file_age_seconds)


_cleanup_handler: Optional[CleanupHandler] = None


def initialize_cleanup_handler(
    temp_dir: str, auto_cleanup_interval: int = 60 * 5, max_file_age_seconds: int = 60 * 20
) -> CleanupHandler:
    global _cleanup_handler
    _cleanup_handler = CleanupHandler(temp_dir, auto_cleanup_interval, max_file_age_seconds)
    return _cleanup_handler


def get_cleanup_handler() -> Optional[CleanupHandler]:
    return _cleanup_handler


def manual_cleanup():
    if _cleanup_handler:
        _cleanup_handler.manual_cleanup()
    else:
        logger.warning("⚠️ CleanupHandler가 초기화되지 않았습니다")


def manual_cleanup_old_files():
    if _cleanup_handler:
        _cleanup_handler.manual_cleanup_old_files()
    else:
        logger.warning("⚠️ CleanupHandler가 초기화되지 않았습니다")
