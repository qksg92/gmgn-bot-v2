from flask import Flask
import threading
import time
import requests
import os  # 운영체제 관련 모듈
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options  # Selenium Chrome 옵션
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# === 텔레그램 설정 ===
TELEGRAM_TOKEN = '7724611870:AAF-bleAIi3ciNU3ND1wBf8EAceoFVl2cyk'  # 본인의 텔레그램 봇 토큰
TELEGRAM_CHAT_ID = '7529989951'  # 본인의 텔레그램 사용자 ID

# === 감시 관련 변수 ===
already_alerted = {}  # {코인아이디: 마지막 알림전송 시간}
watchlist = {}        # {코인아이디: {'start_time': 감시 시작 시간, 'waiting': 대기 상태}}

# === 기본 설정 ===
PUMP_FUN_URL_1 = 'https://pump.fun/board?coins_sort=last_reply'           # URL 1: 마지막 댓글 정렬
PUMP_FUN_URL_2 = 'https://pump.fun/board?coins_sort=last_trade_timestamp'   # URL 2: 마지막 거래 정렬
CHECK_INTERVAL = 10      # 10초마다 검사
NO_ALERT_SECONDS = 600   # 같은 코인 알림 재전송 금지 시간 (10분)
KEEP_WATCH_SECONDS = 432000  # 감시 유지 시간 (5일)

# === 세션 재사용 ===
session = requests.Session()


# === 코인 상세 페이지 URL 생성 함수 ===
def make_detail_url(ca):
    return f'https://pump.fun/coin/{ca}'


# === 텔레그램 알림 함수 ===
def send_telegram_alert(ca):
    detail_url = make_detail_url(ca)
    message = f"코인: {ca}\n상세페이지: {detail_url}"
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


# === 1분 거래액 읽기 함수 (코인 상세 페이지에서 거래량과 가격을 추출) ===
def get_1m_value(ca):
    url = make_detail_url(ca)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = session.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"[Error] {ca} 상세 페이지 불러오기 실패 (상태 {response.status_code})")
            return 0
        soup = BeautifulSoup(response.text, 'html.parser')

        # 거래량 (Volume) 추출
        volume_element = soup.find(string=lambda t: '거래량 (Volume)' in t)
        if not volume_element:
            print(f"[Volume Error] {ca}의 거래량 텍스트 없음")
            return 0
        vol_text = volume_element.split('거래량 (Volume)')[-1]
        vol_number = ''.join(c for c in vol_text if c.isdigit() or c == '.')

        # 가격 (Price) 추출
        price_element = soup.find(string=lambda t: '가격 (Price)' in t)
        if not price_element:
            print(f"[Price Error] {ca}의 가격 정보 없음")
            return 0
        price_text = price_element.split('가격 (Price)')[-1]
        price_number = ''.join(c for c in price_text if c.isdigit() or c == '.')

        return float(vol_number) * float(price_number)
    except Exception as e:
        print(f"[Value Error] {ca} - {e}")
        with open('errors.log', 'a') as f:
            f.write(f"Value error for {ca}: {e}\n")
    return 0


# === 특정 URL에서 전체 코인 리스트 가져오기 (스크롤 다운 포함) ===
def fetch_all_cas_with_scroll(url):
    cas = []
    options = Options()
    options.headless = True  # Headless 모드 (화면 없이 실행)

    # 운영체제에 따른 Chrome 실행파일 경로 지정 (Windows/리눅스 등)
    if os.name == "nt":  # Windows인 경우
        options.binary_location = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    else:  # 리눅스/Render 환경인 경우
        options.binary_location = "/usr/bin/chromium"
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

    # webdriver_manager를 사용한 ChromeDriver 자동 설치 및 실행
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)
    time.sleep(5)  # 페이지 로드 대기

    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    coins = soup.find_all('div', class_='coin-list-item')  # 실제 HTML 구조에 따라 수정 필요
    for coin in coins:
        try:
            a_tag = coin.find('a')
            if not a_tag:
                continue
            ca = a_tag['href'].split('/')[-1]
            market_cap_span = coin.find('span', class_='market-cap')
            volume_span = coin.find('span', class_='volume')
            if not market_cap_span or not volume_span:
                continue
            market_cap = market_cap_span.text.strip().replace('$', '').replace(',', '')
            volume = volume_span.text.strip().replace('$', '').replace(',', '')
            # 코인 필터링: 예시로 시장가치 10,000 ~ 100,000 사이인 코인만 추가
            if market_cap and volume and 10000 <= float(market_cap) <= 100000:
                cas.append(ca)
        except Exception as e:
            print(f"[Parsing Error] {e}")
            continue

    driver.quit()
    return cas


# === 메인 감시 루프 ===
def monitor():
    while True:
        now = time.time()
        # 두 URL 모두에서 코인 리스트를 가져오고 중복 제거
        cas_1 = fetch_all_cas_with_scroll(PUMP_FUN_URL_1)
        cas_2 = fetch_all_cas_with_scroll(PUMP_FUN_URL_2)
        cas = list(set(cas_1 + cas_2))
        print(f"[Fetch] Total coins found: {cas}")

        # 새로운 코인 감시 시작
        for ca in cas:
            if ca not in watchlist:
                watchlist[ca] = {'start_time': now, 'waiting': False}
                print(f"[New] Watching {ca}")

        # 감시 중인 코인 상태 점검
        for ca in list(watchlist.keys()):
            data = watchlist[ca]
            start_time = data['start_time']
            waiting = data['waiting']

            # 감시 만료 조건 (KEEP_WATCH_SECONDS 이후 삭제)
            if now - start_time > KEEP_WATCH_SECONDS:
                print(f"[Delete] {ca} 감시 종료 (만료)")
                del watchlist[ca]
                continue

            value = get_1m_value(ca)
            print(f"[Check] {ca} 거래액: {value}")
            if value >= 5000:
                last_alert = already_alerted.get(ca, 0)
                if now - last_alert >= NO_ALERT_SECONDS:
                    send_telegram_alert(ca)
                    already_alerted[ca] = now
            else:
                # 거래액 기준 미달이면 대기 상태 처리
                if not waiting:
                    watchlist[ca]['waiting'] = True
                    watchlist[ca]['start_time'] = now
                elif waiting and now - start_time >= 60:
                    # 1분 후 재확인
                    value_after = get_1m_value(ca)
                    print(f"[Recheck] {ca} 1분 후 거래액: {value_after}")
                    if value_after >= 5000:
                        last_alert = already_alerted.get(ca, 0)
                        if now - last_alert >= NO_ALERT_SECONDS:
                            send_telegram_alert(ca)
                            already_alerted[ca] = now

        time.sleep(CHECK_INTERVAL)


# === Flask 애플리케이션 설정 (봇 상태 확인용) ===
app = Flask(__name__)


@app.route('/')
def home():
    return "Bot is running!"


def run_flask():
    app.run(host='0.0.0.0', port=8080)


# === 메인 실행 ===
if __name__ == "__main__":
    #
