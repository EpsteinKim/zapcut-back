# Python 3.12 slim 이미지 사용
FROM python:3.12-slim

# 작업 디렉토리 설정
WORKDIR /zapcut-back

# 타임존 설정 (한국 시간)
ENV TZ=Asia/Seoul
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 시스템 의존성 설치 캐싱
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt-get update && apt-get install -y \
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

# 환경 변수 설정 (먼저 설정하여 레이어 캐싱 최적화)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/zapcut-back
ENV ENV=production
ENV DEPLOYMENT_DATE=${DEPLOYMENT_DATE}

# requirements 파일만 먼저 복사 (의존성 변경 시에만 재빌드)
COPY requirements.txt .

# 의존성 설치 (requirements.txt 변경 시에만 재실행)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# temp 디렉토리 생성 및 권한 설정
RUN mkdir -p /zapcut-back/app/temp && \
    chmod 755 /zapcut-back/app/temp

# 애플리케이션 소스 코드 복사 (소스 변경 시에만 재실행)
COPY . .


# FastAPI 서버 실행 (운영 환경용 - 무중단 배포 지원)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80", "--workers", "4", "--access-log"]