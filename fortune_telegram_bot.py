"""
띠별 운세 텔레그램 봇 (완전 무료 버전)
- 네이버 띠별 운세 크롤링
- Gemini API로 요약 (무료)
- 텔레그램으로 전송
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
import json
import time

# 환경 변수에서 가져오기 (GitHub Secrets에 저장됨)
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')
YOUR_ZODIAC = os.environ.get('YOUR_ZODIAC', '쥐')  # 기본값: 쥐띠


def get_naver_fortune(zodiac):
    """네이버에서 띠별 운세 크롤링"""
    
    zodiac_keywords = {
        "쥐": "쥐띠", "소": "소띠", "호랑이": "호랑이띠", "토끼": "토끼띠",
        "용": "용띠", "뱀": "뱀띠", "말": "말띠", "양": "양띠",
        "원숭이": "원숭이띠", "닭": "닭띠", "개": "개띠", "돼지": "돼지띠"
    }
    
    if zodiac not in zodiac_keywords:
        raise ValueError(f"올바른 띠를 입력하세요: {list(zodiac_keywords.keys())}")
    
    keyword = zodiac_keywords[zodiac]
    url = f"https://search.naver.com/search.naver?query={keyword}+오늘의+운세"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        print(f"🔍 크롤링 시작: {keyword}")
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 여러 선택자 시도
        fortune_text = None
        selectors = [
            'div.detail_info',
            'div.detail_txt', 
            'div.txt',
            'p.dsc',
            'div.api_cs_wrap',
            'span._text'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                # 의미있는 길이의 텍스트만 선택
                if len(text) > 30 and '운세' in text or '오늘' in text or zodiac in text:
                    fortune_text = text
                    print(f"✅ 선택자로 추출: {selector}")
                    break
            if fortune_text:
                break
        
        # 추출 실패 시 기본 메시지
        if not fortune_text or len(fortune_text) < 20:
            print("⚠️ 운세 추출 실패, 기본 메시지 사용")
            fortune_text = f"오늘도 {zodiac}띠에게 좋은 일이 가득할 거예요. 긍정적인 마음으로 하루를 시작하세요!"
        
        return fortune_text[:500]  # 최대 500자
            
    except Exception as e:
        print(f"❌ 크롤링 오류: {e}")
        return f"오늘도 {zodiac}띠에게 행운이 가득하길 바랍니다! 💫"


def summarize_with_gemini(fortune_text, zodiac):
    """Gemini API로 운세 한 줄 요약 + 이모지 추가"""
    
    today = datetime.now().strftime("%Y년 %m월 %d일")
    day_of_week = ['월', '화', '수', '목', '금', '토', '일'][datetime.now().weekday()]
    
    prompt = f"""다음은 {zodiac}띠의 오늘({today} {day_of_week}요일) 운세입니다:

{fortune_text}

이 운세를 다음 조건으로 요약해주세요:
1. 첫 줄: "🔮 {zodiac}띠 오늘의 운세 ({today[:11]})"
2. 두 번째 줄: 핵심 내용을 50-60자로 요약
3. 긍정적이고 힘이 나는 톤
4. 이모지 2-3개 적절히 포함

예시:
🔮 쥐띠 오늘의 운세 (2024년 03월 28일)
새로운 기회가 찾아올 날! 용기내서 도전해보세요 ✨💪

답변은 위 형식 그대로만 작성하고, 다른 설명은 추가하지 마세요."""

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 200,
            }
        }
        
        print("🤖 Gemini API 호출 중...")
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        if 'candidates' in result and len(result['candidates']) > 0:
            summary = result['candidates'][0]['content']['parts'][0]['text'].strip()
            print(f"✅ 요약 완료")
            return summary
        else:
            print("⚠️ Gemini 응답 형식 오류")
            return f"🔮 {zodiac}띠 오늘의 운세 ({today[:11]})\n{fortune_text[:60]}... 💫"
            
    except Exception as e:
        print(f"❌ Gemini API 오류: {e}")
        # Gemini 실패 시 기본 포맷으로 반환
        return f"🔮 {zodiac}띠 오늘의 운세 ({today[:11]})\n{fortune_text[:60]}... 💫"


def send_telegram(message):
    """텔레그램으로 메시지 전송"""
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
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
    """메인 실행 함수"""
    print("="*50)
    print(f"🌅 운세 봇 시작 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)
    
    # 환경 변수 확인
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY가 설정되지 않았습니다!")
        return
    if not TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN이 설정되지 않았습니다!")
        return
    if not TELEGRAM_CHAT_ID:
        print("❌ TELEGRAM_CHAT_ID가 설정되지 않았습니다!")
        return
    
    print(f"🐭 띠: {YOUR_ZODIAC}")
    print()
    
    # 1단계: 네이버 운세 크롤링
    fortune = get_naver_fortune(YOUR_ZODIAC)
    print(f"📄 크롤링 결과: {fortune[:100]}...")
    print()
    
    # 2단계: Gemini로 요약
    summary = summarize_with_gemini(fortune, YOUR_ZODIAC)
    print(f"📝 요약 결과:\n{summary}")
    print()
    
    # 3단계: 텔레그램 전송
    success = send_telegram(summary)
    
    if success:
        print()
        print("="*50)
        print("🎉 모든 작업 완료!")
        print("📱 텔레그램을 확인하고 Threads에 복붙하세요!")
        print("="*50)
    else:
        print()
        print("="*50)
        print("⚠️ 전송 실패 - 아래 내용을 직접 복사하세요:")
        print("="*50)
        print(summary)
        print("="*50)


if __name__ == "__main__":
    main()