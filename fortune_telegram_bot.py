"""
띠별 운세 텔레그램 봇 (스크린샷 방식)
- Playwright로 네이버 띠별 운세 캡처
- Gemini Vision API로 분석
- 텔레그램으로 전송
"""

import os
import requests
import base64
from datetime import datetime
import time
import subprocess

def install_playwright():
    """Playwright 설치 및 브라우저 다운로드"""
    try:
        print("📦 Playwright 설치 중...")
        subprocess.run(["pip", "install", "playwright"], check=True)
        subprocess.run(["playwright", "install", "chromium"], check=True)
        subprocess.run(["playwright", "install-deps"], check=True)
        print("✅ Playwright 설치 완료")
    except Exception as e:
        print(f"❌ Playwright 설치 실패: {e}")
        raise


def capture_fortune_screenshot():
    """네이버 띠별 운세 스크린샷 캡처"""
    
    from playwright.sync_api import sync_playwright
    
    print("📸 네이버 띠별 운세 캡처 시작...")
    
    try:
        with sync_playwright() as p:
            # 브라우저 실행
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={'width': 1200, 'height': 2400})
            
            # 네이버 검색
            print("  → 페이지 로딩 중...")
            page.goto("https://search.naver.com/search.naver?query=띠별+운세")
            
            # 페이지 로딩 대기
            time.sleep(3)
            
            # 전체 페이지 스크린샷
            screenshot_bytes = page.screenshot(full_page=False)
            
            browser.close()
            
            # base64 인코딩
            img_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            print("✅ 스크린샷 캡처 완료")
            
            return img_base64
            
    except Exception as e:
        print(f"❌ 스크린샷 캡처 실패: {e}")
        raise


def analyze_with_gemini(img_base64):
    """Gemini Vision API로 운세 분석"""
    
    api_key = os.environ.get('GEMINI_API_KEY')
    today = datetime.now().strftime("%Y년 %m월 %d일")
    day_of_week = ['월', '화', '수', '목', '금', '토', '일'][datetime.now().weekday()]
    
    prompt = f"""이미지에서 12띠별 운세를 찾아서 각 띠별로 한 줄씩 요약해주세요.

오늘은 {today} {day_of_week}요일입니다.

형식:
🔮 {today} 띠별 운세

🐭 쥐띠: (핵심 내용 30자 이내) ✨
🐮 소띠: (핵심 내용 30자 이내) 💪
🐯 호랑이띠: (핵심 내용 30자 이내) 🔥
🐰 토끼띠: (핵심 내용 30자 이내) 🌸
🐲 용띠: (핵심 내용 30자 이내) ⚡
🐍 뱀띠: (핵심 내용 30자 이내) 🌟
🐴 말띠: (핵심 내용 30자 이내) 🎯
🐑 양띠: (핵심 내용 30자 이내) 🍀
🐵 원숭이띠: (핵심 내용 30자 이내) 🎪
🐔 닭띠: (핵심 내용 30자 이내) 🌅
🐶 개띠: (핵심 내용 30자 이내) 💫
🐷 돼지띠: (핵심 내용 30자 이내) 🎁

긍정적이고 간결하게! 정확히 위 형식으로만 답변하세요."""

    # Gemini 1.5 Flash 사용 (최신 모델)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {
                    "inline_data": {
                        "mime_type": "image/png",
                        "data": img_base64
                    }
                }
            ]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 800
        }
    }
    
    # 재시도 로직
    for i in range(3):
        try:
            print(f"🤖 Gemini Vision API 호출 중... (시도 {i+1}/3)")
            res = requests.post(url, json=payload, timeout=60)
            data = res.json()
            
            if 'candidates' in data:
                result = data['candidates'][0]['content']['parts'][0]['text'].strip()
                print("✅ Gemini 분석 완료!")
                return result
            
            elif 'error' in data:
                error_msg = data['error'].get('message', '')
                print(f"❌ API 오류: {error_msg}")
                
                if 'quota' in error_msg.lower() or 'resource' in error_msg.lower():
                    if i < 2:
                        wait_time = 60 + (i * 30)
                        print(f"⏳ {wait_time}초 대기 후 재시도...")
                        time.sleep(wait_time)
                    else:
                        raise Exception("할당량 초과")
                else:
                    raise Exception(error_msg)
        
        except Exception as e:
            print(f"❌ 요청 실패: {e}")
            if i < 2:
                time.sleep(30)
            else:
                raise
    
    raise Exception("Gemini API 호출 실패")


def send_telegram(message):
    """텔레그램 전송"""
    
    tg_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }
    
    try:
        print("📤 텔레그램 전송 중...")
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print("✅ 텔레그램 전송 완료!")
        return True
    except Exception as e:
        print(f"❌ 텔레그램 전송 실패: {e}")
        return False


def main():
    """메인 실행"""
    print("="*50)
    print(f"🌅 운세 봇 시작 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)
    
    try:
        # 0단계: Playwright 설치
        install_playwright()
        print()
        
        # 1단계: 스크린샷 캡처
        img_base64 = capture_fortune_screenshot()
        print()
        
        # 2단계: Gemini로 분석
        summary = analyze_with_gemini(img_base64)
        print(f"\n📝 최종 결과:\n{summary}\n")
        
        # 3단계: 텔레그램 전송
        send_telegram(summary)
        
        print("\n" + "="*50)
        print("🎉 모든 작업 완료!")
        print("📱 텔레그램 확인 후 Threads에 복붙하세요!")
        print("="*50)
        
    except Exception as e:
        error_msg = f"❌ 오류 발생: {str(e)}"
        print(error_msg)
        
        # 오류도 텔레그램으로 알림
        tg_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        if tg_token and chat_id:
            requests.post(
                f"https://api.telegram.org/bot{tg_token}/sendMessage",
                json={"chat_id": chat_id, "text": error_msg}
            )
        
        raise


if __name__ == "__main__":
    main()
