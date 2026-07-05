# -*- coding: utf-8 -*-
"""7팩터 균형형 스코어 (기간별 재랭킹 지원).

가치·수익성·성장대비저평가·뉴스는 기간 무관(고정), 모멘텀·업종모멘텀·대형주상승은
선택 기간의 등락률로 재계산한다. 따라서 기간 탭마다 종합 스코어·순위가 바뀐다.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config

# 팩터 분류
BASE_KEYS = ["per", "pbr", "roe", "peg", "news_buzz"]          # 기간 무관
PERIOD_KEYS = ["momentum", "sector_mom", "largecap_mom"]        # 기간 종속


def _pct(series, index):
    if series is None:
        series = pd.Series(np.nan, index=index)
    return (series.rank(pct=True) * 100.0).fillna(0.0)


def _base_goodness(df):
    """기간 무관 팩터의 '높을수록 좋음' 값."""
    per = df["per"].where(df["per"] > 0)
    pbr = df["pbr"].where(df["pbr"] > 0)
    g = {
        "per": -per,
        "pbr": -pbr,
        "roe": df["roe"],
        "peg": (df["op_growth"] / per).where((per > 0) & (df["op_growth"] > 0)),
        "news_buzz": df.get("news_buzz"),
    }
    return g


def _period_goodness(df, ret_col, mcap_pct):
    """선택 기간(ret_col)의 등락률로 모멘텀 계열 팩터 산출."""
    mom = df[ret_col] if ret_col in df.columns else pd.Series(np.nan, index=df.index)
    sector_mom = pd.DataFrame({"industry": df["industry"], "mom": mom}) \
        .groupby("industry")["mom"].transform("mean")
    largecap = mcap_pct * mom
    return {"momentum": mom, "sector_mom": sector_mom, "largecap_mom": largecap}, mom, sector_mom


def compute_scores(records):
    """records -> 기간별 스코어/순위 컬럼이 포함된 DataFrame (기본기간 스코어 내림차순)."""
    df = pd.DataFrame(records)
    if "news_buzz" not in df.columns:
        df["news_buzz"] = np.nan

    df["market_cap_rank"] = df["market_cap_eok"].rank(ascending=False, method="min").astype("Int64")
    mcap_pct = df["market_cap_eok"].rank(pct=True)

    weights = config.SCORE_WEIGHTS
    total_w = sum(weights.values()) or 1

    # 기간 무관 서브스코어(1회 계산)
    base_g = _base_goodness(df)
    base_sub = {k: _pct(base_g.get(k), df.index) for k in BASE_KEYS}

    default_key = config.DEFAULT_PERIOD_KEY

    # 각 기간별 종합 스코어/순위
    for _label, pkey, _days in config.PERIODS:
        ret_col = f"ret_{pkey}"
        per_g, mom, sector_mom = _period_goodness(df, ret_col, mcap_pct)
        per_sub = {k: _pct(per_g[k], df.index) for k in PERIOD_KEYS}

        all_sub = {**base_sub, **per_sub}
        score = sum(all_sub[k] * weights[k] for k in weights) / total_w
        df[f"pscore_{pkey}"] = score.round(2)
        df[f"prank_{pkey}"] = score.rank(ascending=False, method="min").astype("Int64")
        df[f"pmom_{pkey}"] = mom.round(2)

        if pkey == default_key:
            # 기본기간 값을 대표 컬럼으로 노출 (CSV/정렬/설명용)
            df["score"] = df[f"pscore_{pkey}"]
            df["momentum"] = mom
            df["sector_mom"] = sector_mom
            df["peg_ratio"] = base_g["peg"]
            for k in weights:
                df[f"score_{k}"] = all_sub[k].round(1)

    df = df.sort_values("score", ascending=False).reset_index(drop=True)
    df.insert(0, "rank", df.index + 1)
    return df


if __name__ == "__main__":
    demo = [
        {"code": "A", "name": "가치함정(하락)", "per": 3, "pbr": 0.3, "roe": 12, "op_growth": 2,
         "market_cap_eok": 8000, "industry": "유틸", "news_buzz": 3,
         "ret_d1": -1, "ret_w1": -4, "ret_m1": -8, "ret_m3": -15, "ret_m6": -30},
        {"code": "B", "name": "단기급등 대형", "per": 15, "pbr": 2.0, "roe": 20, "op_growth": 80,
         "market_cap_eok": 500000, "industry": "반도체", "news_buzz": 20,
         "ret_d1": 8, "ret_w1": 20, "ret_m1": 3, "ret_m3": -5, "ret_m6": 5},
        {"code": "C", "name": "장기우상향 중형", "per": 6, "pbr": 0.7, "roe": 15, "op_growth": 30,
         "market_cap_eok": 30000, "industry": "반도체", "news_buzz": 8,
         "ret_d1": 0, "ret_w1": 2, "ret_m1": 6, "ret_m3": 25, "ret_m6": 60},
    ]
    out = compute_scores(demo)
    for pk in ["d1", "w1", "m3", "m6"]:
        o = out.sort_values(f"pscore_{pk}", ascending=False)
        order = " > ".join(f"{n}({s})" for n, s in zip(o["name"], o[f"pscore_{pk}"]))
        print(f"[{pk:>3}] {order}")
