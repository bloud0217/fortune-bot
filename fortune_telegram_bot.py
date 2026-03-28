import os
import requests
import base64
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

# 1. 환경 변수 설정
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

def main():
    # 2. 네이버 캡처 (가장 안정적인 설정)
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1080,3000')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        driver.get("https://m.search.naver.com/search.naver?query=띠별+운세")
        time.sleep(12) 
        img_data = base64.b64encode(driver.get_screenshot_as_png()).decode('utf-8')
    finally:
        driver.quit()

    # 3. Gemini 전송 (가장 호환성 높은 v1beta 버전 사용)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [{
            "parts": [
                {"text": "사진 속 12개 띠의 운세를 한 줄씩 요약해줘."},
                {"inline_data": {"mime_type": "image/png", "data": img_data}}
            ]
        }]
    }

    res = requests.post(url, json=payload)
    data = res.json()

    # 4. 결과 발송
    try:
        fortune_text = data['candidates'][0]['content']['parts'][0]['text']
    except:
        fortune_text = f"오류 발생: {data}"

    requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", 
                  json={"chat_id": TELEGRAM_CHAT_ID, "text": fortune_text})

if __name__ == "__main__":
    main()
