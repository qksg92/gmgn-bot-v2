import time
import requests
from bs4 import BeautifulSoup

# === 텔레그램 설정 ===
TELEGRAM_TOKEN = '7724611870:AAF-bleAIi3ciNU3ND1wBf8EAceoFVl2cyk'
TELEGRAM_CHAT_ID = '7529989951'  # 개인 ID

# === 감시용 ===
already_alerted = {}  # {ca: 마지막 전송시간}
watchlist = {}  # {ca: 감시 시작시간}

# === 기본 설정 ===
GMGN_POPULAR_5M_URL = 'https://gmgn.ai/?chain=sol'
CHECK_INTERVAL = 10  # 인기탭 10초마다 검사
RECHECK_INTERVAL = 60  # 1분마다 해당 코인 거래량 다시 체크
NO_ALERT_SECONDS = 600  # 10분 안에는 같은 코인 다시 알림 금지
KEEP_WATCH_SECONDS = 432000  # 5일 = 5 * 24 * 60 * 60

# === 코인 상세 페이지 URL ===
def make_detail_url(ca):
    return f'https://gmgn.ai/sol/token/{ca}'

# === 텔레그램 알림 ===
def send_telegram_alert(ca):
    url = f'https://pump.fun/{ca}'
    message = f'{ca}'
    telegram_url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'disable_web_page_preview': True
    }
    try:
        requests.post(telegram_url, data=payload)
        print(f"[Alert] Sent for {ca}")
    except Exception as e:
        print(f"[Telegram Error] {e}")

# === 1분 거래량 읽기 ===
def get_1m_volume(ca):
    url = make_detail_url(ca)
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"[Error] Failed to fetch {ca} detail page")
            return 0
        soup = BeautifulSoup(response.text, 'html.parser')
        volumes = soup.find_all(string=lambda t: '거래량 (Volume)' in t)
        for vol in volumes:
            try:
                vol_text = vol.split('거래량 (Volume)')[-1]
                vol_number = ''.join(c for c in vol_text if c.isdigit() or c == '.')
                if 'K' in vol_text:
                    return float(vol_number) * 1000
                elif 'M' in vol_text:
                    return float(vol_number) * 1000000
                else:
                    return float(vol_number)
            except:
                pass
    except Exception as e:
        print(f"[Volume Error] {e}")
    return 0

# === GMGN 인기탭 긁기 ===
def fetch_popular_cas():
    cas = []
    try:
        response = requests.get(GMGN_POPULAR_5M_URL, timeout=10)
        if response.status_code != 200:
            print("[Error] GMGN 인기탭 가져오기 실패")
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
    return list(set(cas))  # 중복 제거

# === 메인 루프 ===
def monitor():
    while True:
        now = time.time()

        # 1. GMGN 인기탭 긁어서 새 코인 추가
        cas = fetch_popular_cas()
        for ca in cas:
            if ca not in watchlist:
                watchlist[ca] = now
                print(f"[New] Watching {ca}")

        # 2. 현재 감시중인 코인 체크
        for ca in list(watchlist.keys()):
            # 2-1. 5일 넘으면 감시 종료
            if now - watchlist[ca] > KEEP_WATCH_SECONDS:
                print(f"[Delete] {ca} expired")
                del watchlist[ca]
                continue

            # 2-2. 1분 거래량 체크
            volume = get_1m_volume(ca)
            print(f"[Check] {ca} volume: {volume}")
            
            if volume >= 5000:
                last_alert = already_alerted.get(ca, 0)
                if now - last_alert >= NO_ALERT_SECONDS:
                    send_telegram_alert(ca)
                    already_alerted[ca] = now

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    monitor()