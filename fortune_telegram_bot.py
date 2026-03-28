import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
import time

# 환경 변수 확인용 출력 (Secrets 값이 잘 로드되는지 확인)
print("--- 환경 변수 로드 확인 ---")
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')
print(f"BOT_TOKEN 존재 여부: {bool(TELEGRAM_BOT_TOKEN)}")
print(f"CHAT_ID: {TELEGRAM_CHAT_ID}")
print("--------------------------")

def get_naver_fortune(zodiac):
    url = f"https://search.naver.com/search.naver?query={zodiac}띠+오늘의+운세"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        text = soup.select_one('div.detail_info p.dsc')
        return text.get_text(strip=True) if text else f"{zodiac}띠 행운 가득하세요!"
    except:
        return f"{zodiac}띠 화이팅!"

def summarize_with_gemini(fortune_text, zodiac):
    if not GEMINI_API_KEY: 
        return f"🔮 {zodiac}띠 운세\n{fortune_text}"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
    payload = {"contents": [{"parts": [{"text": f"{zodiac}띠 운세 요약해줘: {fortune_text}"}]}]}
    try:
        res = requests.post(url, json=payload, timeout=30)
        return res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
    except Exception as e:
        print(f"⚠️ Gemini 요약 실패: {e}")
        return f"🔮 {zodiac}띠 운세\n{fortune_text}"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        res = requests.post(url, json=payload, timeout=10)
        print(f"텔레그램 응답: {res.json().get('ok')}")
    except Exception as e:
        print(f"❗ 전송 에러: {e}")

def main():
    print(f"🚀 실행 시간: {datetime.now()}")
    zodiac_list = ["쥐", "소", "호랑이", "토끼", "용", "뱀", "말", "양", "원숭이", "닭", "개", "돼지"]
    for zodiac in zodiac_list:
        print(f"⏳ {zodiac}띠 처리 중...")
        fortune = get_naver_fortune(zodiac)
        summary = summarize_with_gemini(fortune, zodiac)
        send_telegram(summary)
        time.sleep(2)
    print("✅ 모든 작업 완료")

if __name__ == "__main__":
    main()
