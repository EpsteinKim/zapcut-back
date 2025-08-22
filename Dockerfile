# Python 3.12 slim 이미지 사용
FROM python:3.12-slim

# 작업 디렉토리 설정
WORKDIR /zapcut-back

# 타임존 설정 (한국 시간)
ENV TZ=Asia/Seoul
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 시스템 의존성 설치 (비디오 처리, 오디오 처리, OpenCV, Chromium 등을 위한 패키지)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libfontconfig1 \
    libxrender1 \
    libgl1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libavcodec-extra \
    wget \
    curl \
    gnupg \
    ca-certificates \
    tzdata \
    chromium \
    && rm -rf /var/lib/apt/lists/*

# requirements 파일 복사 및 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 환경 변수 설정
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/zapcut-back
ENV ENV=production
ENV DEPLOYMENT_DATE=${DEPLOYMENT_DATE}

# temp 디렉토리 생성 및 권한 설정
RUN mkdir -p /zapcut-back/app/temp && \
    chmod 755 /zapcut-back/app/temp

# 애플리케이션 소스 코드 복사
COPY . .


# FastAPI 서버 실행 (운영 환경용 - 무중단 배포 지원)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80", "--workers", "4", "--access-log"]