import subprocess
import os
import uuid
import asyncio
from typing import List, Optional
from app.exceptions.http_exceptions import ServerException
import logging
from app.utils.os_processor import get_temp_dir

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FFmpegProcessor:
    def __init__(self, video_width: int = 1080, video_height: int = 1920):
        self.video_width = video_width
        self.video_height = video_height
        self.temp_dir = get_temp_dir("ffmpeg_processor")

    async def create_background_video(self, duration: float, color: str = "black") -> str:
        """단색 배경 비디오 생성"""
        output_path = os.path.join(self.temp_dir, f"background_{uuid.uuid4()}.mp4")

        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c={color}:size={self.video_width}x{self.video_height}:duration={duration}:rate=24",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            output_path,
        ]

        result = await self._run_ffmpeg_command(cmd)
        if result.returncode != 0:
            raise ServerException(f"배경 비디오 생성 실패: {result.stderr}")

        return output_path

    async def resize_and_position_video(self, input_path: str, duration: float, start_time: float = 0) -> str:
        """비디오 리사이즈 및 위치 조정"""
        output_path = os.path.join(self.temp_dir, f"resized_{uuid.uuid4()}.mp4")

        # 비디오 정보 가져오기
        probe_cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", input_path]
        probe_result = await self._run_ffmpeg_command(probe_cmd)

        # 리사이즈 및 위치 조정
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            input_path,
            "-vf",
            f"scale='min({self.video_width},iw)':'min({self.video_height},ih)':force_original_aspect_ratio=decrease,pad={self.video_width}:{self.video_height}:(ow-iw)/2:(oh-ih)/2:black",
            "-t",
            str(duration),
            "-ss",
            str(start_time),
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            "-pix_fmt",
            "yuv420p",
            output_path,
        ]

        result = await self._run_ffmpeg_command(cmd)
        if result.returncode != 0:
            raise ServerException(f"비디오 리사이즈 실패: {result.stderr}")

        return output_path

    async def image_to_video(self, image_path: str, duration: float) -> str:
        """이미지를 비디오로 변환"""
        output_path = os.path.join(self.temp_dir, f"image_video_{uuid.uuid4()}.mp4")

        cmd = [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            image_path,
            "-vf",
            f"scale='min({self.video_width},iw)':'min({self.video_height},ih)':force_original_aspect_ratio=decrease,pad={self.video_width}:{self.video_height}:(ow-iw)/2:(oh-ih)/2:black",
            "-t",
            str(duration),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-r",
            "24",
            output_path,
        ]

        result = await self._run_ffmpeg_command(cmd)
        if result.returncode != 0:
            raise ServerException(f"이미지 비디오 변환 실패: {result.stderr}")

        return output_path

    async def add_text_overlay(
        self,
        video_path: str,
        text: str,
        start_time: float,
        duration: float,
        font_size: int = 100,
        font_color: str = "white",
        stroke_color: str = "black",
        stroke_width: int = 3,
    ) -> str:
        """비디오에 텍스트 오버레이 추가"""
        output_path = os.path.join(self.temp_dir, f"text_overlay_{uuid.uuid4()}.mp4")

        # 텍스트 필터 설정
        text_filter = (
            f"drawtext=text='{text}':fontfile=/app/app/assets/fonts/Jua-Regular.ttf:"
            f"fontsize={font_size}:fontcolor={font_color}:"
            f"borderw={stroke_width}:bordercolor={stroke_color}:"
            f"x=(w-text_w)/2:y=(h-text_h)/2:"
            f"enable='between(t,{start_time},{start_time + duration})'"
        )

        cmd = ["ffmpeg", "-y", "-i", video_path, "-vf", text_filter, "-c:a", "copy", "-c:v", "libx264", output_path]

        result = await self._run_ffmpeg_command(cmd)
        if result.returncode != 0:
            raise ServerException(f"텍스트 오버레이 실패: {result.stderr}")

        return output_path

    async def concatenate_videos(self, video_paths: List[str]) -> str:
        """여러 비디오 연결"""
        if not video_paths:
            raise ServerException("연결할 비디오가 없습니다.")

        if len(video_paths) == 1:
            return video_paths[0]

        # concat 파일 생성
        concat_file = os.path.join(self.temp_dir, f"concat_{uuid.uuid4()}.txt")
        with open(concat_file, "w") as f:
            for video_path in video_paths:
                f.write(f"file '{video_path}'\n")

        output_path = os.path.join(self.temp_dir, f"concatenated_{uuid.uuid4()}.mp4")

        cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file, "-c", "copy", output_path]

        result = await self._run_ffmpeg_command(cmd)
        if result.returncode != 0:
            raise ServerException(f"비디오 연결 실패: {result.stderr}")

        return output_path

    async def add_audio(
        self, video_path: str, audio_paths: List[str], audio_volumes: Optional[List[float]] = None
    ) -> str:
        """비디오에 오디오 추가"""
        if not audio_paths:
            return video_path

        output_path = os.path.join(self.temp_dir, f"with_audio_{uuid.uuid4()}.mp4")

        # 입력 파일들 설정
        inputs = ["-i", video_path]
        for audio_path in audio_paths:
            inputs.extend(["-i", audio_path])

        # 오디오 믹싱 필터 생성
        if len(audio_paths) == 1:
            audio_filter = "[1:a]"
            if audio_volumes and len(audio_volumes) > 0:
                audio_filter = f"[1:a]volume={audio_volumes[0]}[a]"
                audio_map = "[a]"
            else:
                audio_map = "[1:a]"
        else:
            # 여러 오디오 믹싱
            mix_inputs = []
            for i, audio_path in enumerate(audio_paths):
                volume = audio_volumes[i] if audio_volumes and i < len(audio_volumes) else 1.0
                mix_inputs.append(f"[{i+1}:a]volume={volume}[a{i}]")

            mix_filter = "".join(mix_inputs)
            mix_filter += "".join([f"[a{i}]" for i in range(len(audio_paths))])
            mix_filter += f"amix=inputs={len(audio_paths)}[a]"
            audio_map = "[a]"
            audio_filter = mix_filter

        cmd = (
            ["ffmpeg", "-y"]
            + inputs
            + [
                "-filter_complex",
                audio_filter,
                "-map",
                "0:v",
                "-map",
                audio_map,
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-shortest",
                output_path,
            ]
        )

        result = await self._run_ffmpeg_command(cmd)
        if result.returncode != 0:
            raise ServerException(f"오디오 추가 실패: {result.stderr}")

        return output_path

    async def _run_ffmpeg_command(self, cmd: List[str]) -> subprocess.CompletedProcess:
        """FFmpeg 명령어 실행"""
        try:
            result = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()

            return subprocess.CompletedProcess(
                args=cmd, returncode=result.returncode, stdout=stdout.decode(), stderr=stderr.decode()
            )
        except Exception as e:
            raise ServerException(f"FFmpeg 실행 실패: {str(e)}")

    def cleanup(self):
        """임시 파일 정리"""
        if hasattr(self, "temp_dir") and os.path.exists(self.temp_dir):
            import shutil

            shutil.rmtree(self.temp_dir)

    def __del__(self):
        self.cleanup()
