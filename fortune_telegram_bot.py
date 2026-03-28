import os, requests, base64, time, sys, subprocess
from datetime import datetime

def log(msg):
    print(f"[*] {msg} ({datetime.now().strftime('%H:%M:%S')})")
    sys.stdout.flush()

def install_playwright():
    try:
        log("📦 Playwright 설치 중...")
        subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    except Exception as e:
        log(f"⚠️ 설치 알림: {e}")

def capture_fortune():
    from playwright.sync_api import sync_playwright
    log("📸 캡처 시작...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={'width': 450, 'height': 800})
            page.goto("https://m.search.naver.com/search.naver?query=띠별+운세", timeout=60000)
            time.sleep(10)
            img_bytes = page.screenshot()
            browser.close()
            return base64.b64encode(img_bytes).decode('utf-8')
    except Exception as e:
        raise Exception(f"캡처 실패: {e}")

def analyze_gemini(img_base64):
    api_key = os.environ.get('GEMINI_API_KEY')
    # [수정] 가장 안정적인 호출 경로와 모델명 사용
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [
                {"text": "이미지 속 12띠 운세를 '띠: 요약' 형식으로 작성해줘."},
                {"inline_data": {"mime_type": "image/png", "data": img_base64}}
            ]
        }]
    }

    for i in range(2): # 할당량 문제 대비 2번 시도
        res = requests.post(url, json=payload)
        data = res.json()
        if 'candidates' in data:
            return data['candidates'][0]['content']['parts'][0]['text']
        elif 'error' in data:
            if 'quota' in str(data).lower():
                log("⏳ 할당량 초과... 60초 대기 후 재시도")
                time.sleep(60)
                continue
            return f"AI 에러: {data['error'].get('message')}"
    return "🚨 할당량 초과로 분석 실패"

def main():
    try:
        install_playwright()
        img = capture_fortune()
        result = analyze_gemini(img)
        
        token = os.environ.get('TELEGRAM_BOT_TOKEN')
        chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                      json={"chat_id": chat_id, "text": result})
        log("🎉 완료")
    except Exception as e:
        log(f"❌ 실패: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
