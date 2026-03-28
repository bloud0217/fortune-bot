import os, requests, base64, time, sys, subprocess
from datetime import datetime

# [개선] 로깅 함수 (GitHub 로그에서 진행 상황 확인용)
def log(msg):
    print(f"[*] {msg} ({datetime.now().strftime('%H:%M:%S')})")
    sys.stdout.flush()

def install_playwright():
    """[최적화] GitHub Actions 환경에서 Playwright 및 브라우저 강제 설치"""
    try:
        log("📦 Playwright 및 Chromium 브라우저 설치 중...")
        # 이미 설치되어 있더라도 강제로 재설치하여 버전을 맞춥니다.
        subprocess.run(["pip", "install", "--upgrade", "playwright"], check=True)
        subprocess.run(["playwright", "install", "chromium"], check=True)
        log("✅ Playwright 설치 완료")
    except Exception as e:
        log(f"❌ Playwright 설치 실패 (무시하고 진행): {e}")

def capture_fortune():
    """[클로드 방식] Playwright를 이용한 정밀 모바일 캡처"""
    from playwright.sync_api import sync_playwright
    
    log("📸 네이버 운세 캡처 시작...")
    try:
        with sync_playwright() as p:
            # 브라우저 실행 (가장 가벼운 세팅)
            browser = p.chromium.launch(headless=True)
            # 모바일 뷰포트로 설정 (네이버 모바일 페이지가 분석하기 더 좋습니다)
            context = browser.new_context(viewport={'width': 450, 'height': 900})
            page = context.new_page()
            
            # 페이지 로딩 대기 시간을 넉넉히 줍니다.
            page.goto("https://m.search.naver.com/search.naver?query=띠별+운세", timeout=60000)
            time.sleep(10) # 페이지 안정화 대기
            
            # 스크린샷 캡처 (용량을 줄이기 위해 전체 페이지가 아닌 현재 화면만)
            screenshot_bytes = page.screenshot(full_page=False)
            browser.close()
            
            log("✅ 스크린샷 캡처 완료")
            return base64.b64encode(screenshot_bytes).decode('utf-8')
    except Exception as e:
        log(f"❌ 캡처 실패: {e}")
        raise

def analyze_gemini(img_base64):
    """[최적화] Gemini 2.0 Flash 사용 및 끈질긴 할당량 재시도"""
    api_key = os.environ.get('GEMINI_API_KEY')
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 프롬프트는 클로드의 구조를 유지하되 Gemini 2.0에 맞춰 최적화
    prompt = f"이미지에서 12띠별 운세를 찾아 '띠: 내용' 형식으로 한 줄씩 요약해줘. 날짜: {today}"

    # Gemini 2.0 Flash 호출 (더 빠르고 똑똑함)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": "image/png", "data": img_base64}}
            ]
        }],
        "generationConfig": {"temperature": 0.2} # 일관성을 위해 낮춤
    }

    log("🤖 Gemini 2.0 분석 요청 중...")
    
    # [핵심] 할당량 초과 시 3번까지 끈질기게 재시도 (대기 시간 늘림)
    for i in range(3):
        res = requests.post(url, json=payload, timeout=60)
        data = res.json()
        
        if 'candidates' in data:
            log("✅ Gemini 분석 완료!")
            return data['candidates'][0]['content']['parts'][0]['text'].strip()
        elif 'error' in data:
            err_msg = data['error'].get('message', '알 수 없는 에러')
            # 할당량 초과 시 대기 시간을 늘려가며 재시도 (60초 -> 90초)
            if 'quota' in err_msg.lower() or 'resource' in err_msg.lower():
                if i < 2:
                    wait_time = 60 + (i * 30)
                    log(f"⏳ 할당량 초과. {wait_time}초 대기 후 재시도({i+1}/3)...")
                    time.sleep(wait_time)
                    continue
                else:
                    return "🚨 현재 구글 무료 API 사용량이 꽉 찼습니다. 1시간 뒤에 다시 실행해주세요!"
            else:
                raise Exception(err_msg)
        else:
            raise Exception("올바르지 않은 API 응답 구조")

def send_telegram(msg):
    tg_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if not tg_token or not chat_id:
        log("❌ 텔레그램 환경 변수가 설정되지 않았습니다.")
        return

    log("📤 텔레그램 전송 중...")
    try:
        # 메시지가 너무 길면 잘라서 보냅니다.
        if len(msg) > 4000:
            msg = msg[:4000] + "..."
        requests.post(f"https://api.telegram.org/bot{tg_token}/sendMessage", 
                      json={"chat_id": chat_id, "text": msg}, timeout=10)
        log("✅ 텔레그램 전송 완료!")
    except Exception as e:
        log(f"❌ 텔레그램 전송 실패: {e}")

def main():
    log("="*50)
    log("🌅 운세 봇 시작")
    log("="*50)
    
    try:
        install_playwright()
        img = capture_fortune()
        result = analyze_gemini(img)
        send_telegram(result)
        log("🎉 모든 작업 성공!")
    except Exception as e:
        error_log = f"❌ 최종 실패: {str(e)}"
        log(error_log)
        # 실패하더라도 텔레그램으로 알림을 보냅니다.
        send_telegram(error_log)
        # GitHub Actions가 실패로 표시되도록 합니다.
        sys.exit(1)

if __name__ == "__main__":
    main()
