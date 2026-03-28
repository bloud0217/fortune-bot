import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
import json
import time

# 환경 변수
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

def get_naver_fortune(zodiac):
    zodiac_keywords = {"쥐": "쥐띠", "소": "소띠", "호랑이": "호랑이띠", "토끼": "토끼띠", "용": "용띠", "뱀": "뱀띠", "말": "말띠", "양": "양띠", "원숭이": "원숭이띠", "닭": "닭띠", "개": "개띠", "돼지": "돼지띠"}
    keyword = zodiac_keywords[zodiac]
    url = f"https://search.naver.com/search.naver?query={keyword}+오늘의+운세"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        fortune_text = soup.select_one('div.detail_info p.dsc')
        return fortune_text.get_text(strip=True) if fortune_text else f"{zodiac}띠 행운 가득한 날 되세요!"
    except:
        return f"{zodiac}띠 화이팅!"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.post(url, json=payload, timeout=10)
        res_json = response.json()
        if res_json.get("ok"):
            print(f"✅ 전송 성공!")
        else:
            # 여기서 진짜 에러 이유를 로그에 찍습니다.
            print(f"❌ 전송 실패! 에러 내용: {res_json.get('description')}")
            print(f"💡 현재 사용 중인 CHAT_ID: {TELEGRAM_CHAT_ID}")
        return res_json.get("ok")
    except Exception as e:
        print(f"❗ 네트워크 에러: {e}")
        return False

def main():
    print("="*50)
    print(f"🚀 디버깅 모드 시작 - {datetime.now()}")
    
    if not all([TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
        print("❌ 설정값이 없습니다. Secrets를 확인하세요.")
        return

    # 테스트를 위해 '쥐띠' 하나만 먼저 보내봅니다.
    print(f"⏳ 테스트 전송 시작 (쥐띠)...")
    fortune = get_naver_fortune("쥐")
    send_telegram(f"🔮 테스트 메시지:\n{fortune}")
    
    print("="*50)

if __name__ == "__main__":
    main()
