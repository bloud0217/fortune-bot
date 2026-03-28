import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
import time

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

def get_all_fortunes():
    """네이버 띠별 운세 통합 페이지에서 12개 띠 내용을 한 번에 수집"""
    url = "https://search.naver.com/search.naver?query=띠별+운세"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 12개 띠의 이름과 운세 텍스트가 담긴 리스트 추출
        items = soup.select('dl.lnb_fortune_lst dt, dl.lnb_fortune_lst dd')
        
        if not items:
            return "운세 데이터를 찾을 수 없습니다. (네이버 구조 변경 가능성)"

        text_result = ""
        for i in range(0, len(items), 2):
            zodiac = items[i].get_text(strip=True)
            content = items[i+1].get_text(strip=True)
            text_result += f"{zodiac}: {content}\n"
            
        return text_result
    except Exception as e:
        return f"크롤링 에러: {e}"

def summarize_with_gemini(raw_text):
    """Gemini를 사용하여 12개 띠 운세를 한 줄씩 예쁘게 요약"""
    today = datetime.now().strftime("%Y년 %m월 %d일")
    prompt = f"오늘 날짜: {today}\n다음은 네이버 띠별 운세 데이터야:\n{raw_text}\n\n이 내용을 바탕으로 각 띠별 핵심만 1줄 요약(이모지 포함)해서 '하나의 메시지'로 만들어줘. 제목은 🔮 오늘의 띠별 운세 요약 으로 해줘."

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        res = requests.post(url, json=payload, timeout=30)
        return res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
    except:
        return f"🔮 오늘의 운세\n\n{raw_text}"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, json=payload, timeout=10)

def main():
    print("🚀 통합 운세 수집 시작...")
    raw_data = get_all_fortunes()
    
    print("📝 Gemini 요약 중...")
    final_msg = summarize_with_gemini(raw_data)
    
    print("📤 전송 중...")
    send_telegram(final_msg)
    print("✅ 완료!")

if __name__ == "__main__":
    main()
