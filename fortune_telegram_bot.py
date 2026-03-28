import os
import requests
import base64
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

# 환경 변수 확인
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

def main():
    print("--- 🏁 프로세스 시작 ---")
    
    # 1. 브라우저 설정 (GitHub Actions 최적화)
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu') # GPU 비활성화 추가
    options.add_argument('--window-size=1080,3000')
    
    print("🚀 크롬 드라이버 설치 및 시작 중...")
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        print("🔗 네이버 띠별 운세 접속 중...")
        driver.get("https://m.search.naver.com/search.naver?query=띠별+운세")
        
        # 페이지 로딩 대기 및 결과 확인
        time.sleep(15) 
        print(f"📄 현재 페이지 제목: {driver.title}")
        
        screenshot = driver.get_screenshot_as_png()
        img_data = base64.b64encode(screenshot).decode('utf-8')
        print("📸 캡처 성공 및 인코딩 완료")
        driver.quit()
    except Exception as e:
        print(f"❌ 캡처 단계 실패: {str(e)}")
        return

    # 2. Gemini API 호출
    print("🧠 Gemini AI에게 분석 요청 중...")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [{
            "parts": [
                {"text": "사진 속 12개 띠의 운세를 한 줄씩 요약해줘."},
                {"inline_data": {"mime_type": "image/png", "data": img_data}}
            ]
        }]
    }

    try:
        res = requests.post(url, json=payload, timeout=60)
        data = res.json()
        
        if 'candidates' in data:
            fortune_text = data['candidates'][0]['content']['parts'][0]['text']
            print("✅ AI 요약 성공")
        else:
            fortune_text = f"AI 응답 오류: {data}"
            print(f"❌ AI 응답에 'candidates'가 없음: {data}")
    except Exception as e:
        fortune_text = f"API 호출 중 에러 발생: {str(e)}"
        print(f"❌ API 호출 에러: {str(e)}")

    # 3. 텔레그램 발송
    print("📤 텔레그램 전송 중...")
    try:
        tg_res = requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", 
                               json={"chat_id": TELEGRAM_CHAT_ID, "text": fortune_text}, timeout=10)
        print(f"🎉 전송 시도 완료 (결과: {tg_res.status_code})")
    except Exception as e:
        print(f"❌ 텔레그램 전송 실패: {str(e)}")

if __name__ == "__main__":
    main()
