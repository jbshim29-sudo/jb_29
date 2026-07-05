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
DEFAULT_PERIOD_KEY = "w1"     # 기본 선택 기간
PRICE_PAGE_SIZE = 60          # price API 한 페이지 크기(상한 60)
PRICE_PAGES = 3               # 60*3 = 최대 180거래일 (6개월 커버)

# ---- 저평가 다지표 가중치 (합계로 자동 정규화) ----
# 각 지표를 KOSPI200 유니버스 내 백분위(0~100)로 환산 후 가중 합산.
SCORE_WEIGHTS = {
    "per": 30,        # PER 낮을수록 우대 (0 이하/결측은 최하위)
    "pbr": 25,        # PBR 낮을수록 우대 (0 이하/결측은 최하위)
    "roe": 25,        # ROE 높을수록 우대
    "op_growth": 20,  # 영업이익 전년比 증가율 높을수록 우대 (적자 종목 최하위)
}

# 스코어가 높을수록(=저평가+우량) 투자 우선순위 상위.
