import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
import json
import time

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

def get_naver_fortune(zodiac):
    """네이버에서 실제 띠별 운세 텍스트 추출"""
    zodiac_keywords = {"쥐": "쥐띠", "소": "소띠", "호랑이": "호랑이띠", "토끼": "토끼띠", "용": "용띠", "뱀": "뱀띠", "말": "말띠", "양": "양띠", "원숭이": "원숭이띠", "닭": "닭띠", "개": "개띠", "돼지": "돼지띠"}
    keyword = zodiac_keywords[zodiac]
    url = f"https://search.naver.com/search.naver?query={keyword}+오늘의+운세"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 네이버 운세의 실제 텍스트가 담긴 여러 위치를 순차적으로 탐색
        fortune_text = ""
        # 1순위: 상세 설명 박스
        detail_text = soup.select_one('div.detail_info p.dsc')
        if detail_text:
            fortune_text = detail_text.get_text(strip=True)
        
        # 2순위: 다른 형태의 텍스트 박스 (구조 변경 대비)
        if not fortune_text:
            alt_text = soup.select_one('div.api_txt_lines.dsc_txt')
            if alt_text:
                fortune_text = alt_text.get_text(strip=True)

        if fortune_text and len(fortune_text) > 5:
            return fortune_text
        else:
            return f"{zodiac}띠의 상세 운세를 가져오는 데 실패했습니다. 잠시 후 다시 시도해 주세요."
            
    except Exception as e:
        return f"{zodiac}띠 운세 데이터를 가져오는 중 오류 발생: {str(e)}"

def summarize_with_gemini(fortune_text, zodiac):
    """Gemini를 사용해 운세를 요약 (실패 시 원문 전송)"""
    if not GEMINI_API_KEY or "실패" in fortune_text:
        return f"🔮 {zodiac}띠 오늘의 운세\n\n{fortune_text}"

    today = datetime.now().strftime("%Y년 %m월 %d일")
    prompt = f"다음은 {zodiac}띠의 오늘 운세 원문입니다: '{fortune_text}'. 이 내용을 바탕으로 🔮 {zodiac}띠 오늘의 운세 ({today}) 라는 제목 뒤에, 아주 친절하고 희망찬 말투로 핵심만 1줄 요약해서 알려줘. (반드시 원문의 내용을 포함할 것)"

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        response = requests.post(url, json=payload, timeout=30)
        result = response.json()
        summary = result['candidates'][0]['content']['parts'][0]['text'].strip()
        return summary
    except:
        return f"🔮 {zodiac}띠 오늘의 운세\n\n{fortune_text}"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, json=payload, timeout=10)

def main():
    zodiac_list = ["쥐", "소", "호랑이", "토끼", "용", "뱀", "말", "양", "원숭이", "닭", "개", "돼지"]
    for zodiac in zodiac_list:
        print(f"⏳ {zodiac}띠 데이터 수집 및 요약 중...")
        fortune = get_naver_fortune(zodiac)
        summary = summarize_with_gemini(fortune, zodiac)
        send_telegram(summary)
        time.sleep(2) # 텔레그램 도배 방지

if __name__ == "__main__":
    main()
