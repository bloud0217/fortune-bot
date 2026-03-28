import os
import requests
import base64
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

def capture_full_screen():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1080,1920') # 세로로 긴 모바일 화면 크기 설정
    options.add_argument('lang=ko_KR')
    options.add_argument('--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1')

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        print("🚀 네이버 띠별 운세 접속 중...")
        url = "https://m.search.naver.com/search.naver?query=띠별+운세"
        driver.get(url)
        time.sleep(10) # 로딩 대기 시간을 10초로 대폭 늘렸습니다.

        # 특정 영역이 아니라 '전체 화면'을 캡처합니다.
        print("📸 전체 화면 캡처 중...")
        screenshot = driver.get_screenshot_as_png()
        driver.quit()

        return base64.b64encode(screenshot).decode('utf-8')
    except Exception as e:
        print(f"❌ 캡처 에러: {e}")
        if 'driver' in locals(): driver.quit()
        return None

def summarize_fortune_image(image_base64):
    today = datetime.now().strftime("%Y년 %m월 %d일")
    if not image_base64:
        return f"🔮 {today} 화면 캡처에 실패했습니다."

    # Gemini 1.5 Flash 모델 사용 (비전 성능이 좋습니다)
    url = f"https://generativelanguage.googleapis.
