# -*- coding: utf-8 -*-
"""프로젝트 설정 — 경로, 요청 옵션, 저평가 스코어 가중치."""
import os

# ---- 경로 ----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_DIR = os.path.join(DATA_DIR, "log")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
DASHBOARD_HTML = os.path.join(OUTPUT_DIR, "dashboard.html")
# GitHub Pages 서빙용 (main 브랜치 /docs). 클라우드 루틴이 이 파일을 커밋한다.
DOCS_DIR = os.path.join(BASE_DIR, "docs")
DOCS_HTML = os.path.join(DOCS_DIR, "index.html")
# 모의투자 상태 저장(추적 지속을 위해 저장소에 커밋되는 파일)
STATE_DIR = os.path.join(BASE_DIR, "state")
PORTFOLIO_FILE = os.path.join(STATE_DIR, "portfolios.json")

# ---- 네트워크 ----
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
REQUEST_TIMEOUT = 10          # 초
MAX_WORKERS = 8               # 동시 요청 수 (정중한 수준)
RETRY = 3                     # 요청 실패 시 재시도 횟수
RETRY_BACKOFF = 0.6          # 재시도 지연(초) 기준

# ---- 기간별 등락률 ----
# (표시라벨, 데이터키, N거래일 전 대비)
PERIODS = [
    ("당일", "d1", 1),
    ("최근 3일", "d3", 3),
    ("최근 1주일", "w1", 5),
    ("최근 2주일", "w2", 10),
    ("최근 1개월", "m1", 20),
    ("최근 3개월", "m3", 60),
    ("최근 6개월", "m6", 120),
]
DEFAULT_PERIOD_KEY = "total"  # 기본 선택 = 종합(토탈) 순위
PRICE_PAGE_SIZE = 60          # price API 한 페이지 크기(상한 60)
PRICE_PAGES = 3               # 60*3 = 최대 180거래일 (6개월 커버)

# ---- 토탈(종합) 순위 ----
# 종합 모멘텀 = 아래 기간 등락률의 가중 평균 (6개월은 제외, 3개월까지만 반영).
TOTAL_PERIOD_WEIGHTS = {
    "d1": 0.5, "d3": 1.0, "w1": 1.5, "w2": 1.5, "m1": 1.0, "m3": 0.5,
}
# 저평가 → 상승 모멘텀 '전환' 가중치 (종합 점수 안에서 추가 반영).
# 싸면서(저PER/PBR) 최근 1~2주 상승으로 돌아서는(1~3개월 대비 가속) 종목을 우대.
TRANSITION_WEIGHT = 15

# ---- 다지표 가중치 (합계로 자동 정규화) ----
# 각 팩터를 KOSPI200 유니버스 내 백분위(0~100)로 환산 후 가중 합산.
# 균형형: 가치(함정 회피용 모멘텀 결합) + 성장 + 추세 + 관심도.
SCORE_WEIGHTS = {
    "per": 13,          # PER 낮을수록 우대 (0 이하/결측은 최하위)
    "pbr": 12,          # PBR 낮을수록 우대 (0 이하/결측은 최하위)
    "roe": 10,          # ROE 높을수록 우대
    "peg": 15,          # 성장대비 저평가: 영업이익증가율 ÷ PER (높을수록 우대)
    "momentum": 20,     # 가격 모멘텀: 1·3개월 상승률 (높을수록 우대 → 하락 종목 감점)
    "sector_mom": 12,   # 업종 모멘텀: 같은 업종 평균 모멘텀 (뜨는 업종 우대)
    "largecap_mom": 8,  # 대형주 상승 보너스: 시가총액 상위 × 상승 (큰 종목이 오를 때 가점)
    "news_buzz": 10,    # 뉴스 버즈: 최근 기사량 (관심도/전망 프록시)
}

# 모멘텀 계산에 쓰는 기간 키(1개월·3개월 평균). fetch_prices 의 ret_ 키와 일치.
MOMENTUM_KEYS = ["m1", "m3"]

# ---- 뉴스 버즈 ----
NEWS_RECENT_DAYS = 7          # 최근 N일 기사 수를 버즈로 집계
NEWS_PAGE_SIZE = 20           # 뉴스 API 한 페이지 클러스터 수

# 스코어가 높을수록(=저평가+성장+추세+관심) 투자 우선순위 상위.

# ---- 모의투자(test 페이지) ----
# 각 기간 유망종목 TOP10을 종목당 1천만원씩 매수했다고 가정하고 수익률을 지속 추적.
PAPER_START_DATE = "2026-07-05"       # 이 날짜(9시 이후) 첫 실행에 매수가를 고정(테스트: 오늘부터)
PAPER_AMOUNT_PER_STOCK = 10_000_000   # 종목당 매수 금액(원)
PAPER_TOP_N = 10                      # 기간별 상위 몇 종목
PAPER_HISTORY_CAP = 2000             # 기간별 수익률 히스토리 최대 보관 포인트
# (표시라벨, pscore 키) — 요약 유망종목 TOP10과 동일 기준
PAPER_PERIODS = [
    ("당일", "d1"), ("최근 3일", "d3"), ("최근 1주일", "w1"), ("최근 2주일", "w2"),
    ("최근 1개월", "m1"), ("최근 3개월", "m3"), ("최근 6개월", "m6"),
]
# 주기적 재매입(리밸런싱): 각 기간 탭 = 재매입 주기(달력일). 매도 시 세금만 반영.
REBAL_INTERVAL_DAYS = {"d1": 1, "d3": 3, "w1": 7, "w2": 14, "m1": 30, "m3": 90, "m6": 180}
# 매도 시 실효 세금 (KOSPI 2025~: 증권거래세 0% + 농어촌특별세 0.15%). 매수는 세금 없음.
REBAL_TAX_RATE = 0.0015
