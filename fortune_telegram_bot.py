"""
띠별 운세 텔레그램 봇 (개선된 버전)
- BeautifulSoup으로 간단하고 안정적인 크롤링
- Gemini API로 요약 (텍스트 입력이라 할당량 절약)
- 텔레그램으로 전송
"""

import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time

def get_all_zodiac_fortunes():
    """네이버에서 12띠 운세 한번에 크롤링"""
    
    zodiacs = ["쥐", "소", "호랑이", "토끼", "용", "뱀", "말", "양", "원숭이", "닭", "개", "돼지"]
    fortune_data = {}
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    print("🔍 12띠 운세 크롤링 시작...")
    
    for zodiac in zodiacs:
        try:
            url = f"https://search.naver.com/search.naver?query={zodiac}띠+오늘의+운세"
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 운세 텍스트 추출
            fortune_text = None
            selectors = [
                'div.detail_info',
                'div.detail_txt', 
                'div.txt',
                'p.dsc',
                'div.api_cs_wrap'
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text(strip=True)
                    if len(text) > 30:
                        fortune_text = text[:200]  # 200자로 제한
                        break
                if fortune_text:
                    break
            
            if not fortune_text:
                fortune_text = f"{zodiac}띠에게 좋은 하루가 될 거예요!"
            
            fortune_data[zodiac] = fortune_text
            print(f"  ✅ {zodiac}띠 완료")
            time.sleep(0.5)  # 서버 부하 방지
            
        except Exception as e:
            print(f"  ⚠️ {zodiac}띠 실패: {e}")
            fortune_data[zodiac] = f"{zodiac}띠에게 행운이 가득하길!"
    
    return fortune_data


def summarize_with_gemini(fortune_data):
    """Gemini로 12띠 운세 요약"""
    
    api_key = os.environ.get('GEMINI_API_KEY')
    today = datetime.now().strftime("%Y년 %m월 %d일")
    day_of_week = ['월', '화', '수', '목', '금', '토', '일'][datetime.now().weekday()]
    
    # 12띠 운세 텍스트 합치기
    fortune_text = ""
    for zodiac, content in fortune_data.items():
        fortune_text += f"{zodiac}띠: {content}\n\n"
    
    prompt = f"""다음은 {today} {day_of_week}요일의 12띠 운세입니다:

{fortune_text}

각 띠별로 핵심만 한 줄씩 요약해주세요.
형식:
🔮 {today} 띠별 운세

🐭 쥐띠: (30자 이내로 요약) ✨
🐮 소띠: (30자 이내로 요약) 💪
🐯 호랑이띠: (30자 이내로 요약) 🔥
🐰 토끼띠: (30자 이내로 요약) 🌸
🐲 용띠: (30자 이내로 요약) ⚡
🐍 뱀띠: (30자 이내로 요약) 🌟
🐴 말띠: (30자 이내로 요약) 🎯
🐑 양띠: (30자 이내로 요약) 🍀
🐵 원숭이띠: (30자 이내로 요약) 🎪
🐔 닭띠: (30자 이내로 요약) 🌅
🐶 개띠: (30자 이내로 요약) 💫
🐷 돼지띠: (30자 이내로 요약) 🎁

긍정적이고 간결하게! 이모지 각 1개씩만."""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 500
        }
    }
    
    # 할당량 초과 대비 재시도
    for i in range(3):
        try:
            print(f"🤖 Gemini API 호출 중... (시도 {i+1}/3)")
            res = requests.post(url, json=payload, timeout=30)
            data = res.json()
            
            if 'candidates' in data:
                result = data['candidates'][0]['content']['parts'][0]['text'].strip()
                print("✅ Gemini 요약 완료!")
                return result
            
            elif 'error' in data:
                error_msg = data['error'].get('message', '')
                
                if 'quota' in error_msg.lower() or 'resource' in error_msg.lower():
                    wait_time = 60 + (i * 30)
                    print(f"⏳ 할당량 초과. {wait_time}초 대기 후 재시도...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ API 오류: {error_msg}")
                    break
        
        except Exception as e:
            print(f"❌ 요청 실패: {e}")
            if i < 2:
                time.sleep(30)
    
    # Gemini 실패 시 기본 포맷으로 반환
    print("⚠️ Gemini 실패, 기본 포맷 사용")
    result = f"🔮 {today} 띠별 운세\n\n"
    emoji_map = {
        "쥐": "🐭", "소": "🐮", "호랑이": "🐯", "토끼": "🐰",
        "용": "🐲", "뱀": "🐍", "말": "🐴", "양": "🐑",
        "원숭이": "🐵", "닭": "🐔", "개": "🐶", "돼지": "🐷"
    }
    
    for zodiac, content in fortune_data.items():
        emoji = emoji_map.get(zodiac, "⭐")
        short = content[:30] + "..." if len(content) > 30 else content
        result += f"{emoji} {zodiac}띠: {short}\n"
    
    return result


def send_telegram(message):
    """텔레그램 전송"""
    
    tg_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
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
    """메인 실행"""
    print("="*50)
    print(f"🌅 운세 봇 시작 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)
    
    try:
        # 1단계: 12띠 운세 크롤링
        fortune_data = get_all_zodiac_fortunes()
        print(f"\n✅ {len(fortune_data)}개 띠 크롤링 완료\n")
        
        # 2단계: Gemini로 요약
        summary = summarize_with_gemini(fortune_data)
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
        
        # 오류 발생해도 텔레그램으로 알림
        tg_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        if tg_token and chat_id:
            requests.post(
                f"https://api.telegram.org/bot{tg_token}/sendMessage",
                json={"chat_id": chat_id, "text": error_msg}
            )


if __name__ == "__main__":
    main()
