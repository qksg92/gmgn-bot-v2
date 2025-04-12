from flask import Flask
import threading
import time
import requests
from bs4 import BeautifulSoup

# === 텔레그램 설정 ===
TELEGRAM_TOKEN = '7724611870:AAF-bleAIi3ciNU3ND1wBf8EAceoFVl2cyk'
TELEGRAM_CHAT_ID = '7529989951'  # 개인 ID

# === 감시용 ===
already_alerted = {}
watchlist = {}

# === 기본 설정 ===
GMGN_POPULAR_5M_URL = 'https://gmgn.ai/?chain=sol'
CHECK_INTERVAL = 10
NO_ALERT_SECONDS = 600
KEEP_WATCH_SECONDS = 432000

# === 세션 재사용 ===
session = requests.Session()

# === 코인 상세 페이지 URL ===
def make_detail_url(ca):
    return f'https://gmgn.ai/sol/token/{ca}'

# === 텔레그램 알림 ===
def send_telegram_alert(ca):
    message = f'{ca}'
    telegram_url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'disable_web_page_preview': True
    }
    try:
        session.post(telegram_url, data=payload, timeout=10)
        print(f"[Alert] Sent for {ca}")
    except Exception as e:
        print(f"[Telegram Error] {e}")
        with open('errors.log', 'a') as f:
            f.write(f"Telegram error for {ca}: {e}\n")

# === 1분 거래량 읽기 ===
def get_1m_volume(ca):
    url = make_detail_url(ca)
    try:
        response = session.get(url, timeout=10)
        if response.status_code != 200:
            print(f"[Error] Failed to fetch {ca} detail page (status {response.status_code})")
            return 0
        soup = BeautifulSoup(response.text, 'html.parser')
        volume_element = soup.find(string=lambda t: '거래량 (Volume)' in t)
        if not volume_element:
            print(f"[Volume Error] 거래량 텍스트 없음 for {ca}")
            return 0
        vol_text = volume_element.split('거래량 (Volume)')[-1]
        vol_number = ''.join(c for c in vol_text if c.isdigit() or c == '.')
        if 'K' in vol_text:
            return float(vol_number) * 1000
        elif 'M' in vol_text:
            return float(vol_number) * 1000000
        else:
            return float(vol_number)
    except Exception as e:
        print(f"[Volume Error] {e}")
        with open('errors.log', 'a') as f:
            f.write(f"Volume error for {ca}: {e}\n")
    return 0

# === GMGN 인기탭 긁기 ===
def fetch_popular_cas():
    cas = []
    try:
        response = session.get(GMGN_POPULAR_5M_URL, timeout=10)
        if response.status_code != 200:
            print("[Error] GMGN 인기탭 가져오기 실패 (status {})".format(response.status_code))
            return []
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a', href=True)
        for link in links:
            href = link['href']
            if href.startswith('/sol/token/'):
                ca = href.split('/')[-1]
                if ca.endswith('pump'):
                    cas.append(ca)
    except Exception as e:
        print(f"[GMGN Error] {e}")
        with open('errors.log', 'a') as f:
            f.write(f"GMGN error: {e}\n")
    return list(set(cas))

# === 메인 루프 ===
def monitor():
    while True:
        now = time.time()
        cas = fetch_popular_cas()
        for ca in cas:
            if ca not in watchlist:
                watchlist[ca] = {'start_time': now, 'waiting': False}
                print(f"[New] Watching {ca}")

        for ca in list(watchlist.keys()):
            data = watchlist[ca]
            start_time = data['start_time']
            waiting = data['waiting']

            if now - start_time > KEEP_WATCH_SECONDS:
                print(f"[Delete] {ca} expired")
                del watchlist[ca]
                continue

            volume = get_1m_volume(ca)
            print(f"[Check] {ca} volume: {volume}")

            if volume >= 5000:
                last_alert = already_alerted.get(ca, 0)
                if now - last_alert >= NO_ALERT_SECONDS:
                    send_telegram_alert(ca)
                    already_alerted[ca] = now
                    del watchlist[ca]
            else:
                if not waiting:
                    watchlist[ca]['waiting'] = True
                    watchlist[ca]['start_time'] = now
                elif waiting and now - start_time >= 60:
                    volume_after = get_1m_volume(ca)
                    print(f"[Recheck] {ca} volume after 1m: {volume_after}")
                    if volume_after >= 5000:
                        last_alert = already_alerted.get(ca, 0)
                        if now - last_alert >= NO_ALERT_SECONDS:
                            send_telegram_alert(ca)
                            already_alerted[ca] = now
                    del watchlist[ca]
        time.sleep(CHECK_INTERVAL)

# === 가짜 웹 서버 시작 ===
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

# === 메인 ===
if __name__ == "__main__":
    threading.Thread(target=run).start()
    monitor()
