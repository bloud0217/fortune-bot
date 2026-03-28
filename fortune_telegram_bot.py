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
        print("🚀 네이버 접속 중...")
        url = "https://m.search.naver.com/search.naver?query=띠별+운세"
        driver.get(url)
        time.sleep(15) # 로딩 시간을 15초로 대폭 늘림
        screenshot = driver.get_screenshot_as_png()
        driver.quit()
        return base64.b64encode(screenshot).decode('utf-8')
    except Exception as e:
        print(f"❌ 캡처 에러: {e}")
        return None

def summarize_fortune_image(image_base64):
    today = datetime.now().strftime("%Y년 %m월 %d일")
    # v1beta가 아닌 정식 v1 주소 사용
    api_url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [{
            "parts": [
                {"text": f"이 사진은 {today} 네이버 띠별 운세 검색 결과야. 사진 속 12개 띠의 운세를 한 줄씩 요약해줘."},
                {"inline_data": {"mime_type": "image/png", "data": image_base64}}
            ]
        }]
    }

    try:
        res = requests.post(api_url, json=payload, timeout=60)
        data = res.json()
        
        # 응답이 정상적으로 오면 출력, 아니면 에러 메시지 상세 출력
        if 'candidates' in data:
            return data['candidates'][0]['content']['parts'][0]['text'].strip()
        else:
            # 여기서 에러 원인을 텔레그램으로 쏴서 정확히 파악합니다.
            error_msg = data.get('error', {}).get('message', '알 수 없는 응답 구조')
            return f"🔮 요약 실패 상세 사유: {error_msg}"
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
        print("✅ 실행 완료")
    else:
        print("❌ 캡처 단계 실패")

if __name__ == "__main__":
    main()
