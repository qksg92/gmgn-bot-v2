FROM python:3.13-slim

# Install Chromium and ChromeDriver
RUN apt-get update && \
    apt-get install -y chromium chromium-driver && \
    rm -rf /var/lib/apt/lists/*

# Set the environment variable for the chromium binary path
ENV CHROME_BIN=/usr/bin/chromium

# Ensure that chrome works in headless mode
ENV DISPLAY=:99

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

CMD ["gunicorn", "main:app", "-b", "0.0.0.0:8080"]
