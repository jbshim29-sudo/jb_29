# -*- coding: utf-8 -*-
"""모의투자 추적: 기간별 유망종목 TOP10을 매수가로 고정하고 수익률을 지속 추적.

- 매수(고정)는 PAPER_START_DATE 당일 장중(KST 9시 이후) 첫 실행에서 1회.
- 이후 매 실행마다 현재가로 평가액·수익률 계산 + 히스토리 누적.
- 상태는 state/portfolios.json 에 저장(저장소에 커밋되어 추적이 이어짐).
"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

KST = timezone(timedelta(hours=9))


def _load():
    if os.path.exists(config.PORTFOLIO_FILE):
        try:
            with open(config.PORTFOLIO_FILE, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None
    return None


def _save(state):
    os.makedirs(config.STATE_DIR, exist_ok=True)
    tmp = config.PORTFOLIO_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)
    os.replace(tmp, config.PORTFOLIO_FILE)


def _price_map(df):
    out = {}
    for _, r in df.iterrows():
        v = r.get("last_close")
        out[r["code"]] = None if (v is None or pd.isna(v)) else float(v)
    return out


def _top_n(df, pkey, n):
    col = f"pscore_{pkey}"
    d = df.sort_values(col, ascending=False) if col in df.columns else df
    return [{"code": r["code"], "name": r["name"]} for _, r in d.head(n).iterrows()]


def update(df):
    """모의투자 상태를 갱신하고 반환한다."""
    now = datetime.now(KST)
    today = now.strftime("%Y-%m-%d")
    now_iso = now.strftime("%Y-%m-%d %H:%M")
    amount = config.PAPER_AMOUNT_PER_STOCK
    prices = _price_map(df)

    state = _load() or {"start_date": config.PAPER_START_DATE, "established": False, "periods": {}}

    # 매수 고정 (start_date 당일 장중 9시 이후 첫 실행)
    if not state.get("established") and today >= state.get("start_date", config.PAPER_START_DATE) and now.hour >= 9:
        periods = {}
        for label, pkey in config.PAPER_PERIODS:
            holds = []
            for s in _top_n(df, pkey, config.PAPER_TOP_N):
                bp = prices.get(s["code"])
                if not bp:
                    continue
                holds.append({
                    "code": s["code"], "name": s["name"], "buy_price": bp,
                    "shares": round(amount / bp, 4), "last_price": bp,
                })
            periods[pkey] = {"label": label, "holdings": holds, "history": []}
        state["periods"] = periods
        state["established"] = True
        state["buy_date"] = now_iso

    # 현재가 평가 + 히스토리 누적
    if state.get("established"):
        for pkey, p in state["periods"].items():
            invested = value = 0.0
            for h in p["holdings"]:
                cur = prices.get(h["code"])
                if cur:
                    h["last_price"] = cur
                cur = h.get("last_price") or h["buy_price"]
                invested += amount
                value += h["shares"] * cur
                h["ret"] = round((cur - h["buy_price"]) / h["buy_price"] * 100, 2)
                h["value"] = round(h["shares"] * cur)
            p["invested"] = round(invested)
            p["value"] = round(value)
            p["ret"] = round((value - invested) / invested * 100, 2) if invested else 0.0
            p["profit"] = round(value - invested)
            hist = p.setdefault("history", [])
            hist.append({"t": now_iso, "ret": p["ret"]})
            if len(hist) > config.PAPER_HISTORY_CAP:
                p["history"] = hist[-config.PAPER_HISTORY_CAP:]
        state["updated"] = now_iso

    _save(state)
    return state


if __name__ == "__main__":
    print("PAPER_START_DATE:", config.PAPER_START_DATE)
    print("파일 경로:", config.PORTFOLIO_FILE)
    print("현재 상태:", "있음" if _load() else "없음")
