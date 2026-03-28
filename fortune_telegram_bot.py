import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
import json
import time

# 환경 변수 (GitHub Secrets에 저장된 값 사용)
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

def get_naver_fortune(zodiac):
    """네이버에서 띠별 운세 크롤링"""
    zodiac_keywords = {
        "쥐": "쥐띠", "소": "소띠", "호랑이": "호랑이띠", "토끼": "토끼띠",
        "용": "용띠", "뱀": "뱀띠", "말": "말띠", "양": "양띠",
        "원숭이": "원숭이띠", "닭": "닭띠", "개": "개띠", "돼지": "돼지띠"
    }
    keyword = zodiac_keywords[zodiac]
    url = f"https://search.naver.com/search.naver?query={keyword}+오늘의+운세"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        fortune_text = soup.select_one('div.detail_info p.dsc')
        return fortune_text.get_text(strip=True) if fortune_text else f"오늘도 {zodiac}띠에게 행운이 가득하길!"
    except:
        return f"{zodiac}띠 화이팅!"

def summarize_with_gemini(fortune_text, zodiac):
    """Gemini API로 요약"""
    today = datetime.now().strftime("%Y년 %m월 %d일")
    prompt = f"다음은 {zodiac}띠의 오늘 운세입니다: {fortune_text}\n\n1. 첫 줄: 🔮 {zodiac}띠 오늘의 운세 ({today})\n2. 두 번째 줄: 핵심 1줄 요약 (이모지 포함)\n형식에 맞춰 짧게 답하세요."
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        response = requests.post(url, json=payload, timeout=30)
        result = response.json()
        return result['candidates'][0]['content']['parts'][0]['text'].strip()
    except:
        return f"🔮 {zodiac}띠 오늘의 운세\n{fortune_text[:60]}... 💫"

def send_telegram(message):
    """텔레그램 전송"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, json=payload, timeout=10)

def main():
    print("="*50)
    print(f"🌅 전 띠 운세 봇 가동 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)
    
    zodiac_list = ["쥐", "소", "호랑이", "토끼", "용", "뱀", "말", "양", "원숭이", "닭", "개", "돼지"]
    for zodiac in zodiac_list:
        print(f"⏳ {zodiac}띠 전송 중...")
        fortune = get_naver_fortune(zodiac)
        summary = summarize_with_gemini(fortune, zodiac)
        send_telegram(summary)
        time.sleep(1.5)  # 전송 제한 방지

    print("="*50)
    print("🎉 모든 띠 전송 완료!")

if __name__ == "__main__":
    main()
