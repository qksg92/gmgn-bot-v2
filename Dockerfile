FROM python:3.11-slim

# apt-get으로 Linux 패키지를 설치 (chromium, chromedriver)
RUN apt-get update && \
    apt-get install -y chromium chromium-driver && \
    rm -rf /var/lib/apt/lists/*

# 환경 변수 설정: Chromium 실행 파일 경로 지정 (설치된 경로 확인 필요)
ENV CHROME_BIN=/usr/bin/chromium

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

CMD ["gunicorn", "main:app", "-b", "0.0.0.0:8080"]
