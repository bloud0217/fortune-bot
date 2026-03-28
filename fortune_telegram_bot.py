import os, requests, base64, time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def main():
    api_key = os.environ.get('GEMINI_API_KEY')
    tg_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    # 1. 브라우저 안정성 강화 (가장 가벼운 설정)
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.get("https://m.search.naver.com/search.naver?query=띠별+운세")
        time.sleep(15)
        img_data = base64.b64encode(driver.get_screenshot_as_png()).decode('utf-8')
        driver.quit()
    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{tg_token}/sendMessage", 
                      json={"chat_id": chat_id, "text": f"❌ 브라우저 실행 실패: {str(e)}"})
        return

    # 2. 할당량 초과 대응을 위한 재시도 로직
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [
            {"text": "12개 띠의 운세를 '띠: 요약' 형태로 한 줄씩 알려줘."},
            {"inline_data": {"mime_type": "image/png", "data": img_data}}
        ]}]
    }

    for i in range(2): # 할당량 문제 대비 최대 2번 시도
        res = requests.post(url, json=payload)
        data = res.json()
        
        if 'candidates' in data:
            result_msg = data['candidates'][0]['content']['parts'][0]['text']
            break
        elif 'error' in data and 'quota' in data['error']['message'].lower():
            print("⏳ 할당량 초과. 40초 대기 후 재시도...")
            time.sleep(40)
            continue
        else:
            result_msg = f"❌ AI 단계 오류: {data.get('error', {}).get('message', '알 수 없는 오류')}"
            break

    # 3. 최종 전송
    requests.post(f"https://api.telegram.org/bot{tg_token}/sendMessage", 
                  json={"chat_id": chat_id, "text": result_msg})

if __name__ == "__main__":
    main()
