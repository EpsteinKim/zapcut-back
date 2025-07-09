import os
import asyncio
import logging
import uuid
from typing import List
from io import BytesIO
from PIL import Image
import numpy as np
import mimetypes

from app.models.schemas import ShortsVideoRequest, SceneWithData, BGMType
from app.core.service_locator import get_google_ai_service
from app.utils.ffmpeg_processor import FFmpegProcessor
from app.utils.io_processor import IOProcessor
from app.exceptions.http_exceptions import ServerException
from app.core.config import TEMP_DIR
from app.utils.os_processor import get_temp_dir


class VideoServiceFFmpeg:
    def __init__(self):
        self.video_width = 1080
        self.video_height = 1920
        self.temp_dir = get_temp_dir("video_ffmpeg")
        self.ffmpeg_processor = FFmpegProcessor(self.video_width, self.video_height)
        self.io_processor = IOProcessor()

    def _is_gif_file(self, file_path: str) -> bool:
        """GIF 파일인지 확인"""
        if file_path.lower().endswith(".gif"):
            return True

        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type == "image/gif":
            return True

        try:
            with open(file_path, "rb") as f:
                header = f.read(6)
                return header.startswith(b"GIF87a") or header.startswith(b"GIF89a")
        except:
            return False

    async def _process_scene_media_with_retry(self, scene, google_ai_service, max_retries=3):
        """재시도 로직이 포함된 미디어 처리"""
        for attempt in range(max_retries):
            try:
                if scene.video_url is not None:
                    video_path = await self.io_processor.download_file(scene.video_url)
                    processed_video = await self.ffmpeg_processor.resize_and_position_video(video_path, scene.duration)
                    return processed_video, None

                elif scene.image_url is not None:
                    image_path = await self.io_processor.download_file(scene.image_url)

                    if self._is_gif_file(image_path):
                        # GIF를 비디오로 변환
                        processed_video = await self.ffmpeg_processor.resize_and_position_video(
                            image_path, scene.duration
                        )
                        return processed_video, None
                    else:
                        # 일반 이미지를 비디오로 변환
                        processed_video = await self.ffmpeg_processor.image_to_video(image_path, scene.duration)
                        return processed_video, None

                else:
                    # AI 이미지 생성
                    (upload_url, image_buffer) = await google_ai_service.generate_shorts_image(scene.description)

                    # 이미지를 임시 파일로 저장
                    pil_image = Image.open(image_buffer)
                    if pil_image.mode != "RGB":
                        pil_image = pil_image.convert("RGB")

                    temp_image_path = os.path.join(self.temp_dir, f"ai_image_{uuid.uuid4()}.jpg")
                    pil_image.save(temp_image_path, "JPEG")

                    # 이미지를 비디오로 변환
                    processed_video = await self.ffmpeg_processor.image_to_video(temp_image_path, scene.duration)
                    return processed_video, upload_url
            except Exception as e:
                logging.warning(f"Scene media processing attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    logging.error(f"All attempts failed for scene media, using fallback. Error: {str(e)}")
                    raise ServerException(f"Scene media processing failed: {str(e)}")
                await asyncio.sleep(1 * (attempt + 1))

    async def _prepare_background_music(self, request: ShortsVideoRequest, total_duration: float) -> str:
        """배경 음악 준비 - 개선된 버전"""
        if request.bgm_id == BGMType.CUSTOM and request.custom_bgm_url:
            music_path = await self.io_processor.download_file(request.custom_bgm_url)
        elif request.bgm_id != BGMType.NONE:
            music_path = BGMType.get_file_path(request.bgm_id)
        else:
            return None

        if not music_path or not os.path.exists(music_path):
            return None

        # 배경음악을 전체 길이에 맞게 반복하고 볼륨 조정
        adjusted_music_path = os.path.join(self.temp_dir, f"bgm_{uuid.uuid4()}.aac")

        cmd = [
            "ffmpeg",
            "-y",
            "-stream_loop",
            "-1",  # 무한 반복
            "-i",
            music_path,
            "-t",
            str(total_duration),  # 총 길이로 자르기
            "-af",
            f"volume={request.music_volume}",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-ar",
            "48000",
            adjusted_music_path,
        ]

        result = await self.ffmpeg_processor._run_ffmpeg_command(cmd)
        if result.returncode != 0:
            logging.warning(f"배경음악 처리 실패: {result.stderr}")
            return None

        return adjusted_music_path

    async def _add_text_overlays_to_video(self, video_path: str, scenes: List[SceneWithData]) -> str:
        """비디오에 텍스트 오버레이 추가"""
        current_video = video_path
        current_time = 0

        for scene in scenes:
            if scene.captions:
                for caption in scene.captions:
                    # 텍스트 이스케이프 처리
                    escaped_text = caption.text.replace("'", "\\'").replace(":", "\\:")

                    # 애니메이션 효과가 있는 텍스트 오버레이 추가
                    new_video = await self.ffmpeg_processor.add_text_overlay_with_animation(
                        current_video,
                        escaped_text,
                        current_time + caption.start_time,
                        caption.end_time - caption.start_time,
                        animation_effect=caption.animation_effect or "NONE",
                        font_size=120,  # 더 큰 폰트 크기로 굵게 보이게
                        font_color=caption.color or "white",
                        stroke_color="black",
                        stroke_width=10,  # 테두리는 얇게, 폰트는 굵게
                    )

                    # 이전 비디오 파일 정리 (원본 제외)
                    if current_video != video_path:
                        try:
                            os.remove(current_video)
                        except:
                            pass

                    current_video = new_video

            current_time += scene.duration

        return current_video

    async def _collect_scene_audio(self, scenes: List[SceneWithData]) -> List[str]:
        """씬별 오디오 수집 - 개선된 버전"""
        audio_files = []
        current_time = 0

        for scene in scenes:
            # 음성 파일 처리
            if scene.voice_url:
                try:
                    voice_path = await self.io_processor.download_file(scene.voice_url)

                    # 음성 파일을 올바른 시간에 배치 - offset 사용
                    adjusted_voice_path = os.path.join(self.temp_dir, f"voice_{uuid.uuid4()}.aac")

                    # 무음 패딩과 함께 오디오 배치
                    cmd = [
                        "ffmpeg",
                        "-y",
                        "-f",
                        "lavfi",
                        "-i",
                        f"anullsrc=channel_layout=stereo:sample_rate=48000:duration={current_time}",  # 앞쪽 무음
                        "-i",
                        voice_path,
                        "-f",
                        "lavfi",
                        "-i",
                        f"anullsrc=channel_layout=stereo:sample_rate=48000:duration=1",  # 뒤쪽 무음 (1초)
                        "-filter_complex",
                        f"[0:a][1:a][2:a]concat=n=3:v=0:a=1[out]",
                        "-map",
                        "[out]",
                        "-c:a",
                        "aac",
                        "-b:a",
                        "128k",
                        "-t",
                        str(current_time + scene.duration + 1),  # 전체 길이 설정
                        adjusted_voice_path,
                    ]

                    result = await self.ffmpeg_processor._run_ffmpeg_command(cmd)
                    if result.returncode == 0:
                        audio_files.append(adjusted_voice_path)
                    else:
                        logging.warning(f"음성 처리 실패: {result.stderr}")
                except Exception as e:
                    logging.warning(f"음성 처리 실패: {str(e)}")

            current_time += scene.duration

        return audio_files

    async def create_video(self, request: ShortsVideoRequest) -> str:
        """FFmpeg를 사용한 비디오 생성"""
        logging.info(f"create_video: {request}")
        google_ai_service = get_google_ai_service()
        total_duration = sum(scene.duration for scene in request.scenes)

        # 1. 모든 씬의 미디어 병렬 처리
        media_tasks = [self._process_scene_media_with_retry(scene, google_ai_service) for scene in request.scenes]

        try:
            media_results = await asyncio.gather(*media_tasks, return_exceptions=True)
        except Exception as e:
            logging.error(f"Critical error in parallel processing: {str(e)}")
            raise ServerException(f"비디오 처리 중 치명적 오류가 발생했습니다: {str(e)}")

        # 2. 처리된 비디오 클립들 수집
        video_clips = []
        for i, result in enumerate(media_results):
            if isinstance(result, Exception):
                logging.error(f"Media processing failed for scene {i}: {str(result)}")
                # 폴백 처리는 _process_scene_media_with_retry에서 이미 처리됨
                continue

            video_path, upload_url = result
            video_clips.append(video_path)

        # 3. 비디오 클립들 연결
        if not video_clips:
            raise ServerException("처리된 비디오 클립이 없습니다.")

        concatenated_video = await self.ffmpeg_processor.concatenate_videos(video_clips)

        # 4. 텍스트 오버레이 추가
        video_with_text = await self._add_text_overlays_to_video(concatenated_video, request.scenes)

        # 5. 오디오 처리 - 개선된 버전
        audio_files = []
        audio_volumes = []

        # 배경음악 추가
        bgm_path = await self._prepare_background_music(request, total_duration)
        if bgm_path:
            audio_files.append(bgm_path)
            audio_volumes.append(0.3)  # 배경음악 볼륨 (30%)
            logging.warning(f"배경음악 추가됨: {bgm_path}")

        # 씬별 오디오 수집
        scene_audio_files = await self._collect_scene_audio(request.scenes)
        audio_files.extend(scene_audio_files)
        # 음성은 100% 볼륨
        audio_volumes.extend([1.0] * len(scene_audio_files))
        logging.warning(f"음성 파일 {len(scene_audio_files)}개 추가됨: {scene_audio_files}")

        # 6. 최종 비디오에 오디오 추가
        if audio_files:
            logging.warning(f"총 오디오 파일: {len(audio_files)}개, 볼륨: {audio_volumes}")
            final_video = await self.ffmpeg_processor.add_audio(video_with_text, audio_files, audio_volumes)
        else:
            # 오디오가 없는 경우 원본 비디오 사용
            logging.warning("오디오 파일이 없음 - 무음 비디오 생성")
            final_video = video_with_text

        # 7. 최종 비디오 파일 읽기 및 업로드
        with open(final_video, "rb") as f:
            video_bytes = f.read()
        video_buffer = BytesIO(video_bytes)

        try:
            download_url = await self.io_processor.upload_file_s3(file_data=video_buffer, ext="mp4")
            return download_url
        except Exception as e:
            raise ServerException(f"파일 업로드 실패: {str(e)}")
        finally:
            # 임시 파일 정리
            self.ffmpeg_processor.cleanup()
