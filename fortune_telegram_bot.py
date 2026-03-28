import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
import time

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

def get_naver_fortune(zodiac):
    """네이버에서 실제 운세 텍스트를 뽑아내는 가장 확실한 방법"""
    # 검색어를 더 구체적으로 설정 (예: '쥐띠 오늘의 운세')
    url = f"https://search.naver.com/search.naver?query={zodiac}띠+오늘의+운세"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 방식 1: 상세 정보 박스(p.dsc) 직접 타겟팅
        content = soup.select_one('div.detail_info p.dsc')
        if content:
            return content.get_text(strip=True)
            
        # 방식 2: 다른 클래스명(api_txt_lines) 검색
        content_alt = soup.select_one('.api_txt_lines.dsc_txt')
        if content_alt:
            return content_alt.get_text(strip=True)
            
        # 방식 3: 텍스트가 포함된 div 전체에서 가장 긴 문장 찾기 (최후의 수단)
        texts = soup.select('.detail_info')
        if texts:
            return texts[0].get_text(" ", strip=True)

        return f"{zodiac}띠 운세 내용을 찾지 못했습니다."
    except Exception as e:
        return f"에러 발생: {str(e)}"

def summarize_all_with_gemini(all_fortunes):
    """12개 띠 운세를 하나의 메시지로 요약"""
    today = datetime.now().strftime("%Y년 %m월 %d일")
    
    # Gemini API가 없거나 에러날 경우 대비한 기본 메시지 구성
    default_msg = f"🔮 {today} 띠별 운세 요약\n\n" + "\n".join(all_fortunes)

    if not GEMINI_API_KEY:
        return default_msg

    prompt = (
        f"오늘 날짜: {today}\n"
        f"12개 띠 운세 원문: {all_fortunes}\n\n"
        "위 원문들을 바탕으로 텔레그램에 보낼 요약본을 만들어줘.\n"
        "형식:\n"
        "🔮 오늘의 띠별 운세 요약\n"
        "각 띠별로 [띠 이모지] [띠 이름]: [한 줄 핵심 요약]\n"
        "예시: 🐭 쥐띠: 뜻밖의 행운이 찾아오니 적극적으로 움직이세요.\n"
        "말투는 친절하고 희망차게 작성해줘."
    )

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        res = requests.post(url, json=payload, timeout=30)
        summary = res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        return summary
    except:
        return default_msg

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
