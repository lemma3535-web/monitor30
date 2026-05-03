#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import feedparser
import time
from datetime import datetime, timedelta
import urllib.parse

GEMINI_API_KEY = "AIzaSyDNk-zrPm-aMhnlQsOpn_U09JXyGUHTgDA"
TELEGRAM_TOKEN = "8468655095:AAH5hpnhtm45plMAwHeI2DtdF651Se-2XmI"
TELEGRAM_CHAT_ID = "352100442"

TARGETS = [
    {"name": "Donald Trump",        "sector": "코인/관세/방산/에너지"},
    {"name": "Elon Musk",           "sector": "AI/우주/로봇/에너지/바이오"},
    {"name": "Jensen Huang",        "sector": "AI/반도체/광반도체/양자"},
    {"name": "Jerome Powell",       "sector": "금리/달러/전체시장"},
    {"name": "Scott Bessent",       "sector": "관세/달러/무역정책"},
    {"name": "Satya Nadella",       "sector": "MS/클라우드/AI"},
    {"name": "Sundar Pichai",       "sector": "구글/AI"},
    {"name": "Tim Cook",            "sector": "애플/공급망"},
    {"name": "Mark Zuckerberg",     "sector": "메타/AI/VR"},
    {"name": "Andy Jassy",          "sector": "아마존/클라우드"},
    {"name": "Lisa Su",             "sector": "AMD/반도체"},
    {"name": "Sam Altman",          "sector": "OpenAI/AI"},
    {"name": "Jim Taiclet",         "sector": "록히드/방산"},
    {"name": "Greg Hayes",          "sector": "RTX/방산"},
    {"name": "Peter Beck",          "sector": "Rocket Lab/우주"},
    {"name": "Bill Gates",          "sector": "바이오/팬데믹/mRNA"},
    {"name": "Dave Ricks",          "sector": "엘리릴리/바이오"},
    {"name": "Albert Bourla",       "sector": "화이자/바이오"},
    {"name": "FDA Commissioner",    "sector": "FDA/바이오전체"},
    {"name": "BioNTech CEO",        "sector": "BioNTech/mRNA"},
    {"name": "Darren Woods",        "sector": "엑슨/에너지"},
    {"name": "Vicki Hollub",        "sector": "코노코/에너지"},
    {"name": "Joe Dominguez",       "sector": "원전/에너지"},
    {"name": "Jamie Dimon",         "sector": "JP모건/금융"},
    {"name": "David Solomon",       "sector": "골드만삭스/금융"},
    {"name": "Brian Moynihan",      "sector": "뱅크오브아메리카/금융"},
    {"name": "Brad Garlinghouse",   "sector": "리플/XRP/코인"},
    {"name": "Brian Armstrong",     "sector": "코인베이스/코인"},
    {"name": "Cathie Wood",         "sector": "ARK/혁신주"},
    {"name": "Mary Barra",          "sector": "GM/전기차"},
]

KOREA_MAPPING = {
    "Jensen Huang":     "한미반도체, 우리로, 파이버프로, 리노공업",
    "Elon Musk":        "레인보우로보틱스, 쎄트렉아이, 에코프로비엠",
    "Donald Trump":     "한화에어로, LIG넥스원, 우리기술투자",
    "Bill Gates":       "SK바이오사이언스, 유바이오로직스",
    "Dave Ricks":       "한미약품, 유한양행, 에이비엘바이오",
    "Albert Bourla":    "한미약품, 삼성바이오로직스",
    "FDA Commissioner": "한국 바이오 전체",
    "BioNTech CEO":     "SK바이오사이언스",
    "Jim Taiclet":      "한화에어로, LIG넥스원, 현대로템",
    "Greg Hayes":       "한화에어로, LIG넥스원",
    "Peter Beck":       "쎄트렉아이, AP위성, 한화시스템",
    "Brad Garlinghouse":"우리기술투자, 갤럭시아머니트리",
    "Satya Nadella":    "클라우드/AI SW 관련주",
    "Sam Altman":       "AI 관련주 전체",
    "Lisa Su":          "한미반도체, 리노공업",
}

def fetch_news(person_name):
    since = datetime.now() - timedelta(hours=24)
    results = []
    try:
        query = urllib.parse.quote(f'"{person_name}"')
        url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]:
            pub = entry.get("published_parsed")
            if pub:
                pub_dt = datetime(*pub[:6])
                if pub_dt >= since:
                    results.append({
                        "title": entry.get("title", ""),
                        "summary": entry.get("summary", "")[:300],
                        "published": pub_dt.strftime("%Y-%m-%d %H:%M"),
                    })
    except Exception as e:
        print(f"[error] {person_name}: {e}")
    return results

def analyze_with_gemini(person, news_list):
    if not news_list:
        return {"has_news": False, "summary": "발언 없음", "importance": 0,
                "direction": "없음", "korea_sector": "", "action": ""}
    
    news_text = "\n".join([f"- [{n['published']}] {n['title']}\n  {n['summary']}" for n in news_list])
    
    prompt = f"""You are a Korean stock market analyst. Analyze news about {person['name']} ({person['sector']}).

News:
{news_text}

Output ONLY this JSON in Korean language (summary must be in Korean):
{{"has_news": true, "summary": "한국어로 핵심 발언 요약 2줄", "importance": 1~10 숫자만, "direction": "긍정 또는 부정 또는 중립", "korea_sector": "한국 영향 섹터 한국어로", "action": "매수검토 또는 매도검토 또는 관망"}}

Rules:
- summary MUST be written in Korean
- importance: investment/contract=8-10, CEO statement=5-7, mention=1-4
- Output only JSON, no other text"""

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 500}
        }
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        text = text.strip().replace("```json", "").replace("```", "").strip()
        result = json.loads(text)
        result["has_news"] = True
        return result
    except Exception as e:
        print(f"[gemini error] {person['name']}: {e}")
        return {"has_news": True, "summary": news_list[0]["title"],
                "importance": 0, "direction": "알수없음", "korea_sector": "", "action": "관망"}

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}, timeout=10).raise_for_status()
        print("[telegram] sent")
    except Exception as e:
        print(f"[telegram error] {e}")

def run_briefing():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 브리핑 시작")
    results = []
    for i, person in enumerate(TARGETS):
        print(f"[{i+1:02d}/30] {person['name']}")
        news = fetch_news(person["name"])
        analysis = analyze_with_gemini(person, news)
        results.append({"person": person, "news": news, "analysis": analysis})
        time.sleep(2)

    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    has_news = [r for r in results if r["analysis"]["has_news"]]
    no_news  = [r for r in results if not r["analysis"]["has_news"]]

    msg = (f"📊 <b>[30인 모닝 브리핑] {today}</b>\n"
           f"📅 {yesterday} 08:00 ~ {today} 08:00\n"
           f"✅ 발언있음: {len(has_news)}인 | ❌ 없음: {len(no_news)}인\n"
           f"{'─'*30}\n")

    for r in has_news:
        a = r["analysis"]
        name = r["person"]["name"]
        imp  = a.get("importance", 0)
        d    = a.get("direction", "")
        korea = KOREA_MAPPING.get(name, a.get("korea_sector", ""))
        emoji = {"긍정": "📈", "부정": "📉", "중립": "➡️"}.get(d, "❓")
        stars = "⭐" * min(imp, 5) if imp > 0 else ""
        msg += f"\n👤 <b>{name}</b> ({r['person']['sector']})\n"
        msg += f"{emoji} {a.get('summary', '')}\n"
        msg += f"{stars} {imp}/10 | {a.get('action', '')}\n"
        if korea:
            msg += f"🇰🇷 {korea}\n"
        msg += f"{'─'*30}\n"

    if no_news:
        msg += f"\n❌ <b>발언없음</b>\n{', '.join([r['person']['name'] for r in no_news])}\n"

    for i in range(0, len(msg), 4000):
        send_telegram(msg[i:i+4000])
        time.sleep(1)
    print("[완료]")

if __name__ == "__main__":
    run_briefing()
