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
        time.sleep(12)
        screenshot = driver.get_screenshot_as_png()
        driver.quit()
        return base64.b64encode(screenshot).decode('utf-8')
    except Exception as e:
        print(f"❌ 캡처 에러: {e}")
        return None

def summarize_fortune_image(image_base64):
    today = datetime.now().strftime("%Y년 %m월 %d일")
    # 시도해볼 모델 후보군 리스트
    model_candidates = [
        "gemini-1.5-flash",
        "gemini-1.5-flash-latest",
        "gemini-pro-vision"
    ]
    
    prompt = f"이 사진은 {today} 네이버 띠별 운세야. 12개 띠의 운세를 찾아서 한 줄씩 요약해줘."
    payload = {
        "contents": [{"parts": [
            {"text": prompt},
            {"inline_data": {"mime_type": "image/png", "data": image_base64}}
        ]}]
    }

    # 성공할 때까지 모델을 바꿔가며 시도
    for model in model_candidates:
        print(f"🔄 {model} 모델로 시도 중...")
        # v1 버전으로 우선 시도
        api_url = f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={GEMINI_API_KEY}"
        try:
            res = requests.post(api_url, json=payload, timeout=60)
            data = res.json()
            
            # 성공 시 결과 반환
            if 'candidates' in data and data[0].get('content') or 'candidates' in data and len(data['candidates']) > 0:
                return data['candidates'][0]['content']['parts'][0]['text'].strip()
            
            # v1 실패 시 v1beta로 한 번 더 시도
            print(f"⚠️ {model} (v1) 실패, v1beta 재시도...")
            res_beta = requests.post(api_url.replace("/v1/", "/v1beta/"), json=payload, timeout=60)
            data_beta = res_beta.json()
            if 'candidates' in data_beta:
                return data_beta['candidates'][0]['content']['parts'][0]['text'].strip()
        except:
            continue

    return f"🔮 {today} 모든 AI 모델 시도 실패. API 키의 모델 권한을 확인해주세요."

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, json=payload)

def main():
    img = capture_full_screen()
    if img:
        msg = summarize_fortune_image(img)
        send_telegram(msg)
        print("✅ 프로세스 종료")
    else:
        print("❌ 실패")

if __name__ == "__main__":
    main()
