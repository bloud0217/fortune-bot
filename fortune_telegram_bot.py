import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
import time

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

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
    if not GEMINI_API_KEY: return f"🔮 {zodiac}띠 운세\n{fortune_text}"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
    payload = {"contents": [{"parts": [{"text": f"{zodiac}띠 운세 요약해줘: {fortune_text}"}]}]}
    try:
        res = requests.post(url, json=payload, timeout=30)
        return res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
    except Exception as e:
        print(f"⚠️ Gemini 요약 실패(원문전송): {e}")
        return f"🔮 {zodiac}띠 운세\n{fortune_text}"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        res = requests.post(url, json=payload, timeout=10)
        res_j = res.json()
        if res_j.get("ok"):
            print("✅ 전송 성공")
        else:
            print(f"❌ 전송 실패: {res_j.get('description')}")
    except Exception as e:
        print(f"❗ 네트워크 에러: {e}")

def main():
    zodiac_list = ["쥐", "소", "호랑이", "토끼", "용", "뱀", "말", "양", "원숭이", "닭", "개", "돼지"]
    for zodiac in zodiac_list:
        print(f"⏳ {zodiac}띠 처리 중...")
        fortune = get_naver_fortune(zodiac)
        summary = summarize_with_gemini(fortune, zodiac)
        send_telegram(summary)
        time.sleep(2)

if __name__ == "__main__":
    main()
