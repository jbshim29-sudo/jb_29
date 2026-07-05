# -*- coding: utf-8 -*-
"""7팩터 균형형 스코어 + 기간별 재랭킹 + 토탈(종합) 순위.

- 가치·수익성·성장대비저평가·뉴스: 기간 무관(고정)
- 모멘텀·업종모멘텀·대형주상승: 선택 기간의 등락률로 재계산
- 토탈: 3개월까지 기간 가중평균 모멘텀 + '저평가→상승 전환' 가중치
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config

BASE_KEYS = ["per", "pbr", "roe", "peg", "news_buzz"]
PERIOD_KEYS = ["momentum", "sector_mom", "largecap_mom"]


def _pct(series, index):
    if series is None:
        series = pd.Series(np.nan, index=index)
    return (series.rank(pct=True) * 100.0).fillna(0.0)


def _base_goodness(df):
    per = df["per"].where(df["per"] > 0)
    pbr = df["pbr"].where(df["pbr"] > 0)
    return {
        "per": -per, "pbr": -pbr, "roe": df["roe"],
        "peg": (df["op_growth"] / per).where((per > 0) & (df["op_growth"] > 0)),
        "news_buzz": df.get("news_buzz"),
    }, per


def _period_goodness(df, mom, mcap_pct):
    """모멘텀 시리즈(mom)로 모멘텀 계열 팩터 산출."""
    sector_mom = pd.DataFrame({"industry": df["industry"], "mom": mom}) \
        .groupby("industry")["mom"].transform("mean")
    return {"momentum": mom, "sector_mom": sector_mom, "largecap_mom": mcap_pct * mom}


def _blend(df, weights):
    """기간 등락률의 행별 가중평균(결측 기간은 제외)."""
    cols = [(f"ret_{k}", wt) for k, wt in weights.items() if f"ret_{k}" in df.columns]
    if not cols:
        return pd.Series(np.nan, index=df.index)
    vals = df[[c for c, _ in cols]].to_numpy(dtype=float)
    wts = np.array([wt for _, wt in cols], dtype=float)
    mask = ~np.isnan(vals)
    wsum = (mask * wts).sum(axis=1)
    num = np.nansum(vals * wts, axis=1)
    out = np.where(wsum > 0, num / np.where(wsum == 0, 1, wsum), np.nan)
    return pd.Series(out, index=df.index)


def compute_scores(records):
    df = pd.DataFrame(records)
    if "news_buzz" not in df.columns:
        df["news_buzz"] = np.nan

    df["market_cap_rank"] = df["market_cap_eok"].rank(ascending=False, method="min").astype("Int64")
    mcap_pct = df["market_cap_eok"].rank(pct=True)

    weights = config.SCORE_WEIGHTS
    total_w = sum(weights.values()) or 1

    base_g, _per = _base_goodness(df)
    base_sub = {k: _pct(base_g.get(k), df.index) for k in BASE_KEYS}

    def period_score(mom):
        per_sub = {k: _pct(v, df.index) for k, v in _period_goodness(df, mom, mcap_pct).items()}
        all_sub = {**base_sub, **per_sub}
        return sum(all_sub[k] * weights[k] for k in weights) / total_w, all_sub

    # ---- 실제 기간별 스코어 ----
    for _label, pkey, _days in config.PERIODS:
        mom = df[f"ret_{pkey}"] if f"ret_{pkey}" in df.columns else pd.Series(np.nan, index=df.index)
        score, _ = period_score(mom)
        df[f"pscore_{pkey}"] = score.round(2)
        df[f"prank_{pkey}"] = score.rank(ascending=False, method="min").astype("Int64")
        df[f"pmom_{pkey}"] = mom.round(2)

    # ---- 토탈(종합) 순위 : 3개월까지 가중평균 모멘텀 + 전환 가중치 ----
    mom_total = _blend(df, config.TOTAL_PERIOD_WEIGHTS)
    df["ret_total"] = mom_total.round(2)

    # 저평가 → 상승 전환 팩터
    value01 = ((base_sub["per"] + base_sub["pbr"]) / 2.0) / 100.0        # 저평가도(0~1)
    short = _blend(df, {"w1": 1, "w2": 1})                               # 최근 1~2주
    med = _blend(df, {"m1": 1, "m3": 1})                                 # 1~3개월
    short_relu = short.clip(lower=0).fillna(0)
    accel = (short - med)
    accel_factor = pd.Series(np.where(accel.fillna(-1) > 0, 1.0, 0.4), index=df.index)
    transition_raw = value01.fillna(0) * short_relu * accel_factor
    transition_sub = _pct(transition_raw, df.index)
    df["transition"] = transition_raw.round(3)

    base_score, all_sub = period_score(mom_total)
    tw = config.TRANSITION_WEIGHT
    total_score = (base_score * total_w + transition_sub * tw) / (total_w + tw)
    df["pscore_total"] = total_score.round(2)
    df["prank_total"] = total_score.rank(ascending=False, method="min").astype("Int64")
    df["pmom_total"] = mom_total.round(2)

    # ---- 기본 대표 컬럼 (기본 선택 기간) ----
    dk = config.DEFAULT_PERIOD_KEY
    df["score"] = df[f"pscore_{dk}"]
    df["momentum"] = df[f"pmom_{dk}"]
    df["sector_mom"] = _period_goodness(df, df[f"pmom_{dk}"], mcap_pct)["sector_mom"]
    df["peg_ratio"] = base_g["peg"]
    if dk == "total":
        for k in weights:
            df[f"score_{k}"] = all_sub[k].round(1)
        df["score_transition"] = transition_sub.round(1)
    else:
        _, dsub = period_score(df[f"pmom_{dk}"])
        for k in weights:
            df[f"score_{k}"] = dsub[k].round(1)

    df = df.sort_values("score", ascending=False).reset_index(drop=True)
    df.insert(0, "rank", df.index + 1)
    return df


if __name__ == "__main__":
    demo = [
        {"code": "A", "name": "저평가+전환(싸다가 반등)", "per": 4, "pbr": 0.4, "roe": 12, "op_growth": 10,
         "market_cap_eok": 20000, "industry": "은행", "news_buzz": 6,
         "ret_d1": 2, "ret_d3": 5, "ret_w1": 7, "ret_w2": 4, "ret_m1": -3, "ret_m3": -8, "ret_m6": -12},
        {"code": "B", "name": "저평가+계속하락(함정)", "per": 3, "pbr": 0.3, "roe": 10, "op_growth": 5,
         "market_cap_eok": 15000, "industry": "유틸", "news_buzz": 3,
         "ret_d1": -1, "ret_d3": -3, "ret_w1": -5, "ret_w2": -6, "ret_m1": -10, "ret_m3": -18, "ret_m6": -30},
        {"code": "C", "name": "고평가+급등", "per": 40, "pbr": 8, "roe": 20, "op_growth": 60,
         "market_cap_eok": 300000, "industry": "반도체", "news_buzz": 20,
         "ret_d1": 5, "ret_d3": 12, "ret_w1": 20, "ret_w2": 25, "ret_m1": 30, "ret_m3": 50, "ret_m6": 90},
    ]
    out = compute_scores(demo)
    print(out[["rank", "name", "score", "score_transition", "pscore_total", "ret_total"]].to_string(index=False))
