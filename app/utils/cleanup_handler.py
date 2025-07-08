import os
import shutil
import signal
import sys
import atexit
import threading
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class CleanupHandler:
    """서비스 종료 시 리소스 정리를 담당하는 클래스"""

    def __init__(self, temp_dir: str):
        self.temp_dir = temp_dir
        self._cleanup_done = False
        self._cleanup_lock = threading.Lock()
        self._setup_handlers()

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

    def cleanup_temp_directory(self):
        """TEMP_DIR의 모든 파일과 디렉토리를 정리"""
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
                        # 읽기 전용 파일들도 삭제할 수 있도록 권한 변경
                        for root, dirs, files in os.walk(self.temp_dir, topdown=False):
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

                        shutil.rmtree(self.temp_dir, ignore_errors=True)
                        logger.info("✅ TEMP_DIR 정리 완료")
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


# 전역 인스턴스 (필요시 사용)
_cleanup_handler: Optional[CleanupHandler] = None


def initialize_cleanup_handler(temp_dir: str) -> CleanupHandler:
    """CleanupHandler를 초기화하고 반환"""
    global _cleanup_handler
    _cleanup_handler = CleanupHandler(temp_dir)
    return _cleanup_handler


def get_cleanup_handler() -> Optional[CleanupHandler]:
    """전역 CleanupHandler 인스턴스를 반환"""
    return _cleanup_handler


def manual_cleanup():
    """전역 인스턴스를 통한 수동 정리"""
    if _cleanup_handler:
        _cleanup_handler.manual_cleanup()
    else:
        logger.warning("⚠️ CleanupHandler가 초기화되지 않았습니다")
