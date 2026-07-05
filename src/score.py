# -*- coding: utf-8 -*-
"""7팩터 균형형 스코어: 가치·수익성·성장대비저평가·모멘텀·업종모멘텀·대형주상승·뉴스버즈."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config


def _momentum(df):
    """1·3개월 등락률 평균을 가격 모멘텀으로 사용."""
    cols = [f"ret_{k}" for k in config.MOMENTUM_KEYS if f"ret_{k}" in df.columns]
    if not cols:
        return pd.Series(np.nan, index=df.index)
    return df[cols].mean(axis=1, skipna=True)


def _goodness(df):
    """각 팩터를 '높을수록 좋음' 값으로 변환(무효는 NaN). (goodness dict, 파생컬럼 dict) 반환."""
    g = {}
    derived = {}

    # 가치: PER/PBR 낮을수록 좋음 (0 이하/결측 무효)
    per = df["per"].where(df["per"] > 0)
    pbr = df["pbr"].where(df["pbr"] > 0)
    g["per"] = -per
    g["pbr"] = -pbr

    # 수익성
    g["roe"] = df["roe"]

    # 성장대비 저평가(PEG류): 영업이익증가율 ÷ PER (둘 다 양수일 때만)
    peg = (df["op_growth"] / per).where((per > 0) & (df["op_growth"] > 0))
    g["peg"] = peg
    derived["peg_ratio"] = peg

    # 가격 모멘텀 (1·3개월 평균)
    mom = _momentum(df)
    g["momentum"] = mom
    derived["momentum"] = mom

    # 업종 모멘텀: 같은 업종 종목들의 모멘텀 평균
    sect = pd.DataFrame({"industry": df["industry"], "mom": mom})
    sector_mom = sect.groupby("industry")["mom"].transform("mean")
    g["sector_mom"] = sector_mom
    derived["sector_mom"] = sector_mom

    # 대형주 상승 보너스: 시가총액 백분위 × 모멘텀 (큰 종목이 오를수록 ↑)
    mcap_pct = df["market_cap_eok"].rank(pct=True)
    g["largecap_mom"] = (mcap_pct * mom)

    # 뉴스 버즈
    g["news_buzz"] = df.get("news_buzz")

    return g, derived


def compute_scores(records):
    """records(list[dict]) -> 스코어·순위 컬럼이 추가된 DataFrame (스코어 내림차순)."""
    df = pd.DataFrame(records)
    if "news_buzz" not in df.columns:
        df["news_buzz"] = np.nan

    # 시가총액 순위 (유니버스 내, 큰 순서 = 1위)
    df["market_cap_rank"] = df["market_cap_eok"].rank(ascending=False, method="min").astype("Int64")

    goodness, derived = _goodness(df)
    for k, v in derived.items():
        df[k] = v

    weights = config.SCORE_WEIGHTS
    sub = {}
    for key in weights:
        series = goodness.get(key)
        if series is None:
            series = pd.Series(np.nan, index=df.index)
        pct = series.rank(pct=True) * 100.0     # 높을수록 좋음 → 큰 값이 높은 백분위
        sub[key] = pct.fillna(0.0)
        df[f"score_{key}"] = sub[key].round(1)

    total_w = sum(weights.values()) or 1
    df["score"] = sum(sub[k] * w for k, w in weights.items()) / total_w
    df["score"] = df["score"].round(2)

    df = df.sort_values("score", ascending=False).reset_index(drop=True)
    df.insert(0, "rank", df.index + 1)
    return df


if __name__ == "__main__":
    # 간단 데모: 가치함정(싸지만 하락) vs 성장모멘텀
    demo = [
        {"code": "A", "name": "가치함정(하락)", "per": 3, "pbr": 0.3, "eps": 100, "bps": 1000,
         "market_cap_eok": 8000, "industry": "유틸", "op_profit": 500, "roe": 12, "op_growth": 2,
         "ret_m1": -8, "ret_m3": -15, "news_buzz": 3},
        {"code": "B", "name": "성장+상승 대형", "per": 15, "pbr": 2.0, "eps": 3000, "bps": 9000,
         "market_cap_eok": 500000, "industry": "반도체", "op_profit": 40000, "roe": 20, "op_growth": 80,
         "ret_m1": 12, "ret_m3": 40, "news_buzz": 20},
        {"code": "C", "name": "저평가+반등 중형", "per": 6, "pbr": 0.7, "eps": 1500, "bps": 4000,
         "market_cap_eok": 30000, "industry": "반도체", "op_profit": 5000, "roe": 15, "op_growth": 30,
         "ret_m1": 5, "ret_m3": 10, "news_buzz": 8},
    ]
    out = compute_scores(demo)
    cols = ["rank", "name", "score"] + [f"score_{k}" for k in config.SCORE_WEIGHTS]
    print(out[cols].to_string(index=False))
