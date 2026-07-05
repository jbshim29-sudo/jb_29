# -*- coding: utf-8 -*-
"""종목별 재무지표 수집: PER/PBR/EPS/시가총액/업종 + 영업이익/ROE (finance/annual)."""
import re

import naver

INTEGRATION_URL = "https://m.stock.naver.com/api/stock/{code}/integration"
ANNUAL_URL = "https://m.stock.naver.com/api/stock/{code}/finance/annual"
GROUP_URL = "https://finance.naver.com/sise/sise_group.naver?type=upjong"


def fetch_industry_map(session):
    """업종코드 -> 업종명 딕셔너리 (1회 요청)."""
    html = naver.get_text(session, GROUP_URL)
    if not html:
        return {}
    pairs = re.findall(
        r'sise_group_detail\.naver\?type=upjong&no=(\d+)"[^>]*>([^<]+)</a>', html
    )
    return {no: name.strip() for no, name in pairs}


def _totalinfo_map(integration):
    """totalInfos 리스트 -> {code: value} 딕셔너리."""
    out = {}
    for item in integration.get("totalInfos") or []:
        out[item.get("code")] = item.get("value")
    return out


def _latest_actual(finance_info):
    """trTitleList에서 확정(isConsensus=N) 실적 중 최신 2개 key 반환 (최신, 직전)."""
    titles = (finance_info or {}).get("trTitleList") or []
    actual = [t["key"] for t in titles if t.get("isConsensus") == "N"]
    # trTitleList는 과거->미래 순서. 확정 실적의 마지막이 최신.
    if not actual:
        return None, None
    latest = actual[-1]
    prev = actual[-2] if len(actual) >= 2 else None
    return latest, prev


def _row_value(finance_info, row_title, key):
    for row in (finance_info or {}).get("rowList") or []:
        if row.get("title") == row_title:
            col = (row.get("columns") or {}).get(key)
            if col:
                return naver.to_float(col.get("value"))
    return None


def fetch_one(session, code, name, industry_map):
    """단일 종목의 지표 dict 반환."""
    rec = {
        "code": code, "name": name,
        "per": None, "pbr": None, "eps": None, "bps": None,
        "market_cap_eok": None, "industry": None,
        "op_profit": None, "roe": None, "op_growth": None,
    }

    integ = naver.get_json(session, INTEGRATION_URL.format(code=code))
    if integ:
        ti = _totalinfo_map(integ)
        rec["per"] = naver.to_float(ti.get("per"))
        rec["pbr"] = naver.to_float(ti.get("pbr"))
        rec["eps"] = naver.to_float(ti.get("eps"))
        rec["bps"] = naver.to_float(ti.get("bps"))
        rec["market_cap_eok"] = naver.market_value_to_eok(ti.get("marketValue"))
        icode = str(integ.get("industryCode") or "")
        rec["industry"] = industry_map.get(icode) or (icode or None)
        if integ.get("stockName"):
            rec["name"] = integ["stockName"]

    annual = naver.get_json(session, ANNUAL_URL.format(code=code))
    if annual:
        fi = annual.get("financeInfo") or {}
        latest, prev = _latest_actual(fi)
        if latest:
            rec["op_profit"] = _row_value(fi, "영업이익", latest)
            rec["roe"] = _row_value(fi, "ROE", latest)
            if prev:
                op_prev = _row_value(fi, "영업이익", prev)
                op_now = rec["op_profit"]
                if op_now is not None and op_prev not in (None, 0):
                    rec["op_growth"] = (op_now - op_prev) / abs(op_prev) * 100.0
    return rec


if __name__ == "__main__":
    s = naver.make_session()
    imap = fetch_industry_map(s)
    print("업종 수:", len(imap))
    for code, name in [("005930", "삼성전자"), ("000660", "SK하이닉스"), ("012450", "한화에어로스페이스")]:
        r = fetch_one(s, code, name, imap)
        print(r)
