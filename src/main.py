# -*- coding: utf-8 -*-
"""KOSPI 200 저평가 스크리너 — 수집→스코어→대시보드 통합 실행."""
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
import naver
import fetch_constituents
import fetch_fundamentals
import fetch_prices
import fetch_news
import fetch_market
import score as score_mod
import build_dashboard

KST = timezone(timedelta(hours=9))


def log(msg):
    stamp = datetime.now(KST).strftime("%H:%M:%S")
    line = f"[{stamp}] {msg}"
    print(line, flush=True)
    try:
        os.makedirs(config.LOG_DIR, exist_ok=True)
        day = datetime.now(KST).strftime("%Y%m%d")
        with open(os.path.join(config.LOG_DIR, f"{day}.log"), "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def collect_one(code, name, industry_map):
    """스레드 작업: 종목 1개의 재무 + 주간등락 수집."""
    sess = naver.make_session()
    rec = fetch_fundamentals.fetch_one(sess, code, name, industry_map)
    rets, latest = fetch_prices.fetch_returns(sess, code)
    for key, val in rets.items():
        rec[f"ret_{key}"] = val
    rec["last_close"] = latest
    rec["news_buzz"] = fetch_news.fetch_news_buzz(sess, code)
    return rec


def main():
    t0 = time.time()
    os.makedirs(config.DATA_DIR, exist_ok=True)
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)

    sess = naver.make_session()
    log("KOSPI 200 구성종목 수집 중...")
    constituents = fetch_constituents.fetch_constituents(sess)
    log(f"구성종목 {len(constituents)}개 확보")
    if not constituents:
        log("ERROR: 구성종목을 가져오지 못했습니다. 중단.")
        return 1

    industry_map = fetch_fundamentals.fetch_industry_map(sess)
    log(f"업종 매핑 {len(industry_map)}개 로드")

    log(f"재무·주가 수집 시작 (동시 {config.MAX_WORKERS} 요청)...")
    records = []
    done = 0
    with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as ex:
        futs = {ex.submit(collect_one, c, n, industry_map): c for c, n in constituents}
        for fut in as_completed(futs):
            try:
                records.append(fut.result())
            except Exception as e:
                log(f"  종목 {futs[fut]} 수집 실패: {e}")
            done += 1
            if done % 40 == 0:
                log(f"  진행 {done}/{len(constituents)}")

    log(f"수집 완료 {len(records)}개. 시장 데이터(지수·ETF) 수집 중...")
    etf_list = fetch_market.fetch_etf_list(sess)
    # ETF 기간별(당일·1주·1개월·3개월) 수익률 병렬 수집
    with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as ex:
        futs = {ex.submit(fetch_market.fetch_etf_returns, naver.make_session(), e["code"]): e
                for e in etf_list}
        for fut in as_completed(futs):
            try:
                futs[fut]["rets"] = fut.result()
            except Exception:
                futs[fut]["rets"] = {}
    market = {
        "index": fetch_market.fetch_index(sess),
        "etf_list": etf_list,
    }
    log(f"  지수 + 국내 ETF {len(etf_list)}개 수집(기간별 수익률 포함)")

    log("스코어 계산 중...")
    df = score_mod.compute_scores(records)

    # CSV 저장 (최신 + 일자별 히스토리)
    day = datetime.now(KST).strftime("%Y%m%d")
    ret_cols = [f"ret_{key}" for _l, key, _d in config.PERIODS]
    score_cols = [f"score_{k}" for k in config.SCORE_WEIGHTS]
    cols = ["rank", "code", "name", "industry", "score", "per", "pbr", "roe", "eps",
            "op_profit", "op_growth", "peg_ratio", "momentum", "sector_mom",
            "news_buzz", "market_cap_eok", "market_cap_rank"] + score_cols + ret_cols
    csv_cols = [c for c in cols if c in df.columns]
    df[csv_cols].to_csv(os.path.join(config.DATA_DIR, "latest.csv"), index=False, encoding="utf-8-sig")
    df[csv_cols].to_csv(os.path.join(config.DATA_DIR, f"{day}.csv"), index=False, encoding="utf-8-sig")

    generated = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")
    path = build_dashboard.build(df, generated, market)
    log(f"대시보드 생성: {path}")

    # GitHub Pages용 사본 (docs/index.html)
    os.makedirs(config.DOCS_DIR, exist_ok=True)
    import shutil
    shutil.copyfile(config.DASHBOARD_HTML, config.DOCS_HTML)
    log(f"Pages 사본 생성: {config.DOCS_HTML}")

    dk = f"ret_{config.DEFAULT_PERIOD_KEY}"
    up = int((df[dk] > 0).sum()); down = int((df[dk] < 0).sum())
    log(f"요약 | 기본기간 상승 {up} / 하락 {down} | 저평가1위: {df.iloc[0]['name']} (스코어 {df.iloc[0]['score']})")
    log(f"완료 (소요 {time.time()-t0:.1f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
