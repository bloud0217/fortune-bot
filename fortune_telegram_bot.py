import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
import time

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

def get_naver_fortune(zodiac):
    """네이버 모바일 버전 주소를 사용하여 더 정확하게 운세 크롤링"""
    zodiac_map = {"쥐": "84", "소": "85", "호랑이": "86", "토끼": "87", "용": "88", "뱀": "89", "말": "90", "양": "91", "원숭이": "92", "닭": "93", "개": "94", "돼지": "95"}
    
    # 더 안정적인 모바일 검색 결과 페이지 활용
    url = f"https://m.search.naver.com/search.naver?query={zodiac}띠+오늘의+운세"
    headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1'}
    
    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 실제 운세 텍스트가 들어있는 영역 추출
        content = soup.select_one('p.dsc')
        if content:
            return content.get_text(strip=True)
        
        # 대안 구조 탐색
        content_alt = soup.select_one('._cs_fortune_text')
        if content_alt:
            return content_alt.get_text(strip=True)
            
        return "운세 정보를 찾을 수 없습니다."
    except:
        return "데이터를 가져오는 중 오류가 발생했습니다."

def summarize_all_with_gemini(all_fortunes):
    """12개 띠 운세를 하나의 요약 메시지로 변환"""
    today = datetime.now().strftime("%Y년 %m월 %d일")
    
    if not GEMINI_API_KEY:
        # Gemini 키가 없을 경우 원문 합쳐서 반환
        return f"🔮 {today} 띠별 운세\n\n" + "\n".join(all_fortunes)

    prompt = (
        f"오늘 날짜: {today}\n"
        f"다음은 12개 띠의 운세 원문들입니다: {all_fortunes}\n\n"
        "위 내용을 바탕으로 다음 형식의 '하나의 메시지'를 작성해줘:\n"
        "1. 제목: 🔮 오늘의 띠별 운세 요약\n"
        "2. 내용: 각 띠별로 한 줄씩, 아주 핵심적인 내용만 이모지와 함께 요약 (예: 🐭 쥐띠: 금전운이 좋으니 적극적으로 움직이세요)\n"
        "3. 말투: 친절하고 긍정적인 말투로 작성할 것"
    )

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        res = requests.post(url, json=payload, timeout=30)
        return res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
    except:
        return f"🔮 {today} 띠별 운세 요약본을 만드는 데 실패했습니다.\n\n" + "\n".join(all_fortunes)

def send_telegram(message):
    """하나의 통합 메시지 전송"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, json=payload, timeout=10)

def main():
    zodiac_list = ["쥐", "소", "호랑이", "토끼", "용", "뱀", "말", "양", "원숭이", "닭", "개", "돼지"]
    results = []
    
    print("🚀 운세 수집 시작...")
    for zodiac in zodiac_list:
        print(f"gathering: {zodiac}")
        fortune = get_naver_fortune(zodiac)
        results.append(f"{zodiac}띠: {fortune}")
        time.sleep(1) # 차단 방지용 미세 지연

    print("📝 요약 및 전송 중...")
    all_text = "\n".join(results)
    final_message = summarize_all_with_gemini(all_text)
    send_telegram(final_message)
    print("✅ 전송 완료!")

if __name__ == "__main__":
    main()
