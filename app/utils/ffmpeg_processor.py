import subprocess
import os
import uuid
import asyncio
from typing import List, Optional
from app.exceptions.http_exceptions import ServerException
import logging
from app.utils.os_processor import get_temp_dir

# 로그 레벨을 WARNING으로 설정
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class FFmpegProcessor:
    def __init__(self, video_width: int = 1080, video_height: int = 1920):
        self.video_width = video_width
        self.video_height = video_height
        self.temp_dir = get_temp_dir("ffmpeg_processor")
        self.font_path = ""

    async def create_background_video(self, duration: float, color: str = "black") -> str:
        """배경 비디오 생성 - 개선된 버전"""
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
            "-preset",
            "medium",
            "-crf",
            "23",
            output_path,
        ]

        result = await self._run_ffmpeg_command(cmd)
        if result.returncode != 0:
            raise ServerException(f"배경 비디오 생성 실패: {result.stderr}")

        return output_path

    async def resize_and_position_video(self, input_path: str, duration: float, start_time: float = 0) -> str:
        """비디오 리사이징 및 위치 조정 - 기존 video_service 로직 적용"""
        output_path = os.path.join(self.temp_dir, f"resized_{uuid.uuid4()}.mp4")

        # 기존 video_service와 동일한 로직: min 비율로 축소하고 가운데 정렬
        # force_original_aspect_ratio=decrease는 min() 역할
        # pad 필터로 가운데 정렬하되 검은색 배경 사용
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            input_path,
            "-vf",
            f"scale={self.video_width}:{self.video_height}:force_original_aspect_ratio=decrease,pad={self.video_width}:{self.video_height}:(ow-iw)/2:(oh-ih)/2:black",
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
            "-preset",
            "medium",
            "-crf",
            "23",
            output_path,
        ]

        result = await self._run_ffmpeg_command(cmd)
        if result.returncode != 0:
            raise ServerException(f"비디오 리사이즈 실패: {result.stderr}")

        return output_path

    async def image_to_video(self, image_path: str, duration: float) -> str:
        """이미지를 비디오로 변환 - 기존 video_service 로직 적용"""
        output_path = os.path.join(self.temp_dir, f"image_video_{uuid.uuid4()}.mp4")

        # 기존 video_service와 동일한 로직: min 비율로 축소하고 가운데 정렬
        cmd = [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            image_path,
            "-vf",
            f"scale={self.video_width}:{self.video_height}:force_original_aspect_ratio=decrease,pad={self.video_width}:{self.video_height}:(ow-iw)/2:(oh-ih)/2:black",
            "-t",
            str(duration),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "medium",
            "-crf",
            "23",
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
        font_size: int = 120,  # 100에서 120으로 증가 (더 굵게 보이게)
        font_color: str = "white",
        stroke_color: str = "black",
        stroke_width: int = 10,  # 40에서 10으로 줄임 (테두리는 얇게)
    ) -> str:
        """비디오에 텍스트 오버레이 추가 - 폰트 자체를 굵게"""
        output_path = os.path.join(self.temp_dir, f"text_overlay_{uuid.uuid4()}.mp4")

        # 폰트를 굵게 만들기 위한 여러 방법 시도
        filter_complex = (
            f"[0:v]"
            # 약간 오프셋된 텍스트로 굵은 효과 생성
            f"drawtext=text='{text}':"
            f"fontfile='/app/app/assets/fonts/Jua-Regular.ttf':"
            f"fontsize={font_size}:"
            f"fontcolor={font_color}:"
            f"x=(w-text_w)/2+0.5:"
            f"y=(h-text_h)/2+0.5:"
            f"borderw={stroke_width}:"
            f"bordercolor={stroke_color}:"
            f"line_spacing=10:"
            f"enable='between(t,{start_time},{start_time + duration})',"
            # 원래 위치의 텍스트
            f"drawtext=text='{text}':"
            f"fontfile='/app/app/assets/fonts/Jua-Regular.ttf':"
            f"fontsize={font_size}:"
            f"fontcolor={font_color}:"
            f"x=(w-text_w)/2:"
            f"y=(h-text_h)/2:"
            f"borderw={stroke_width}:"
            f"bordercolor={stroke_color}:"
            f"line_spacing=10:"
            f"enable='between(t,{start_time},{start_time + duration})'[v]"
        )

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            video_path,
            "-filter_complex",
            filter_complex,
            "-map",
            "[v]",
            "-map",
            "0:a?",  # 오디오가 있으면 복사
            "-c:a",
            "copy",
            "-preset",
            "medium",
            "-crf",
            "23",
            output_path,
        ]

        result = await self._run_ffmpeg_command(cmd)
        if result.returncode != 0:
            # 복잡한 필터가 실패하면 간단한 버전으로 재시도
            logging.warning(f"굵은 텍스트 필터 실패, 간단한 버전으로 재시도: {result.stderr}")
            simple_filter = (
                f"[0:v]drawtext="
                f"text='{text}':"
                f"fontfile='/app/app/assets/fonts/Jua-Regular.ttf':"
                f"fontsize={font_size}:"
                f"fontcolor={font_color}:"
                f"x=(w-text_w)/2:"
                f"y=(h-text_h)/2:"
                f"borderw={stroke_width}:"
                f"bordercolor={stroke_color}:"
                f"line_spacing=10:"
                f"enable='between(t,{start_time},{start_time + duration})'[v]"
            )

            cmd[4] = simple_filter
            result = await self._run_ffmpeg_command(cmd)

            if result.returncode != 0:
                raise Exception(f"텍스트 오버레이 추가 실패: {result.stderr}")

        return output_path

    async def add_text_overlay_with_animation(
        self,
        video_path: str,
        text: str,
        start_time: float,
        duration: float,
        animation_effect: str = "NONE",
        font_size: int = 120,  # 100에서 120으로 증가
        font_color: str = "white",
        stroke_color: str = "black",
        stroke_width: int = 10,  # 40에서 10으로 줄임
    ) -> str:
        """애니메이션 효과가 있는 텍스트 오버레이 추가"""
        if animation_effect == "SEQUENTIAL":
            return await self._add_sequential_text(
                video_path, text, start_time, duration, font_size, font_color, stroke_color, stroke_width
            )
        elif animation_effect == "LARGE_TEXT":
            return await self._add_large_text(
                video_path, text, start_time, duration, font_size, font_color, stroke_color, stroke_width
            )
        elif animation_effect == "SMOOTH_POP":
            return await self._add_smooth_pop_text(
                video_path, text, start_time, duration, font_size, font_color, stroke_color, stroke_width
            )
        else:
            # 기본 텍스트 오버레이
            return await self.add_text_overlay(
                video_path, text, start_time, duration, font_size, font_color, stroke_color, stroke_width
            )

    async def _add_sequential_text(
        self,
        video_path: str,
        text: str,
        start_time: float,
        duration: float,
        font_size: int,
        font_color: str,
        stroke_color: str,
        stroke_width: int,
    ) -> str:
        """타이핑 효과 (글자가 순차적으로 나타남) - 수정된 버전"""
        output_path = os.path.join(self.temp_dir, f"sequential_text_{uuid.uuid4()}.mp4")

        # 간단한 페이드인 효과로 대체 (타이핑 효과는 복잡하므로)
        fade_duration = min(0.5, duration * 0.3)  # 전체 시간의 30% 또는 최대 0.5초

        filter_complex = (
            f"[0:v]drawtext="
            f"text='{text}':"
            f"fontfile='/app/app/assets/fonts/Jua-Regular.ttf':"
            f"fontsize={font_size}:"
            f"fontcolor={font_color}:"
            f"x=(w-text_w)/2:"
            f"y=(h-text_h)/2:"
            f"borderw={stroke_width}:"
            f"bordercolor={stroke_color}:"
            f"line_spacing=10:"
            f"alpha='if(lt(t-{start_time},{fade_duration}),(t-{start_time})/{fade_duration},1)':"
            f"enable='between(t,{start_time},{start_time + duration})'[v]"
        )

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            video_path,
            "-filter_complex",
            filter_complex,
            "-map",
            "[v]",
            "-map",
            "0:a?",
            "-c:a",
            "copy",
            "-preset",
            "medium",
            "-crf",
            "23",
            output_path,
        ]

        result = await self._run_ffmpeg_command(cmd)
        if result.returncode != 0:
            # 복잡한 효과가 실패하면 기본 텍스트로 대체
            logging.warning(f"페이드인 효과 실패, 기본 텍스트 사용: {result.stderr}")
            return await self.add_text_overlay(
                video_path, text, start_time, duration, font_size, font_color, stroke_color, stroke_width
            )

        return output_path

    async def _add_large_text(
        self,
        video_path: str,
        text: str,
        start_time: float,
        duration: float,
        font_size: int,
        font_color: str,
        stroke_color: str,
        stroke_width: int,
    ) -> str:
        """크기 변화 효과 - 수정된 버전"""
        output_path = os.path.join(self.temp_dir, f"large_text_{uuid.uuid4()}.mp4")

        animation_duration = min(0.3, duration * 0.5)  # 애니메이션 시간 단축

        if duration <= animation_duration:
            return await self.add_text_overlay(
                video_path, text, start_time, duration, font_size, font_color, stroke_color, stroke_width
            )

        # 더 간단하고 안정적인 크기 변화
        anim_end = start_time + animation_duration

        filter_complex = (
            f"[0:v]drawtext="
            f"text='{text}':"
            f"fontfile='/app/app/assets/fonts/Jua-Regular.ttf':"
            f"fontsize='if(lt(t,{anim_end}),{font_size}*(1.2-0.2*(t-{start_time})/{animation_duration}),{font_size})':"
            f"fontcolor={font_color}:"
            f"x=(w-text_w)/2:"
            f"y=(h-text_h)/2:"
            f"borderw='if(lt(t,{anim_end}),{stroke_width}*(1.2-0.2*(t-{start_time})/{animation_duration}),{stroke_width})':"
            f"bordercolor={stroke_color}:"
            f"line_spacing=10:"
            f"enable='between(t,{start_time},{start_time + duration})'[v]"
        )

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            video_path,
            "-filter_complex",
            filter_complex,
            "-map",
            "[v]",
            "-map",
            "0:a?",
            "-c:a",
            "copy",
            "-preset",
            "medium",
            "-crf",
            "23",
            output_path,
        ]

        result = await self._run_ffmpeg_command(cmd)
        if result.returncode != 0:
            logging.warning(f"크기 변화 효과 실패, 기본 텍스트 사용: {result.stderr}")
            return await self.add_text_overlay(
                video_path, text, start_time, duration, font_size, font_color, stroke_color, stroke_width
            )

        return output_path

    async def _add_smooth_pop_text(
        self,
        video_path: str,
        text: str,
        start_time: float,
        duration: float,
        font_size: int,
        font_color: str,
        stroke_color: str,
        stroke_width: int,
    ) -> str:
        """부드러운 팝업 효과 - 수정된 버전"""
        output_path = os.path.join(self.temp_dir, f"smooth_pop_{uuid.uuid4()}.mp4")

        animation_duration = min(0.3, duration * 0.5)

        if duration <= animation_duration:
            return await self.add_text_overlay(
                video_path, text, start_time, duration, font_size, font_color, stroke_color, stroke_width
            )

        # 더 간단한 팝업 효과: 0.8배에서 시작해서 1.1배로 커졌다가 1.0배로
        mid_time = start_time + animation_duration / 2
        anim_end = start_time + animation_duration

        filter_complex = (
            f"[0:v]drawtext="
            f"text='{text}':"
            f"fontfile='/app/app/assets/fonts/Jua-Regular.ttf':"
            f"fontsize='if(lt(t,{mid_time}),"
            f"{font_size}*(0.8+0.3*(t-{start_time})/{animation_duration}*2),"
            f"if(lt(t,{anim_end}),"
            f"{font_size}*(1.1-0.1*(t-{mid_time})/{animation_duration}*2),"
            f"{font_size}))':"
            f"fontcolor={font_color}:"
            f"x=(w-text_w)/2:"
            f"y=(h-text_h)/2:"
            f"borderw='if(lt(t,{mid_time}),"
            f"{stroke_width}*(0.8+0.3*(t-{start_time})/{animation_duration}*2),"
            f"if(lt(t,{anim_end}),"
            f"{stroke_width}*(1.1-0.1*(t-{mid_time})/{animation_duration}*2),"
            f"{stroke_width}))':"
            f"bordercolor={stroke_color}:"
            f"line_spacing=10:"
            f"enable='between(t,{start_time},{start_time + duration})'[v]"
        )

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            video_path,
            "-filter_complex",
            filter_complex,
            "-map",
            "[v]",
            "-map",
            "0:a?",
            "-c:a",
            "copy",
            "-preset",
            "medium",
            "-crf",
            "23",
            output_path,
        ]

        result = await self._run_ffmpeg_command(cmd)
        if result.returncode != 0:
            logging.warning(f"부드러운 팝업 효과 실패, 기본 텍스트 사용: {result.stderr}")
            return await self.add_text_overlay(
                video_path, text, start_time, duration, font_size, font_color, stroke_color, stroke_width
            )

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
        """비디오에 오디오 추가 - 개선된 버전"""
        if not audio_paths:
            return video_path

        output_path = os.path.join(self.temp_dir, f"with_audio_{uuid.uuid4()}.mp4")

        # 입력 파일들 설정
        inputs = ["-i", video_path]
        for audio_path in audio_paths:
            inputs.extend(["-i", audio_path])

        # 오디오 믹싱 필터 생성
        if len(audio_paths) == 1:
            # 단일 오디오
            volume = audio_volumes[0] if audio_volumes and len(audio_volumes) > 0 else 1.0
            filter_complex = f"[1:a]volume={volume}[a]"
            audio_map = "[a]"
        else:
            # 여러 오디오 믹싱 - 더 안정적인 방법
            filter_parts = []

            # 각 오디오에 볼륨 적용
            for i in range(len(audio_paths)):
                volume = audio_volumes[i] if audio_volumes and i < len(audio_volumes) else 1.0
                filter_parts.append(f"[{i+1}:a]volume={volume}[a{i}]")

            # amix로 모든 오디오 믹싱
            amix_inputs = "".join([f"[a{i}]" for i in range(len(audio_paths))])
            filter_parts.append(f"{amix_inputs}amix=inputs={len(audio_paths)}:duration=first:dropout_transition=2[a]")

            filter_complex = ";".join(filter_parts)
            audio_map = "[a]"

        # FFmpeg 명령어 구성
        cmd = (
            ["ffmpeg", "-y"]
            + inputs
            + [
                "-filter_complex",
                filter_complex,
                "-map",
                "0:v",
                "-map",
                audio_map,
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                "-ar",
                "48000",
                "-shortest",  # 가장 짧은 스트림에 맞춤
                output_path,
            ]
        )

        result = await self._run_ffmpeg_command(cmd)
        if result.returncode != 0:
            # 오류 발생 시 더 자세한 정보 로깅
            logging.error(f"FFmpeg 오디오 추가 실패: {result.stderr}")
            logging.error(f"사용된 명령어: {' '.join(cmd)}")
            logging.error(f"오디오 파일들: {audio_paths}")
            logging.error(f"볼륨 설정: {audio_volumes}")
            raise ServerException(f"오디오 추가 실패: {result.stderr}")

        return output_path

    async def _run_ffmpeg_command(self, cmd: List[str]) -> asyncio.subprocess.Process:
        """FFmpeg 명령 실행"""
        try:
            # 디버깅을 위해 명령어 출력
            logging.warning(f"FFmpeg 명령어 실행: {' '.join(cmd)}")

            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            # 결과를 CompletedProcess와 유사한 형태로 반환
            result = type("CompletedProcess", (), {})()
            result.returncode = process.returncode
            result.stdout = stdout.decode("utf-8") if stdout else ""
            result.stderr = stderr.decode("utf-8") if stderr else ""

            if result.returncode != 0:
                logging.warning(f"FFmpeg 오류: {result.stderr}")

            return result
        except Exception as e:
            logging.error(f"FFmpeg 명령 실행 실패: {str(e)}")
            # 오류 시에도 CompletedProcess 형태로 반환
            result = type("CompletedProcess", (), {})()
            result.returncode = 1
            result.stdout = ""
            result.stderr = str(e)
            return result

    def cleanup(self):
        """임시 파일 정리"""
        if hasattr(self, "temp_dir") and os.path.exists(self.temp_dir):
            import shutil

            shutil.rmtree(self.temp_dir)

    def __del__(self):
        self.cleanup()
