# -*- coding: utf-8 -*-
"""종목별 일봉 종가로 기간별(당일~6개월) 등락률 계산."""
import os
import sys

import naver

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

PRICE_URL = "https://m.stock.naver.com/api/stock/{code}/price?pageSize={n}&page={page}"


def _fetch_closes(session, code):
    """최신->과거 순서의 종가 리스트 반환 (여러 페이지 병합)."""
    closes = []
    for page in range(1, config.PRICE_PAGES + 1):
        data = naver.get_json(
            session, PRICE_URL.format(code=code, n=config.PRICE_PAGE_SIZE, page=page)
        )
        if not isinstance(data, list) or not data:
            break
        closes.extend(naver.to_float(d.get("closePrice")) for d in data)
        if len(data) < config.PRICE_PAGE_SIZE:
            break  # 마지막 페이지
    return [c for c in closes if c is not None]


def fetch_returns(session, code):
    """({키: 등락률% 또는 None}, 최신종가) 반환. 데이터 부족 기간은 None."""
    closes = _fetch_closes(session, code)
    out = {key: None for _, key, _ in config.PERIODS}
    if len(closes) < 2:
        return out, (closes[0] if closes else None)
    latest = closes[0]
    for _label, key, ndays in config.PERIODS:
        if ndays < len(closes) and closes[ndays]:
            out[key] = (latest - closes[ndays]) / closes[ndays] * 100.0
    return out, latest


if __name__ == "__main__":
    s = naver.make_session()
    for code in ["005930", "000660", "012450"]:
        rets, last = fetch_returns(s, code)
        print(code, "last", last, {k: (round(v, 2) if v is not None else None) for k, v in rets.items()})
