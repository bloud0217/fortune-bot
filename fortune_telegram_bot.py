import os
import requests
import json
import base64
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

def capture_naver_fortune():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('lang=ko_KR')
    options.add_argument('--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1')

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        print("🚀 네이버 띠별 운세 접속 중...")
        # 띠별 운세 탭이 바로 보이는 주소로 변경
        url = "https://m.search.naver.com/search.naver?query=띠별+운세"
        driver.get(url)
        time.sleep(7) # 로딩 시간을 넉넉히 7초로 늘렸습니다.

        # 캡처할 영역의 이름을 정확하게 수정 (._cs_fortune_list)
        print("📸 운세 영역 찾는 중...")
        fortune_section = driver.find_element(By.CSS_SELECTOR, '._cs_fortune_list')
        
        screenshot = fortune_section.screenshot_as_png
        driver.quit()

        return base64.b64encode(screenshot).decode('utf-8')
    except Exception as e:
        print(f"❌ 캡처 에러: {e}")
        if 'driver' in locals(): driver.quit()
        return None

def summarize_fortune_image(image_base64):
    today = datetime.now().strftime("%Y년 %m월 %d일")
    if not image_base64:
        return f"🔮 {today} 운세 캡처에 실패했습니다."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    prompt = f"""
    오늘 날짜: {today}
    이미지에 보이는 12개 띠의 운세를 확인하고 요약해줘.
    [형식]
    🔮 오늘의 띠별 운세 요약
    🐭 쥐띠: [한 줄 요약]
    ... (12개 띠 전부)
    친절하고 희망찬 말투로 작성해줘.
    """

    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": "image/png", "data": image_base64}}
            ]
        }]
    }

    try:
        res = requests.post(url, json=payload, timeout=60)
        summary = res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        return summary
    except Exception as e:
        print(f"⚠️ 요약 실패: {e}")
        return f"🔮 {today} 운세 분석 중 오류가 발생했습니다."

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, json=payload, timeout=10)

def main():
    image_base64 = capture_naver_fortune()
    if image_base64:
        final_msg = summarize_fortune_image(image_base64)
        send_telegram(final_msg)
        print("✅ 전송 완료!")
    else:
        print("❌ 실행 실패")

if __name__ == "__main__":
    main()
