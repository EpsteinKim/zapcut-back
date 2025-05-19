FROM python:3.9.6-slim

WORKDIR /app

# pip-tools 설치
RUN pip install --no-cache-dir pip-tools

# requirements 파일 복사 및 설치
COPY requirements.in .
RUN pip-compile requirements.in > requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# .env 파일 복사
COPY .env.example .env

# 나머지 소스 코드 복사
COPY . .

CMD ["python", "-m", "pytest", "tests/"] 