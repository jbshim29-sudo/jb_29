# -*- coding: utf-8 -*-
"""모의투자 추적: 기간별 유망종목 TOP10을 두 가지 방식으로 추적.

- fixed(고정 보유): 매수 시점 TOP10을 한 번 사서 계속 보유.
- rebal(주기적 재매입): 각 기간 주기마다 현재 TOP10으로 전량 교체(리밸런싱).
    매도 시 실효 세금(REBAL_TAX_RATE)을 차감하고 평가금액을 복리로 재투자.

매수(고정)는 PAPER_START_DATE 당일 장중(KST 9시 이후) 첫 실행에서 1회.
상태는 state/portfolios.json 에 저장(저장소 커밋으로 추적 지속).
"""
import copy
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


def _basket(df, pkey, n, prices, total):
    """현재 TOP-n을 total 금액으로 균등 매수한 보유 리스트."""
    picks = [s for s in _top_n(df, pkey, n) if prices.get(s["code"])]
    if not picks:
        return []
    alloc = total / len(picks)
    out = []
    for s in picks:
        bp = prices[s["code"]]
        out.append({"code": s["code"], "name": s["name"], "buy_price": bp,
                    "shares": round(alloc / bp, 6), "last_price": bp})
    return out


def _mark(holds, prices):
    """보유 평가액 계산 + 각 종목 현재가/수익률 갱신."""
    value = 0.0
    for h in holds:
        cur = prices.get(h["code"])
        if cur:
            h["last_price"] = cur
        cur = h.get("last_price") or h["buy_price"]
        h["ret"] = round((cur - h["buy_price"]) / h["buy_price"] * 100, 2)
        h["value"] = round(h["shares"] * cur)
        value += h["shares"] * cur
    return value


def _push_hist(track, now_iso, ret):
    hist = track.setdefault("history", [])
    hist.append({"t": now_iso, "ret": ret})
    if len(hist) > config.PAPER_HISTORY_CAP:
        track["history"] = hist[-config.PAPER_HISTORY_CAP:]


def update(df):
    now = datetime.now(KST)
    today = now.strftime("%Y-%m-%d")
    now_iso = now.strftime("%Y-%m-%d %H:%M")
    amount = config.PAPER_AMOUNT_PER_STOCK
    n = config.PAPER_TOP_N
    initial = amount * n
    prices = _price_map(df)

    state = _load() or {"start_date": config.PAPER_START_DATE, "established": False, "periods": {}}

    # ---- 매수 고정 (start_date 당일 장중 9시 이후 첫 실행) ----
    if not state.get("established") and today >= state.get("start_date", config.PAPER_START_DATE) and now.hour >= 9:
        periods = {}
        for label, pkey in config.PAPER_PERIODS:
            holds = _basket(df, pkey, n, prices, initial)
            periods[pkey] = {
                "label": label,
                "fixed": {"holdings": copy.deepcopy(holds), "history": []},
                "rebal": {"holdings": copy.deepcopy(holds), "last_rebalance": today,
                          "count": 0, "total_tax": 0.0,
                          "interval": config.REBAL_INTERVAL_DAYS.get(pkey, 30), "history": []},
            }
        state.update({"periods": periods, "established": True, "buy_date": now_iso, "initial": initial})

    # ---- 매 실행 평가/리밸런싱 ----
    if state.get("established"):
        for pkey, p in state["periods"].items():
            # 고정 보유
            fx = p["fixed"]
            fv = _mark(fx["holdings"], prices)
            fx.update({"value": round(fv), "invested": initial,
                       "ret": round((fv - initial) / initial * 100, 2), "profit": round(fv - initial)})
            _push_hist(fx, now_iso, fx["ret"])

            # 주기적 재매입
            rb = p["rebal"]
            rv = _mark(rb["holdings"], prices)
            last = datetime.strptime(rb["last_rebalance"], "%Y-%m-%d").date()
            if (now.date() - last).days >= rb.get("interval", 30):
                tax = rv * config.REBAL_TAX_RATE
                after = rv - tax
                rb["holdings"] = _basket(df, pkey, n, prices, after)
                rv = _mark(rb["holdings"], prices)
                rb["last_rebalance"] = today
                rb["count"] = rb.get("count", 0) + 1
                rb["total_tax"] = round(rb.get("total_tax", 0.0) + tax)
            rb.update({"value": round(rv), "invested": initial,
                       "ret": round((rv - initial) / initial * 100, 2), "profit": round(rv - initial)})
            _push_hist(rb, now_iso, rb["ret"])
        state["updated"] = now_iso

    _save(state)
    return state


if __name__ == "__main__":
    print("start:", config.PAPER_START_DATE, "| 세금:", config.REBAL_TAX_RATE,
          "| 주기(일):", config.REBAL_INTERVAL_DAYS)
    print("상태:", "있음" if _load() else "없음")
