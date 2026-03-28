import os, requests, base64, time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

def main():
    # 1. 네이버 캡처
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--window-size=1080,3000')
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    driver.get("https://m.search.naver.com/search.naver?query=띠별+운세")
    time.sleep(10)
    img_data = base64.b64encode(driver.get_screenshot_as_png()).decode('utf-8')
    driver.quit()

    # 2. Gemini에게 전달 (새로 발급받은 키가 적용됨)
    api_key = os.environ.get('GEMINI_API_KEY')
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [
                {"text": "사진 속 12개 띠의 운세를 한 줄씩 요약해줘."},
                {"inline_data": {"mime_type": "image/png", "data": img_data}}
            ]
        }]
    }

    res = requests.post(url, json=payload)
    result = res.json()

    # 3. 텔레그램 발송
    msg = result['candidates'][0]['content']['parts'][0]['text'] if 'candidates' in result else f"에러: {result}"
    requests.post(f"https://api.telegram.org/bot{os.environ.get('TELEGRAM_BOT_TOKEN')}/sendMessage", 
                  json={"chat_id": os.environ.get('TELEGRAM_CHAT_ID'), "text": msg})

if __name__ == "__main__":
    main()
