import os, requests, base64, time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

def main():
    # 1. 환경 변수 설정
    api_key = os.environ.get('GEMINI_API_KEY')
    tg_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    # 2. 네이버 캡처
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1080,3000')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    try:
        driver.get("https://m.search.naver.com/search.naver?query=띠별+운세")
        time.sleep(15) 
        img_data = base64.b64encode(driver.get_screenshot_as_png()).decode('utf-8')
    finally:
        driver.quit()

    # 3. Gemini 요청 (v1 주소와 gemini-1.5-flash 모델명 고정)
    # 현재 성민님의 키 설정에 가장 적합한 경로입니다.
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [
                {"text": "이미지에 있는 12개 띠별 운세를 한 줄씩 짧게 요약해서 보내줘."},
                {"inline_data": {"mime_type": "image/png", "data": img_data}}
            ]
        }]
    }

    # 4. 결과 발송
    res = requests.post(url, json=payload)
    result = res.json()

    try:
        # 정상 응답 시 메시지 추출
        msg = result['candidates'][0]['content']['parts'][0]['text']
    except:
        # 실패 시 에러 사유 발송
        error_msg = result.get('error', {}).get('message', '알 수 없는 오류')
        msg = f"🔮 운세 요약 실패\n사유: {error_msg}"

    requests.post(f"https://api.telegram.org/bot{tg_token}/sendMessage", 
                  json={"chat_id": chat_id, "text": msg})

if __name__ == "__main__":
    main()
