import os
import requests
import base64
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

# 1. 환경 변수 로드
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

def main():
    print(f"📅 실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not GEMINI_API_KEY or not TELEGRAM_BOT_TOKEN:
        print("❌ 에러: GitHub Secrets에 API 키가 설정되지 않았습니다.")
        return

    # 2. 네이버 띠별 운세 캡처 (Headless Chrome)
    print("🚀 네이버 접속 및 캡처 시작...")
    try:
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1080,3000') # 12개 띠가 다 나오도록 길게 설정
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        driver.get("https://m.search.naver.com/search.naver?query=띠별+운세")
        time.sleep(12) # 페이지 로딩 대기
        
        screenshot = driver.get_screenshot_as_png()
        img_base64 = base64.b64encode(screenshot).decode('utf-8')
        driver.quit()
        print("📸 네이버 화면 캡처 성공!")
    except Exception as e:
        print(f"❌ 캡처 에러 발생: {e}")
        return

    # 3. Gemini AI에게 이미지 분석 및 요약 요청
    print("🧠 Gemini AI(v1)에게 요약 요청 중...")
    # 최신 정식 버전인 v1 주소를 사용합니다.
    api_url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [{
            "parts": [
                {"text": "이미지에 보이는 12개 띠의 오늘 운세를 찾아서, '띠: 내용' 형식으로 한 줄씩 짧게 요약해줘."},
                {"inline_data": {"mime_type": "image/png", "data": img_base64}}
            ]
        }]
    }

    try:
        res = requests.post(api_url, json=payload, timeout=60)
        data = res.json()
        
        if 'candidates' in data:
            fortune_text = data['candidates'][0]['content']['parts'][0]['text'].strip()
            print("✅ AI 요약 완료!")
        else:
            # 에러 발생 시 상세 사유 파악용
            error_detail = data.get('error', {}).get('message', '알 수 없는 응답 구조')
            print(f"🔍 AI 응답 에러 상세: {error_detail}")
            fortune_text = f"🔮 운세 요약 실패 (사유: {error_detail})"
    except Exception as e:
        print(f"❌ AI 요청 중 시스템 에러: {e}")
        fortune_text = "⚠️ 시스템 에러로 운세를 읽어오지 못했습니다."

    # 4. 텔레그램으로 최종 메시지 발송
    print("📤 텔레그램 메시지 발송 중...")
    try:
        tg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(tg_url, json={"chat_id": TELEGRAM_CHAT_ID, "text": fortune_text}, timeout=10)
        print("🎉 모든 작업이 성공적으로 완료되었습니다!")
    except Exception as e:
        print(f"❌ 텔레그램 발송 실패: {e}")

if __name__ == "__main__":
    main()
