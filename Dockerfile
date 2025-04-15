FROM python:3.11-slim

# 시스템 의존성 설치 (apt.txt 파일 또는 직접 설치)
RUN apt-get update && \
    apt-get install -y \
    chromium-browser \
    chromedriver \
    libgconf-2-4 \
    libnss3 \
    libgdk-pixbuf2.0-0 \
    libdbus-glib-1-2 && \
    rm -rf /var/lib/apt/lists/*

# Chromium 경로 환경 변수 설정
ENV CHROME_BIN=/usr/bin/chromium-browser

WORKDIR /app

# dependencies 설치
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# 애플리케이션 복사
COPY . .

# gunicorn을 통해 Flask 앱 실행
CMD ["gunicorn", "main:app", "-b", "0.0.0.0:8080"]
