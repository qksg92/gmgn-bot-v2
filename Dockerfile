FROM python:3.11-slim

# apt-get으로 Linux 패키지를 설치 (chromium-browser, chromedriver)
RUN apt-get update && \
    apt-get install -y chromium-browser chromedriver && \
    rm -rf /var/lib/apt/lists/*

# 환경 변수 설정: Chromium 실행 파일 경로 지정
ENV CHROME_BIN=/usr/bin/chromium-browser

# 작업 디렉토리 설정
WORKDIR /app

# requirements.txt 복사 및 Python 패키지 설치
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# 프로젝트 전체 복사
COPY . .

# 애플리케이션 실행: 여기서는 gunicorn을 사용하여 Flask 앱을 실행
CMD ["gunicorn", "main:app", "-b", "0.0.0.0:8080"]
