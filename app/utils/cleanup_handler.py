import os
import shutil
import signal
import sys
import atexit
import threading
import logging
import time
from typing import Optional
from app.utils.os_processor import cleanup_old_files

logger = logging.getLogger(__name__)


class CleanupHandler:
    """서비스 종료 시 리소스 정리를 담당하는 클래스"""

    def __init__(self, temp_dir: str, auto_cleanup_interval: int = 3600, max_file_age_hours: int = 1):
        self.temp_dir = temp_dir
        self.auto_cleanup_interval = auto_cleanup_interval  # 자동 정리 간격 (초)
        self.max_file_age_hours = max_file_age_hours  # 최대 파일 보존 시간 (시간)
        self._cleanup_done = False
        self._cleanup_lock = threading.Lock()
        self._auto_cleanup_thread = None
        self._stop_auto_cleanup = threading.Event()
        self._setup_handlers()
        self._start_auto_cleanup()

    def _setup_handlers(self):
        """시그널 핸들러와 atexit 핸들러를 설정"""
        # 시그널 핸들러 등록
        signal.signal(signal.SIGTERM, self._signal_handler)  # Docker stop, kill 등
        signal.signal(signal.SIGINT, self._signal_handler)  # Ctrl+C
        signal.signal(signal.SIGQUIT, self._signal_handler)  # Ctrl+\
        signal.signal(signal.SIGHUP, self._signal_handler)  # 터미널 종료

        # atexit 핸들러 등록
        atexit.register(self._atexit_handler)

        logger.info("🧹 CleanupHandler 초기화 완료")

    def _start_auto_cleanup(self):
        self._auto_cleanup_thread = threading.Thread(
            target=self._auto_cleanup_worker, daemon=True, name="AutoCleanupWorker"
        )
        self._auto_cleanup_thread.start()
        logger.info(
            f"🔄 자동 정리 스레드 시작 (간격: {self.auto_cleanup_interval}초, 최대 보존: {self.max_file_age_hours}시간)"
        )

    def _auto_cleanup_worker(self):
        while not self._stop_auto_cleanup.is_set():
            try:
                if self._stop_auto_cleanup.wait(self.auto_cleanup_interval):
                    break

                logger.info(f"🧹 자동 정리 실행 중... (최대 보존: {self.max_file_age_hours}시간)")
                cleanup_old_files(self.temp_dir, self.max_file_age_hours)
                logger.info("✅ 자동 정리 완료")

            except Exception as e:
                logger.error(f"❌ 자동 정리 중 오류 발생: {str(e)}")
                time.sleep(60)

    def stop_auto_cleanup(self):
        self._stop_auto_cleanup.set()
        if self._auto_cleanup_thread and self._auto_cleanup_thread.is_alive():
            self._auto_cleanup_thread.join(timeout=5)
            logger.info("🛑 자동 정리 스레드 중지됨")

    def cleanup_temp_directory(self):
        """TEMP_DIR의 모든 파일과 디렉토리를 정리 (폴더 자체는 유지)"""
        with self._cleanup_lock:
            if self._cleanup_done:
                return
            self._cleanup_done = True

        try:
            if os.path.exists(self.temp_dir):
                logger.info(f"🧹 TEMP_DIR 정리 중: {self.temp_dir}")

                # 파일 권한 문제 해결을 위한 재시도 로직
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        # temp_dir 내부의 모든 항목을 삭제하되, temp_dir 자체는 유지
                        for item in os.listdir(self.temp_dir):
                            item_path = os.path.join(self.temp_dir, item)

                            # 읽기 전용 파일들도 삭제할 수 있도록 권한 변경
                            if os.path.isfile(item_path):
                                try:
                                    os.chmod(item_path, 0o777)
                                    os.remove(item_path)
                                except Exception as e:
                                    logger.warning(f"⚠️ 파일 삭제 실패: {item_path} - {str(e)}")
                            elif os.path.isdir(item_path):
                                # 디렉토리 내부의 모든 파일에 대해 권한 변경
                                for root, dirs, files in os.walk(item_path, topdown=False):
                                    for file in files:
                                        file_path = os.path.join(root, file)
                                        try:
                                            os.chmod(file_path, 0o777)
                                        except:
                                            pass
                                    for dir in dirs:
                                        dir_path = os.path.join(root, dir)
                                        try:
                                            os.chmod(dir_path, 0o777)
                                        except:
                                            pass

                                shutil.rmtree(item_path, ignore_errors=True)

                        logger.info("✅ TEMP_DIR 정리 완료 (폴더 유지)")
                        break
                    except Exception as e:
                        if attempt < max_retries - 1:
                            logger.warning(f"⚠️ TEMP_DIR 정리 재시도 {attempt + 1}/{max_retries}: {str(e)}")
                            import time

                            time.sleep(1)
                        else:
                            raise e
            else:
                logger.info("ℹ️ TEMP_DIR이 존재하지 않습니다")
        except Exception as e:
            logger.error(f"❌ TEMP_DIR 정리 실패: {str(e)}")

    def _signal_handler(self, signum, frame):
        """시그널 핸들러 - 서비스 종료 시 정리"""
        signal_name = {
            signal.SIGTERM: "SIGTERM",
            signal.SIGINT: "SIGINT",
            signal.SIGQUIT: "SIGQUIT",
            signal.SIGHUP: "SIGHUP",
        }.get(signum, f"Signal {signum}")

        logger.info(f"🛑 서비스 종료 신호 수신: {signal_name}")
        self.stop_auto_cleanup()  # 자동 정리 스레드 중지
        self.cleanup_temp_directory()
        sys.exit(0)

    def _atexit_handler(self):
        """프로그램 종료 시 정리 (atexit를 통한 안전한 종료)"""
        logger.info("🔄 프로그램 종료 시 정리 실행")
        self.cleanup_temp_directory()

    def manual_cleanup(self):
        """수동으로 정리 실행 (테스트나 디버깅용)"""
        logger.info("🔧 수동 정리 실행")
        self.cleanup_temp_directory()

    def manual_cleanup_old_files(self):
        logger.info(f"🔧 수동 오래된 파일 정리 실행 (최대 보존: {self.max_file_age_hours}시간)")
        cleanup_old_files(self.temp_dir, self.max_file_age_hours)


# 전역 인스턴스 (필요시 사용)
_cleanup_handler: Optional[CleanupHandler] = None


def initialize_cleanup_handler(
    temp_dir: str, auto_cleanup_interval: int = 3600, max_file_age_hours: int = 24
) -> CleanupHandler:
    global _cleanup_handler
    _cleanup_handler = CleanupHandler(temp_dir, auto_cleanup_interval, max_file_age_hours)
    return _cleanup_handler


def get_cleanup_handler() -> Optional[CleanupHandler]:
    """전역 CleanupHandler 인스턴스를 반환"""
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
