import os, requests, base64, time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def main():
    API_KEY = os.environ.get('GEMINI_API_KEY')
    TG_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
    CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

    # 1. 네이버 캡처
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

    # 2. 후보 모델 리스트 (성민님 계정에서 허용될 가능성이 높은 순서)
    # 404 에러를 피하기 위해 가장 보편적인 모델들로 구성했습니다.
    model_candidates = [
        "gemini-1.5-flash-8b", 
        "gemini-1.5-flash",
        "gemini-1.5-pro"
    ]

    fortune_text = "운세 요약 실패"
    
    for model in model_candidates:
        print(f"🔄 {model} 모델로 시도 중...")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={API_KEY}"
        
        payload = {
            "contents": [{
                "parts": [
                    {"text": "12개 띠별 운세를 한 줄씩 요약해줘."},
                    {"inline_data": {"mime_type": "image/png", "data": img_data}}
                ]
            }]
        }

        res = requests.post(url, json=payload)
        data = res.json()

        if 'candidates' in data:
            fortune_text = data['candidates'][0]['content']['parts'][0]['text']
            print(f"✅ {model} 모델로 성공!")
            break
        else:
            print(f"❌ {model} 실패: {data.get('error', {}).get('message', 'Unknown')}")

    # 3. 텔레그램 전송
    requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", 
                  json={"chat_id": CHAT_ID, "text": fortune_text})

if __name__ == "__main__":
    main()
