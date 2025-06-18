from moviepy import (
    VideoFileClip,
    CompositeVideoClip,
    TextClip,
    AudioFileClip,
    AudioArrayClip,
    concatenate_videoclips,
    concatenate_audioclips,
    CompositeAudioClip,
    ImageClip,
)
from moviepy.audio import fx as afx
from typing import List, Optional, Tuple
from app.models.schemas import SceneRequest, ShortsSceneRequest, CombineShortsSceneRequest, ShortsVideoRequest
from app.core.service_locator import get_google_ai_service
from app.utils.video_processor import VideoProcessor
from app.utils.audio_processor import AudioProcessor
from app.utils.text_processor import TextProcessor
from app.utils.io_processor import IOProcessor
import tempfile
import os
import shutil
import uuid
from app.exceptions.http_exceptions import ServerException
from dataclasses import dataclass
from io import BytesIO
from PIL import Image
import numpy as np
import mimetypes


@dataclass
class Processors:
    video: VideoProcessor
    audio: AudioProcessor
    text: TextProcessor
    IO: IOProcessor


class VideoService:
    def __init__(self):
        self.video_width = 1080
        self.video_height = 1920
        self.temp_dir = tempfile.mkdtemp()
        self.processors = Processors(
            video=VideoProcessor(self.video_width, self.video_height),
            audio=AudioProcessor(),
            text=TextProcessor(self.video_width, self.video_height),
            IO=IOProcessor(),
        )

    def _is_gif_file(self, file_path: str) -> bool:
        """GIF 파일인지 확인"""
        # 확장자로 먼저 확인
        if file_path.lower().endswith(".gif"):
            return True

        # MIME 타입으로 확인
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type == "image/gif":
            return True

        # 파일 헤더로 확인
        try:
            with open(file_path, "rb") as f:
                header = f.read(6)
                return header.startswith(b"GIF87a") or header.startswith(b"GIF89a")
        except:
            return False

    def _process_gif_file(self, gif_path: str, duration: float) -> ImageClip:
        """GIF 파일을 처리하여 애니메이션을 유지"""
        try:
            # PIL로 GIF 정보 확인
            with Image.open(gif_path) as gif_image:
                # GIF가 애니메이션인지 확인
                is_animated = getattr(gif_image, "is_animated", False)

                if is_animated:
                    # 애니메이션 GIF인 경우 MoviePy의 VideoFileClip으로 처리
                    # GIF를 비디오로 취급하여 애니메이션 유지
                    try:
                        gif_clip = VideoFileClip(gif_path)
                        # GIF의 원본 길이가 씬 길이보다 짧으면 반복
                        if gif_clip.duration < duration:
                            # 필요한 반복 횟수 계산
                            loops_needed = int(np.ceil(duration / gif_clip.duration))
                            gif_clip = gif_clip.loop(loops_needed)
                        return gif_clip.with_duration(duration)
                    except Exception as e:
                        print(f"GIF를 비디오로 처리하는 중 오류: {e}")
                        # 실패 시 정적 이미지로 처리
                        return self._process_static_gif(gif_image, duration)
                else:
                    # 정적 GIF인 경우
                    return self._process_static_gif(gif_image, duration)

        except Exception as e:
            print(f"GIF 처리 중 오류: {e}")
            # 오류 발생 시 기본 이미지 처리
            pil_image = Image.open(gif_path)
            if pil_image.mode != "RGB":
                pil_image = pil_image.convert("RGB")
            image_array = np.array(pil_image)
            return ImageClip(image_array, duration=duration)

    def _process_static_gif(self, gif_image: Image.Image, duration: float) -> ImageClip:
        """정적 GIF 또는 첫 번째 프레임 처리"""
        if gif_image.mode != "RGB":
            gif_image = gif_image.convert("RGB")
        image_array = np.array(gif_image)
        return ImageClip(image_array, duration=duration)

    async def create_video(self, request: ShortsVideoRequest) -> str:
        google_ai_service = get_google_ai_service()
        video_clips = []
        text_clips = []
        audio_clips = []
        total_duration = sum(scene.duration for scene in request.scenes)
        background = self.processors.video.create_background(total_duration)
        video_clips.append(background)

        if request.background_music_url:
            music_path = await self.processors.IO.download_file(request.background_music_url)
            background_music = (
                AudioFileClip(music_path).with_effects([afx.MultiplyVolume(0.5)]).with_duration(total_duration)
            )
            audio_clips.append(background_music)

        current_time = 0  # 합성 비디오를 만들긴 위한 누적 시간
        used_image_urls = []
        for scene in request.scenes:
            if scene.video_url is not None:
                video_path = await self.processors.IO.download_file(scene.video_url)
                target_clip = VideoFileClip(video_path)
            elif scene.image_url is not None:
                image_path = await self.processors.IO.download_file(scene.image_url)

                # GIF 파일인지 확인하고 적절히 처리
                if self._is_gif_file(image_path):
                    target_clip = self._process_gif_file(image_path, scene.duration)
                else:
                    # 일반 이미지 처리
                    pil_image = Image.open(image_path)
                    if pil_image.mode != "RGB":
                        pil_image = pil_image.convert("RGB")
                    image_array = np.array(pil_image)
                    target_clip = ImageClip(image_array, duration=scene.duration)
            else:
                (upload_url, image_buffer) = await google_ai_service.generate_shorts_image(scene.description)
                pil_image = Image.open(image_buffer)
                if pil_image.mode != "RGB":
                    pil_image = pil_image.convert("RGB")
                image_array = np.array(pil_image)
                target_clip = ImageClip(image_array, duration=scene.duration)
                used_image_urls.append(upload_url)

            target_clip = (
                target_clip.with_duration(scene.duration)
                .with_start(current_time)
                .with_end(current_time + scene.duration)
            )

            clip_width, clip_height = target_clip.w, target_clip.h
            width_ratio = self.video_width / clip_width
            height_ratio = self.video_height / clip_height

            scale_ratio = min(width_ratio, height_ratio)
            new_width = int(clip_width * scale_ratio)
            new_height = int(clip_height * scale_ratio)

            x_center = (self.video_width - new_width) // 2
            y_center = (self.video_height - new_height) // 2
            target_clip = target_clip.resized(width=new_width, height=new_height).with_position((x_center, y_center))
            video_clips.append(target_clip)

            if scene.captions:
                for caption in scene.captions:
                    text_clip = self.processors.text.create_text_clip(
                        caption=caption.text,
                        start_time=current_time + caption.start_time,
                        end_time=current_time + caption.end_time,
                    )
                    text_clips.append(text_clip)

                    tts_result = google_ai_service.genereate_text_to_speech(
                        caption.text,
                        duration=caption.end_time - caption.start_time,
                        speed_multiplier=1.2,
                    )

                    audio_clip = AudioFileClip(tts_result["output_path"], fps=tts_result["fps"])
                    audio_clip = audio_clip.with_start(current_time + caption.start_time)
                    audio_clips.append(audio_clip)

            # 다음 씬을 위해 현재 씬의 duration만큼 누적
            current_time += scene.duration

        final_audio_clip = CompositeAudioClip(audio_clips)

        final_video_clip = CompositeVideoClip(video_clips + text_clips)
        final_video_clip = final_video_clip.with_audio(final_audio_clip).with_duration(total_duration)
        print(final_video_clip.duration)
        output_path = os.path.join(self.temp_dir, f"shorts_video_{uuid.uuid4()}.mp4")
        self.processors.video.save_video(final_video_clip, output_path)

        with open(output_path, "rb") as f:
            video_bytes = f.read()
        video_buffer = BytesIO(video_bytes)

        try:
            download_url = await self.processors.IO.upload_file_s3(1, video_buffer, "mp4")

            for clip in video_clips:
                clip.close()
            for clip in text_clips:
                clip.close()
            for clip in audio_clips:
                clip.close()

            final_video_clip.close()
            final_audio_clip.close()
            background.close()

            return download_url
        except Exception as e:
            raise ServerException(f"파일 업로드 실패: {str(e)}")

    async def create_shorts_scene(self, request: ShortsSceneRequest) -> str:
        tts_service = get_tts_service()
        video_clips = []
        text_clips = []
        audio_clips = []

        total_duration = max(caption.end_time for caption in request.captions)
        background = self.processors.video.create_background(total_duration)
        video_clips.append(background)

        # 비디오나 이미지가 모두 없으면 검은 배경만 사용 (자막만 표시)
        if request.video_url is not None or request.image_url is not None:
            target_path = await self.processors.IO.download_file(
                request.video_url if request.video_url is not None else request.image_url
            )

            # 이미지 파일인지 비디오 파일인지 확인
            if request.image_url is not None:
                # 이미지 파일인 경우 PIL로 처리
                pil_image = Image.open(target_path)
                if pil_image.mode != "RGB":
                    pil_image = pil_image.convert("RGB")
                image_array = np.array(pil_image)
                target_clip = ImageClip(image_array)
            else:
                # 비디오 파일인 경우
                target_clip = VideoFileClip(target_path)

            clip_width, clip_height = target_clip.w, target_clip.h
            width_ratio = self.video_width / clip_width
            height_ratio = self.video_height / clip_height

            scale_ratio = min(width_ratio, height_ratio)
            new_width = int(clip_width * scale_ratio)
            new_height = int(clip_height * scale_ratio)

            x_center = (self.video_width - new_width) // 2
            y_center = (self.video_height - new_height) // 2
            target_clip = target_clip.resized(width=new_width, height=new_height).with_position((x_center, y_center))

            target_clip = target_clip.with_duration(total_duration)
            video_clips.append(target_clip)

        for caption in request.captions:
            text_clip = self.processors.text.create_text_clip(
                caption=caption.text, duration=caption.end_time - caption.start_time, start_time=caption.start_time
            )
            text_clips.append(text_clip)

            try:
                tts_url = await tts_service.get_download_speech_url(caption.text, caption.end_time - caption.start_time)
                tts_path = await self.processors.IO.download_file(tts_url, "mp3")
                tts_audio = AudioFileClip(tts_path)
                tts_audio = tts_audio.with_start(caption.start_time)
                audio_clips.append(tts_audio)
            except Exception as e:
                print(f"TTS 생성 실패: {str(e)}")
                continue

        all_clips = video_clips + text_clips

        final_audio = None
        if audio_clips:
            final_audio = self.processors.audio.create_final_audio(audio_clips)

        final_video = self.processors.video.create_final_video(all_clips, total_duration, final_audio)

        output_path = os.path.join(self.temp_dir, f"shorts_scene_{uuid.uuid4()}.mp4")

        self.processors.video.save_video(final_video, output_path)

        with open(output_path, "rb") as f:
            video_bytes = f.read()
        video_buffer = BytesIO(video_bytes)

        try:
            return await self.processors.IO.upload_file_s3(1, video_buffer, "mp4")
        except Exception as e:
            raise ServerException(f"파일 업로드 실패: {str(e)}")

    async def combine_video(self, request: CombineShortsSceneRequest) -> str:
        video_clips = []
        audio_clips = []

        for video_url in request.scene_urls:
            video_path = await self.processors.IO.download_file(video_url, "mp4")
            video_clip = VideoFileClip(video_path)
            audio_clips.append(video_clip.audio)
            video_clips.append(video_clip)

        final_video = concatenate_videoclips(video_clips)
        final_audio = concatenate_audioclips(audio_clips)

        total_duration = sum(clip.duration for clip in video_clips)

        audio_tracks = [final_audio]
        if request.background_music_url:
            music_path = await self.processors.IO.download_file(request.background_music_url, "mp3")
            background_music = (
                AudioFileClip(music_path)
                .with_effects([afx.MultiplyVolume(0.3)])  # 배경음악 볼륨을 30%로 낮춤
                .subclipped(0, total_duration)
            )
            audio_tracks.append(background_music)

        final_composite_audio = CompositeAudioClip(audio_tracks)
        final_video = final_video.with_audio(final_composite_audio)

        output_path = os.path.join(self.temp_dir, f"combined_shorts_{uuid.uuid4()}.mp4")

        self.processors.video.save_video(final_video, output_path)

        with open(output_path, "rb") as f:
            video_bytes = f.read()
        video_buffer = BytesIO(video_bytes)

        try:
            return await self.processors.IO.upload_file_s3(1, video_buffer, "mp4")
        except Exception as e:
            raise ServerException(f"파일 업로드 실패: {str(e)}")
        finally:
            for clip in video_clips:
                clip.close()
            final_video.close()
            if request.background_music_url:
                background_music.close()

    def __del__(self):
        if hasattr(self, "temp_dir") and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
