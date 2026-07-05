# -*- coding: utf-8 -*-
"""Naver 금융 공통 HTTP 유틸 및 파싱 헬퍼."""
import re
import sys
import time

import requests

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.dirname(__file__)))
import config


def make_session():
    s = requests.Session()
    s.headers.update({
        "User-Agent": config.USER_AGENT,
        "Referer": "https://m.stock.naver.com/",
        "Accept": "application/json, text/plain, */*",
    })
    return s


def get_json(session, url):
    """JSON GET (재시도 포함). 실패 시 None."""
    for attempt in range(config.RETRY):
        try:
            r = session.get(url, timeout=config.REQUEST_TIMEOUT)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        time.sleep(config.RETRY_BACKOFF * (attempt + 1))
    return None


def get_text(session, url, encoding="euc-kr"):
    """HTML/텍스트 GET (재시도 포함). 실패 시 None."""
    for attempt in range(config.RETRY):
        try:
            r = session.get(url, timeout=config.REQUEST_TIMEOUT)
            if r.status_code == 200:
                r.encoding = encoding
                return r.text
        except Exception:
            pass
        time.sleep(config.RETRY_BACKOFF * (attempt + 1))
    return None


# ---- 숫자 파싱 헬퍼 ----
def to_float(text):
    """'25.02배', '10.85', '-9.06', '1,234' -> float. 실패 시 None."""
    if text is None:
        return None
    s = str(text).strip()
    if s in ("", "-", "N/A", "null"):
        return None
    m = re.search(r"-?\d[\d,]*\.?\d*", s)
    if not m:
        return None
    try:
        return float(m.group(0).replace(",", ""))
    except ValueError:
        return None


def market_value_to_eok(text):
    """'1,809조 4,232억' -> 억원 단위 float. '4,232억' / '5,000억' 형태도 처리."""
    if not text:
        return None
    jo = re.search(r"([\d,]+)\s*조", text)
    eok = re.search(r"([\d,]+)\s*억", text)
    total = 0.0
    got = False
    if jo:
        total += float(jo.group(1).replace(",", "")) * 10000
        got = True
    if eok:
        total += float(eok.group(1).replace(",", ""))
        got = True
    return total if got else None
