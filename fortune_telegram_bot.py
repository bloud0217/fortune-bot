import os
import requests
import json
import base64
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

def capture_naver_fortune():
    """네이버 띠별 운세 화면을 캡처하고 Base64로 인코딩하여 반환"""
    options = Options()
    options.add_argument('--headless')  # 화면 없이 실행
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # 한국 시간 및 모바일 화면처럼 보이게 설정
    options.add_argument('lang=ko_KR')
    options.add_argument('--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1')

    try:
        driver = webdriver.Chrome(options=options)
        
        # 1. 네이버 띠별 운세 모바일 주소 접속
        print("🚀 네이버 띠별 운세 접속 중...")
        url = "https://m.search.naver.com/search.naver?query=띠별%20운세"
        driver.get(url)
        time.sleep(3) # 데이터 로딩 대기

        # 2. 운세 리스트가 있는 특정 영역 찾기
        fortune_section = driver.find_element(By.CSS_SELECTOR, '._cs_fortune_list')
        
        # 3. 해당 영역만 스크린샷 찍기
        print("📸 운세 리스트 영역 캡처 중...")
        screenshot = fortune_section.screenshot_as_png
        driver.quit()

        # 4. 이미지를 Base64로 인코딩
        return base64.b64encode(screenshot).decode('utf-8')
    except Exception as e:
        print(f"❌ 캡처 에러: {e}")
        return None

def summarize_fortune_image(image_base64):
    """Gemini 비전 API를 사용하여 이미지 속 운세를 한 줄씩 요약"""
    today = datetime.now().strftime("%Y년 %m월 %d일")
    
    if not image_base64:
        return f"🔮 {today} 오늘의 띠별 운세 요약본을 만드는 데 실패했습니다."

    # Gemini 1.5 플래시 모델로 이미지 분석 (비전 기능)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    prompt = f"""
    오늘 날짜: {today}
    이 이미지는 네이버 띠별 운세 화면을 캡처한 것입니다.
    이미지에 있는 12개 띠(쥐, 소, 호랑이, 토끼, 용, 뱀, 말, 양, 원숭이, 닭, 개, 돼지)의 운세 내용을 모두 확인하고, 다음 형식에 맞춰 각 띠별로 한 줄씩 예쁘게 요약해줘.

    [지시사항]
    1. 제목: 🔮 오늘의 띠별 운세 요약
    2. 내용: 각 띠별로 [띠 이모지] [띠 이름]: [한 줄 핵심 요약] 형식
    3. 말투: 친절하고 긍정적인 말투로 작성할 것
    4. 이미지를 기반으로 각 띠별 운세를 한글로 작성해줘.
    """

    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {
                    "mime_type": "image/png",
                    "data": image_base64
                }}
            ]
        }]
    }

    try:
        res = requests.post(url, json=payload, timeout=60) # 이미지 분석은 시간이 걸리므로 타임아웃 넉넉히
        summary = res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        return summary
    exceptException as e:
        print(f"⚠️ Gemini 요약 실패: {e}")
        return f"🔮 {today} 오늘의 띠별 운세 요약본을 만드는 데 실패했습니다. (이미지 분석 오류)"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, json=payload, timeout=10)

def main():
    print("🚀 시작...")
    
    # 1. 네이버 운세 화면 캡처 및 인코딩
    image_base64 = capture_naver_fortune()
    
    if not image_base64:
        send_telegram("네이버 운세 화면을 캡처하는 데 실패했습니다.")
        return

    # 2. Gemini에게 이미지 요약 요청
    print("📝 Gemini 요약 중...")
    final_msg = summarize_fortune_image(image_base64)
    
    # 3. 텔레그램으로 전송
    print("📤 전송 중...")
    send_telegram(final_msg)
    print("✅ 완료!")

if __name__ == "__main__":
    main()
