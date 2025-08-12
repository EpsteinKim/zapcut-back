FROM python:3.12-slim

ENV TZ=Asia/Seoul \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/zapcut-back \
    ENV=production

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    libfontconfig1 \
    libxrender1 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgtk-3-0 \
    libavcodec-extra \
    libfreetype6 \
    libharfbuzz0b \
    tzdata \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /zapcut-back

COPY video_rendering/requirements-video.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /zapcut-back/app/temp && chmod 755 /zapcut-back/app/temp

COPY . .

RUN chmod +x video_rendering/entrypoint.sh

EXPOSE 80

CMD ["/bin/sh", "-c", "video_rendering/entrypoint.sh"] 