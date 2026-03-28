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
        time.sleep(10) # 화면이 다 뜰 때까지 충분히 대기

        screenshot = driver.get_screenshot_as_png()
        driver.quit()
        return base64.b64encode(screenshot).decode('utf-8')
    except Exception as e:
        print(f"❌ 캡처 에러: {e}")
        return None

def summarize_fortune_image(image_base64):
    today = datetime.now().strftime("%Y년 %m월 %d일")
    # 분석 성능이 더 좋은 1.5-flash 모델 사용
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    # AI가 거절하지 않도록 프롬프트를 더 단순하고 명확하게 수정
    prompt = f"이 사진은 {today} 네이버 띠별 운세 검색 결과야. 사진 속에 보이는 12개 띠의 운세 내용을 각각 한 줄씩만 아주 짧게 요약해서 리스트로 만들어줘."

    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": "image/png", "data": image_base64}}
            ]
        }],
        "safetySettings": [ # 안전 필터로 인해 답변이 막히는 것을 방지
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }

    try:
        res = requests.post(api_url, json=payload, timeout=60)
        data = res.json()
        
        # 답변이 정상적으로 왔는지 확인하는 로직 강화
        if 'candidates' in data and data['candidates'][0].get('content'):
            return data['candidates'][0]['content']['parts'][0]['text'].strip()
        else:
            print(f"🔍 AI 응답 구조: {data}")
            return f"🔮 {today} 운세 요약 실패 (AI가 답변을 생성하지 못했습니다. 다시 시도해 주세요.)"
    except Exception as e:
        return f"⚠️ 에러 발생: {str(e)}"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, json=payload)

def main():
    img = capture_full_screen()
    if img:
        msg = summarize_fortune_image(img)
        send_telegram(msg)
        print("✅ 전송 완료!")
    else:
        print("❌ 실패")

if __name__ == "__main__":
    main()
