import os, requests, base64, time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def main():
    # 1. 환경 변수
    api_key = os.environ.get('GEMINI_API_KEY')
    tg_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    # 2. 네이버 캡처
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        driver.get("https://m.search.naver.com/search.naver?query=띠별+운세")
        time.sleep(15)
        img_data = base64.b64encode(driver.get_screenshot_as_png()).decode('utf-8')
    finally:
        driver.quit()

    # 3. Gemini 2.0 Flash 호출 (성민님 계정 확인 모델)
    # 알려주신 목록 중 가장 빠르고 안정적인 2.0-flash를 사용합니다.
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [
                {"text": "이미지에 있는 12개 띠별 운세를 '띠: 내용' 형식으로 한 줄씩 요약해줘."},
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
        error_msg = data.get('error', {}).get('message', 'Unknown Error')
        fortune_text = f"❌ Gemini 2.0 호출 실패: {error_msg}"

    requests.post(f"https://api.telegram.org/bot{tg_token}/sendMessage", 
                  json={"chat_id": chat_id, "text": fortune_text})

if __name__ == "__main__":
    main()
