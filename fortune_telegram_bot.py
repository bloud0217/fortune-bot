import os, requests, base64, time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def main():
    API_KEY = os.environ.get('GEMINI_API_KEY')
    TG_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
    CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

    # 1. 네이버 캡처 (이제 이건 확실히 잘 됩니다)
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

    # 2. 내 API 키가 쓸 수 있는 모델 목록 가져오기
    list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
    models_data = requests.get(list_url).json()
    
    # 1.5-flash 계열의 이름을 가진 모델 중 하나를 자동으로 선택
    actual_model_name = "models/gemini-1.5-flash" # 기본값
    try:
        for m in models_data.get('models', []):
            if 'gemini-1.5-flash' in m['name']:
                actual_model_name = m['name']
                break
    except:
        pass

    # 3. 찾은 모델 이름으로 요약 요청
    print(f"🎯 선택된 모델 이름: {actual_model_name}")
    url = f"https://generativelanguage.googleapis.com/v1beta/{actual_model_name}:generateContent?key={API_KEY}"
    
    payload = {
        "contents": [{
            "parts": [
                {"text": "12개 띠별 운세를 한 줄씩 짧게 요약해줘."},
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
        # 에러 시 어떤 모델 목록이 있었는지 상세히 출력 (디버깅용)
        available_names = [m['name'] for m in models_data.get('models', [])[:3]]
        fortune_text = f"실패 사유: {data.get('error', {}).get('message', '구조 에러')}\n사용 가능 목록: {available_names}"

    requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", 
                  json={"chat_id": CHAT_ID, "text": fortune_text})

if __name__ == "__main__":
    main()
