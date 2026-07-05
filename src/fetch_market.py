# -*- coding: utf-8 -*-
"""시장 데이터: KOSPI200 지수 + ETF 목록/강도."""
import os
import re
import sys

import naver

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

INDEX_URL = "https://m.stock.naver.com/api/index/KPI200/basic"
ETF_LIST_URL = "https://finance.naver.com/api/sise/etfItemList.nhn"

# 레버리지/인버스(파생) 판별 키워드
_LEV = re.compile(r"레버리지|인버스|2X|곱버스|3X")
# 국내 주식형 ETF 카테고리 (1=시장지수, 2=업종/테마, 3=파생)
_DOMESTIC_TABS = {1, 2, 3}


def fetch_index(session):
    """KOSPI200 지수 dict: {value, change, rate, up} 반환."""
    d = naver.get_json(session, INDEX_URL)
    if not isinstance(d, dict):
        return None
    code = (d.get("compareToPreviousPrice") or {}).get("code")
    return {
        "value": naver.to_float(d.get("closePrice")),
        "change": naver.to_float(d.get("compareToPreviousClosePrice")),
        "rate": naver.to_float(d.get("fluctuationsRatio")),
        "up": code == "2",
        "name": d.get("stockName") or "코스피 200",
    }


def fetch_etf_list(session, min_amount_eok=30):
    """국내 주식형 ETF 목록(유동성 필터). 각 항목에 leverage 플래그 포함."""
    d = naver.get_json(session, ETF_LIST_URL)
    try:
        lst = d["result"]["etfItemList"]
    except (TypeError, KeyError):
        return []
    out = []
    for e in lst:
        if e.get("etfTabCode") not in _DOMESTIC_TABS:
            continue
        name = e.get("itemname") or ""
        amt_eok = (e.get("amonut") or 0) / 100.0
        if amt_eok < min_amount_eok:
            continue
        is_lev = bool(_LEV.search(name)) or e.get("etfTabCode") == 3
        r3 = e.get("threeMonthEarnRate")
        out.append({
            "code": e.get("itemcode"),
            "name": name,
            "now": e.get("nowVal"),
            "change_rate": e.get("changeRate"),       # 일간 등락률(%)
            "rate3m": None if r3 is None else float(r3),  # 3개월 수익률(%)
            "amount_eok": round(amt_eok, 0),
            "leverage": is_lev,
        })
    return out


def theme_top(etf_list, top_n=6):
    """일반(비레버리지) 업종/테마 ETF 중 3개월 수익률 상위."""
    cand = [e for e in etf_list if not e["leverage"] and e["rate3m"] is not None
            and e["amount_eok"] >= 100]
    cand.sort(key=lambda x: x["rate3m"], reverse=True)
    return cand[:top_n]


if __name__ == "__main__":
    s = naver.make_session()
    print("지수:", fetch_index(s))
    etfs = fetch_etf_list(s)
    print(f"국내 ETF {len(etfs)}개 (레버리지 {sum(e['leverage'] for e in etfs)}개)")
    ups = sorted([e for e in etfs if e["change_rate"] is not None],
                 key=lambda x: x["change_rate"], reverse=True)
    print("일간 상승률 TOP5:")
    for e in ups[:5]:
        print(f"  {e['name'][:22]:<22} {e['change_rate']:>6.2f}%  3M {e['rate3m']}")
    print("일간 하락률 TOP5:")
    for e in ups[-5:]:
        print(f"  {e['name'][:22]:<22} {e['change_rate']:>6.2f}%")
