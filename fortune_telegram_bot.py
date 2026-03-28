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
    options.add_argument('--window-size=1080,3000') 
    options.add_argument('lang=ko_KR')
    options.add_argument('--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1')

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        print("🚀 네이버 접속 및 캡처 중...")
        url = "https://m.search.naver.com/search.naver?query=띠별+운세"
        driver.get(url)
        time.sleep(12) # 로딩 시간을 조금 더 늘렸습니다.

        screenshot = driver.get_screenshot_as_png()
        driver.quit()
        return base64.b64encode(screenshot).decode('utf-8')
    except Exception as e:
        print(f"❌ 캡처 에러: {e}")
        return None

def summarize_fortune_image(image_base64):
    today = datetime.now().strftime("%Y년 %m월 %d일")
    # 최신 주소 체계인 v1으로 시도하고, 모델명에 'latest'를 붙였습니다.
    api_url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash-latest:generateContent?key={GEMINI_API_KEY}"
    
    prompt = f"이미지에 보이는 {today} 띠별 운세 내용을 각 띠별로 한 줄씩 요약해줘. 형식은 '띠이모지 띠이름: 요약내용'으로 해줘."

    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": "image/png", "data": image_base64}}
            ]
        }]
    }

    try:
        res = requests.post(api_url, json=payload, timeout=60)
        data = res.json()
        
        # 만약 v1에서 실패하면 v1beta로 다시 한 번 자동 시도
        if 'error' in data and data['error']['code'] == 404:
            print("⚠️ v1 실패, v1beta로 재시도 중...")
            api_url_beta = api_url.replace("/v1/", "/v1beta/")
            res = requests.post(api_url_beta, json=payload, timeout=60)
            data = res.json()

        if 'candidates' in data and data['candidates'][0].get('content'):
            return data['candidates'][0]['content']['parts'][0]['text'].strip()
        else:
            print(f"🔍 최종 응답 에러 상세: {data}")
            return f"🔮 {today} 운세 요약 실패 (상세: {data.get('error', {}).get('message', '응답 구조 에러')})"
    except Exception as e:
        return f"⚠️ 시스템 에러: {str(e)}"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, json=payload)

def main():
    img = capture_full_screen()
    if img:
        msg = summarize_fortune_image(img)
        send_telegram(msg)
        print("✅ 전송 시도 완료!")
    else:
        print("❌ 캡처 실패")

if __name__ == "__main__":
    main()
