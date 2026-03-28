import os
import requests
import base64
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def main():
    print("1. 환경 변수 체크 중...")
    API_KEY = os.environ.get('GEMINI_API_KEY')
    TG_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
    CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

    if not all([API_KEY, TG_TOKEN, CHAT_ID]):
        print("❌ 환경 변수 누락!")
        return

    print("2. 브라우저 실행 준비...")
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    try:
        # 최신 방식: Service 객체 사용
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        print("3. 네이버 접속 중...")
        driver.get("https://m.search.naver.com/search.naver?query=띠별+운세")
        time.sleep(10)
        
        print("4. 화면 캡처 중...")
        screenshot = driver.get_screenshot_as_png()
        img_base64 = base64.b64encode(screenshot).decode('utf-8')
        driver.quit()
    except Exception as e:
        print(f"❌ 브라우저 단계 에러: {e}")
        return

    print("5. Gemini AI 요청 중...")
    # v1 주소가 막히면 안 되니 가장 안전한 v1beta로 재시도
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    
    payload = {
        "contents": [{
            "parts": [
                {"text": "12개 띠별 운세를 한 줄씩 요약해줘."},
                {"inline_data": {"mime_type": "image/png", "data": img_base64}}
            ]
        }]
    }

    try:
        res = requests.post(url, json=payload)
        data = res.json()
        fortune_text = data['candidates'][0]['content']['parts'][0]['text']
        print("✅ AI 요약 성공!")
    except Exception as e:
        print(f"❌ AI 단계 에러: {data if 'data' in locals() else e}")
        fortune_text = "운세 요약 실패"

    print("6. 텔레그램 발송 중...")
    requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", 
                  json={"chat_id": CHAT_ID, "text": fortune_text})
    print("🏁 모든 작업 완료!")

if __name__ == "__main__":
    main()
