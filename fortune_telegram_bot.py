import os, requests, base64, time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def main():
    api_key = os.environ.get('GEMINI_API_KEY')
    tg_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    # 변수 초기화 (에러 방지용)
    result_msg = "⚠️ 운세 분석 프로세스 실패"

    # 1. 브라우저 및 캡처
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.get("https://m.search.naver.com/search.naver?query=띠별+운세")
        time.sleep(15)
        img_data = base64.b64encode(driver.get_screenshot_as_png()).decode('utf-8')
        driver.quit()
    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{tg_token}/sendMessage", 
                      json={"chat_id": chat_id, "text": f"❌ 브라우저 실패: {str(e)}"})
        return

    # 2. Gemini 2.0 호출 및 할당량 재시도 (더 긴 대기시간 적용)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [
            {"text": "12개 띠의 운세를 한 줄씩 짧게 알려줘."},
            {"inline_data": {"mime_type": "image/png", "data": img_data}}
        ]}]
    }

    for i in range(3): # 최대 3번 시도
        res = requests.post(url, json=payload)
        data = res.json()
        
        if 'candidates' in data:
            result_msg = data['candidates'][0]['content']['parts'][0]['text']
            break
        elif 'error' in data and 'quota' in data['error']['message'].lower():
            # 할당량 초과 시 대기 시간을 늘려가며 재시도 (60초 -> 90초)
            wait_time = 60 + (i * 30)
            print(f"⏳ 할당량 초과. {wait_time}초 대기 후 재시도({i+1}/3)...")
            time.sleep(wait_time)
        else:
            result_msg = f"❌ AI 단계 오류: {data.get('error', {}).get('message', '알 수 없는 오류')}"
            break

    # 3. 텔레그램 전송 (어떤 상황에서도 메시지를 보냅니다)
    requests.post(f"https://api.telegram.org/bot{tg_token}/sendMessage", 
                  json={"chat_id": chat_id, "text": result_msg})

if __name__ == "__main__":
    main()
