# -*- coding: utf-8 -*-
"""시장 데이터: KOSPI200 지수 + 테마 ETF 강도."""
import os
import re
import sys

import naver

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

INDEX_URL = "https://m.stock.naver.com/api/index/KPI200/basic"
ETF_LIST_URL = "https://finance.naver.com/api/sise/etfItemList.nhn"

# 테마 ETF에서 제외할 파생/단일종목 키워드
_EXCLUDE = re.compile(r"레버리지|인버스|2X|곱버스|단일종목|선물")


def fetch_index(session):
    """KOSPI200 지수 dict: {value, change, rate, up} 반환."""
    d = naver.get_json(session, INDEX_URL)
    if not isinstance(d, dict):
        return None
    code = ((d.get("compareToPreviousPrice") or {}).get("code"))
    return {
        "value": naver.to_float(d.get("closePrice")),
        "change": naver.to_float(d.get("compareToPreviousClosePrice")),
        "rate": naver.to_float(d.get("fluctuationsRatio")),
        "up": code == "2",  # 2=상승, 5=하락
        "name": d.get("stockName") or "코스피 200",
    }


def fetch_theme_etfs(session, top_n=6, min_amount_eok=100):
    """국내 테마/업종 ETF 중 누적수익률(3개월) 상위 top_n 반환."""
    d = naver.get_json(session, ETF_LIST_URL)
    try:
        lst = d["result"]["etfItemList"]
    except (TypeError, KeyError):
        return []
    cand = []
    for e in lst:
        if e.get("etfTabCode") != 2:               # 2 = 국내 업종/테마
            continue
        name = e.get("itemname") or ""
        if _EXCLUDE.search(name):
            continue
        amt_eok = (e.get("amonut") or 0) / 100.0    # 거래대금(억)
        if amt_eok < min_amount_eok:
            continue
        rate3m = e.get("threeMonthEarnRate")
        if rate3m is None:
            continue
        cand.append({
            "code": e.get("itemcode"),
            "name": name,
            "rate3m": float(rate3m),
            "amount_eok": amt_eok,
            "change_rate": e.get("changeRate"),
        })
    cand.sort(key=lambda x: x["rate3m"], reverse=True)
    return cand[:top_n]


if __name__ == "__main__":
    s = naver.make_session()
    print("지수:", fetch_index(s))
    print("테마 ETF TOP6:")
    for e in fetch_theme_etfs(s):
        print(f"  {e['name'][:24]:<24} 3M {e['rate3m']:>7.2f}%  거래대금 {e['amount_eok']:>7.0f}억")
