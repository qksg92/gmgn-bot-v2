from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import time

# Chrome 옵션 설정 (헤드리스 모드: 브라우저 창을 띄우지 않고 실행)
options = webdriver.ChromeOptions()
options.add_argument("--headless")  
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

# ChromeDriver를 자동으로 설치하고 실행
driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

# 목표 URL로 이동
url = "https://pump.fun/board?coins_sort=last_trade_timestamp"
print("페이지 로딩 중:", url)
driver.get(url)

# 페이지 로딩과 JavaScript 실행을 위해 잠시 대기 (필요에 따라 대기 시간을 조정)
time.sleep(5)

# 현재 렌더링된 HTML 소스를 가져오기
html = driver.page_source

# HTML 소스를 콘솔에 출력 (크면 일부만 나오거나, 파일로 저장할 수도 있음)
print(html)

# 브라우저 종료
driver.quit()
