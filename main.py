from flask import Flask
import threading
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# === 텔레그램 설정 ===
TELEGRAM_TOKEN = '7724611870:AAF-bleAIi3ciNU3ND1wBf8EAceoFVl2cyk'  # 여기에 본인의 텔레그램 봇 토큰을 입력하세요.
TELEGRAM_CHAT_ID = '7529989951'  # 여기에 본인의 텔레그램 사용자 ID를 입력하세요.

# === 감시용 ===
already_alerted = {}  # {ca: 마지막 전송시간}
watchlist = {}  # {ca: {'start_time': 시작시간, 'waiting': 대기중 여부}}

# === 기본 설정 ===
PUMP_FUN_URL_1 = 'https://pump.fun/board?coins_sort=last_reply'  # 펌프펀 전체 코인 리스트 URL 1
PUMP_FUN_URL_2 = 'https://pump.fun/board?coins_sort=last_trade_timestamp'  # 펌프펀 전체 코인 리스트 URL 2
CHECK_INTERVAL = 10  # 10초마다 검사
NO_ALERT_SECONDS = 600  # 같은 코인 다시 알림 금지 시간 (10분)
KEEP_WATCH_SECONDS = 432000  # 감시 유지 시간 (5일)

# === 세션 재사용 ===
session = requests.Session()

# === 코인 상세 페이지 URL ===
def make_detail_url(ca):
    return f'https://pump.fun/coin/{ca}'  # 펌프펀에서 코인 상세 URL을 만들기

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

# === 1분 거래액 읽기 ===
def get_1m_value(ca):
    url = make_detail_url(ca)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = session.get(url, headers=headers, timeout=10)  # User-Agent 추가
        if response.status_code != 200:
            print(f"[Error] Failed to fetch {ca} detail page (status {response.status_code})")
            return 0
        soup = BeautifulSoup(response.text, 'html.parser')

        # 거래량 추출
        volume_element = soup.find(string=lambda t: '거래량 (Volume)' in t)
        if not volume_element:
            print(f"[Volume Error] 거래량 텍스트 없음 for {ca}")
            return 0
        vol_text = volume_element.split('거래량 (Volume)')[-1]
        vol_number = ''.join(c for c in vol_text if c.isdigit() or c == '.')

        # 가격 추출
        price_element = soup.find(string=lambda t: '가격 (Price)' in t)
        if not price_element:
            print(f"[Price Error] 가격 정보 없음 for {ca}")
            return 0
        price_text = price_element.split('가격 (Price)')[-1]
        price_number = ''.join(c for c in price_text if c.isdigit() or c == '.')

        # 거래액 = 거래량 * 가격
        return float(vol_number) * float(price_number)
        
    except Exception as e:
        print(f"[Value Error] {e}")
        with open('errors.log', 'a') as f:
            f.write(f"Value error for {ca}: {e}\n")
    return 0

# === 펌프펀 전체 코인 리스트 가져오기 ===
def fetch_all_cas_with_scroll():
    cas = []
<<<<<<< HEAD
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get(PUMP_FUN_URL_1)  # 여기서 URL을 PUMP_FUN_URL_1로 변경

    time.sleep(5)  # 페이지가 로드될 때까지 기다림
=======
    try:
        response = session.get(GMGN_POPULAR_5M_URL, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)  # User-Agent 추가
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
    return list(set(cas))  # 중복 제거

# === GMGN 완료탭 긁기 ===
def fetch_completed_cas():
    cas = []
    try:
        response = session.get(GMGN_COMPLETED_URL, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)  # User-Agent 추가
        if response.status_code != 200:
            print("[Error] GMGN 완료탭 가져오기 실패 (status {})".format(response.status_code))
            return []
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a', href=True)
        for link in links:
            href = link['href']
            if href.startswith('/sol/token/'):
                ca = href.split('/')[-1]
                cas.append(ca)
    except Exception as e:
        print(f"[GMGN Error] {e}")
        with open('errors.log', 'a') as f:
            f.write(f"GMGN error: {e}\n")
    return list(set(cas))  # 중복 제거
>>>>>>> 9aa73dd91c0bc36d17a74e455f07f35995bdeca1

    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")  # 페이지 끝까지 스크롤
        time.sleep(3)  # 잠시 기다려서 더 많은 코인들이 로드될 시간 제공

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:  # 더 이상 스크롤이 내려가지 않으면 종료
            break
        last_height = new_height

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    coins = soup.find_all('div', class_='coin-list-item')  # 이 부분은 펌프펀의 실제 HTML 구조에 맞게 수정해야 함
    for coin in coins:
        ca = coin.find('a')['href'].split('/')[-1]
        market_cap = coin.find('span', class_='market-cap').text.strip().replace('$', '').replace(',', '')  # 시가총액
        volume = coin.find('span', class_='volume').text.strip().replace('$', '').replace(',', '')  # 거래액
        if float(market_cap) >= 10000 and float(market_cap) <= 100000:  # 시가총액이 10,000 ~ 100,000달러 사이
            cas.append(ca)
    
    driver.quit()  # 드라이버 종료

    return cas  # 조건에 맞는 코인 반환

# === 메인 루프 ===
def monitor():
    while True:
        now = time.time()

        # 1. 펌프펀 전체 코인 리스트 가져오기
        cas = fetch_all_cas_with_scroll()
        for ca in cas:
            if ca not in watchlist:
                watchlist[ca] = {'start_time': now, 'waiting': False}
                print(f"[New] Watching {ca}")

        # 2. 현재 감시중인 코인 체크
        for ca in list(watchlist.keys()):
            data = watchlist[ca]
            start_time = data['start_time']
            waiting = data['waiting']

            # 2-1. 5일 넘으면 감시 종료
            if now - start_time > KEEP_WATCH_SECONDS:
                print(f"[Delete] {ca} expired")
                del watchlist[ca]
                continue

            # 2-2. 현재 거래액 체크
            value = get_1m_value(ca)
            print(f"[Check] {ca} value: {value}")

            if value >= 5000:  # 거래액 5000달러 이상
                last_alert = already_alerted.get(ca, 0)
                if now - last_alert >= NO_ALERT_SECONDS:
                    send_telegram_alert(ca)
                    already_alerted[ca] = now
                    # 코인을 감시 목록에서 삭제하지 않음
                    # del watchlist[ca]  # 이 부분을 삭제하거나 주석 처리
            else:
                # 거래액이 안 넘었고 아직 대기중이 아니면 대기상태로 바꿈
                if not waiting:
                    watchlist[ca]['waiting'] = True
                    watchlist[ca]['start_time'] = now  # 1분 대기 시작 시간 기록

                # 이미 대기중이라면 1분 지났는지 확인
                elif waiting and now - start_time >= 60:
                    # 1분 기다렸다가 다시 체크
                    value_after = get_1m_value(ca)
                    print(f"[Recheck] {ca} value after 1m: {value_after}")
                    if value_after >= 5000:
                        last_alert = already_alerted.get(ca, 0)
                        if now - last_alert >= NO_ALERT_SECONDS:
                            send_telegram_alert(ca)
                            already_alerted[ca] = now
                    # 대기 끝났으면 무조건 감시 종료
                    # del watchlist[ca]  # 이 부분을 삭제하거나 주석 처리

        time.sleep(CHECK_INTERVAL)  # 요청 간 간격을 두어 서버에서 차단되지 않도록 함

# === Flask 애플리케이션 설정 ===
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

# === 메인 ===
if __name__ == "__main__":
    threading.Thread(target=run).start()  # Flask 서버를 별도의 스레드에서 실행
<<<<<<< HEAD
    monitor()  # 봇 감시 루프를 실행
=======
    monitor()  # 봇 감시 루프를 실행
>>>>>>> 9aa73dd91c0bc36d17a74e455f07f35995bdeca1
