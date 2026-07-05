# -*- coding: utf-8 -*-
"""백분위 정규화 기반 다지표 가중 저평가 스코어 + 주간 상승/하락 분류."""
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.dirname(__file__)))
import config


def _goodness(df):
    """각 지표를 '높을수록 좋음' 방향의 값으로 변환. 무효값은 NaN."""
    g = pd.DataFrame(index=df.index)
    # PER/PBR: 0 이하(적자·자본잠식)는 무효 처리 후 낮을수록 좋음 -> 부호 반전
    per = df["per"].where(df["per"] > 0)
    pbr = df["pbr"].where(df["pbr"] > 0)
    g["per"] = -per
    g["pbr"] = -pbr
    # ROE: 높을수록 좋음
    g["roe"] = df["roe"]
    # 영업이익 증가율: 높을수록 좋음. 단 최신 영업이익 적자면 무효(최하위)
    op_growth = df["op_growth"].where(df["op_profit"] > 0)
    g["op_growth"] = op_growth
    return g


def compute_scores(records):
    """records(list[dict]) -> 스코어·순위·분류가 추가된 DataFrame (스코어 내림차순)."""
    df = pd.DataFrame(records)

    # 시가총액 순위 (유니버스 내, 큰 순서 = 1위)
    df["market_cap_rank"] = df["market_cap_eok"].rank(ascending=False, method="min").astype("Int64")

    # 지표별 백분위 서브스코어 (0~100). 무효/결측은 0점.
    g = _goodness(df)
    weights = config.SCORE_WEIGHTS
    sub = pd.DataFrame(index=df.index)
    for key in weights:
        pct = g[key].rank(pct=True) * 100.0  # 높을수록 좋음 -> 큰 값이 높은 백분위
        sub[key] = pct.fillna(0.0)
        df[f"score_{key}"] = sub[key].round(1)

    total_w = sum(weights.values()) or 1
    df["score"] = sum(sub[k] * w for k, w in weights.items()) / total_w
    df["score"] = df["score"].round(2)

    # 상승/하락 분류는 기간 선택에 따라 대시보드(JS)에서 처리한다.
    df = df.sort_values("score", ascending=False).reset_index(drop=True)
    df.insert(0, "rank", df.index + 1)
    return df


if __name__ == "__main__":
    demo = [
        {"code": "A", "name": "저평가주", "per": 5, "pbr": 0.5, "eps": 1000, "bps": 2000,
         "market_cap_eok": 5000, "industry": "은행", "op_profit": 1000, "roe": 15, "op_growth": 20},
        {"code": "B", "name": "고평가주", "per": 80, "pbr": 12, "eps": 100, "bps": 500,
         "market_cap_eok": 90000, "industry": "반도체", "op_profit": 500, "roe": 4, "op_growth": -30},
        {"code": "C", "name": "적자주", "per": -3, "pbr": 3, "eps": -200, "bps": 1000,
         "market_cap_eok": 2000, "industry": "화학", "op_profit": -100, "roe": -8, "op_growth": None},
    ]
    out = compute_scores(demo)
    print(out[["rank", "name", "score", "score_per", "score_pbr", "score_roe",
               "score_op_growth", "market_cap_rank"]].to_string(index=False))
