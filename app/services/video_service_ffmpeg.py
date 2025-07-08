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

    def __del__(self):
        auto_cleanup = os.getenv("AUTO_CLEANUP_TEMP", "true").lower() == "true"
        if auto_cleanup and hasattr(self, "temp_dir") and os.path.exists(self.temp_dir):
            import shutil

            shutil.rmtree(self.temp_dir)

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
        """배경 음악 준비"""
        if request.bgm_id == BGMType.CUSTOM and request.custom_bgm_url:
            music_path = await self.io_processor.download_file(request.custom_bgm_url)
        elif request.bgm_id != BGMType.NONE:
            music_path = BGMType.get_file_path(request.bgm_id)
        else:
            return None

        if not music_path or not os.path.exists(music_path):
            return None

        # 배경음악 길이 조정 및 볼륨 조정
        adjusted_music_path = os.path.join(self.temp_dir, f"bgm_{uuid.uuid4()}.mp3")

        import subprocess

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            music_path,
            "-t",
            str(total_duration),
            "-af",
            f"volume={request.music_volume}",
            "-c:a",
            "aac",
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

                    # 텍스트 오버레이 추가
                    new_video = await self.ffmpeg_processor.add_text_overlay(
                        current_video,
                        escaped_text,
                        current_time + caption.start_time,
                        caption.end_time - caption.start_time,
                        font_size=100,
                        font_color=caption.color or "white",
                        stroke_color="black",
                        stroke_width=3,
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
        """씬별 오디오 수집"""
        audio_files = []
        current_time = 0

        for scene in scenes:
            scene_audio_files = []

            # 음성 파일
            if scene.voice_url:
                try:
                    voice_path = await self.io_processor.download_file(scene.voice_url)

                    # 음성 파일 길이 조정
                    adjusted_voice_path = os.path.join(self.temp_dir, f"voice_{uuid.uuid4()}.mp3")
                    cmd = [
                        "ffmpeg",
                        "-y",
                        "-i",
                        voice_path,
                        "-t",
                        str(scene.duration),
                        "-af",
                        f"adelay={int(current_time * 1000)}|{int(current_time * 1000)}",
                        adjusted_voice_path,
                    ]

                    result = await self.ffmpeg_processor._run_ffmpeg_command(cmd)
                    if result.returncode == 0:
                        scene_audio_files.append(adjusted_voice_path)
                except Exception as e:
                    logging.warning(f"음성 처리 실패: {str(e)}")

            # 효과음
            if scene.captions:
                for caption in scene.captions:
                    if caption.sound_effect:
                        try:
                            effect_path = f"/app/app/assets/sounds/effect/{caption.sound_effect.lower()}.mp3"
                            if os.path.exists(effect_path):
                                # 효과음 시간 조정
                                adjusted_effect_path = os.path.join(self.temp_dir, f"effect_{uuid.uuid4()}.mp3")
                                effect_start_time = current_time + caption.start_time

                                cmd = [
                                    "ffmpeg",
                                    "-y",
                                    "-i",
                                    effect_path,
                                    "-t",
                                    "0.5",  # 효과음 길이 제한
                                    "-af",
                                    f"adelay={int(effect_start_time * 1000)}|{int(effect_start_time * 1000)},volume=0.3",
                                    adjusted_effect_path,
                                ]

                                result = await self.ffmpeg_processor._run_ffmpeg_command(cmd)
                                if result.returncode == 0:
                                    scene_audio_files.append(adjusted_effect_path)
                        except Exception as e:
                            logging.warning(f"효과음 처리 실패: {str(e)}")

            audio_files.extend(scene_audio_files)
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

        # 5. 오디오 처리
        audio_files = []

        # 배경음악 추가
        bgm_path = await self._prepare_background_music(request, total_duration)
        if bgm_path:
            audio_files.append(bgm_path)

        # 씬별 오디오 수집
        scene_audio_files = await self._collect_scene_audio(request.scenes)
        audio_files.extend(scene_audio_files)

        # 6. 최종 비디오에 오디오 추가
        if audio_files:
            # 볼륨 조정 (배경음악은 이미 조정됨)
            audio_volumes = [1.0] * len(audio_files)
            final_video = await self.ffmpeg_processor.add_audio(video_with_text, audio_files, audio_volumes)
        else:
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
