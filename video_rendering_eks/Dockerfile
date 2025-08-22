FROM python:3.12-slim

ENV TZ=Asia/Seoul \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/zapcut-back \
    ENV=production

# 비대화식 설치 방지(특히 tzdata)
ENV DEBIAN_FRONTEND=noninteractive

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update && apt-get install -y -q --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    libfontconfig1 \
    libxrender1 \
    libgl1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libavcodec-extra \
    libfreetype6 \
    libharfbuzz0b \
    tzdata \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /zapcut-back

COPY video_rendering_eks/requirements-video.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /zapcut-back/app/temp && chmod 777 /zapcut-back/app/temp

COPY . .

RUN chmod +x video_rendering_eks/entrypoint.sh

EXPOSE 80

CMD ["/bin/sh", "-c", "video_rendering_eks/entrypoint.sh"] 