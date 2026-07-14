# KOSPI 200 저평가 종목 스크리너

네이버 금융 공개 데이터를 수집해 **KOSPI 200 종목의 저평가 순위**와 **기간별 등락**을 HTML 대시보드로 보여주는 도구입니다.

## 🔴 라이브 대시보드 (여기를 보세요)

### 👉 **https://jb-29.vercel.app**

**30분마다 자동 갱신**되는 실시간 대시보드입니다. **이 주소를 북마크하세요.**

> ⚠️ **주의**: 로컬 파일 `output/dashboard.html` 은 로컬에서 `python src/main.py` 를 돌릴 때만 갱신되는
> **미리보기**입니다. 자동 갱신되지 않으니, 최신 데이터는 반드시 위 **Vercel 주소**로 확인하세요.

**자동 갱신 구조**: cron-job.org(30분마다) → GitHub Actions(데이터 수집·대시보드 생성·커밋) → Vercel(자동 재배포)
→ PC를 꺼도 계속 갱신됩니다.

## 무엇을 하나
- KOSPI 200 구성종목(약 200개)을 네이버에서 자동 수집
- 종목별 **PER · PBR · EPS · ROE · 영업이익 · 영업이익 증가율 · 시가총액(순위) · 업종** 수집
- **기간별 등락률**(당일·최근 3일·1주일·2주일·1개월·3개월·6개월) 계산 → 상승/하락 분류
- 다지표 **백분위 가중 스코어**로 저평가 투자 우선순위 산출
- 결과를 `output/dashboard.html` 대시보드 + `data/latest.csv`로 저장 (매일 갱신)

## 대시보드 3개 화면
상단 탭으로 전환합니다.
1. **💎 저평가 전체 랭킹** — 종합 스코어 순 전체 종목. 상단 **기간 탭**을 누르면 등락률·추세·상승/하락 집계가 해당 기간 기준으로 바뀝니다.
2. **🏭 업종별 TOP3** — 업종 테마별로 종합 스코어 상위 1~3위 종목을 카드로 표시(기간 탭 함께 적용).
3. **📐 스코어 산정 방식** — 가중치·백분위 정규화·예외처리·한계를 설명하는 페이지(가중치 변경 시 자동 갱신).

## 데이터 출처 (네이버 금융)
- 구성종목: `finance.naver.com/sise/entryJongmok.naver?type=KPI200`
- 재무지표: `m.stock.naver.com/api/stock/{code}/integration`, `.../finance/annual`
- 주가: `m.stock.naver.com/api/stock/{code}/price`
- 업종명 매핑: `finance.naver.com/sise/sise_group.naver?type=upjong`

## 실행 방법
수동 실행:
```
run_daily.bat          (더블클릭 또는 명령창에서 실행)
```
또는:
```
.venv\Scripts\python.exe src\main.py
```
실행 후 `output/dashboard.html`을 브라우저로 엽니다.

## 매일 자동 실행 ― 방법 A: 클라우드 루틴 (PC 꺼도 됨, 권장)
[Claude Code 루틴](https://code.claude.com/docs/ko/routines)은 Anthropic 클라우드에서 실행되므로 **내 PC가 꺼져 있어도** 매일 돌아갑니다. 이 저장소를 GitHub에 올리고 루틴을 걸면, 루틴이 매일 데이터를 수집해 `docs/index.html`을 갱신·커밋하고 **GitHub Pages 고정 URL**로 볼 수 있습니다. 자세한 설정 절차는 `ROUTINE.md`를 참고하세요.

- 클라우드 루틴은 `docs/index.html`을 GitHub Pages로 서빙(main 브랜치 `/docs`)
- 네이버 도메인(`finance.naver.com`, `m.stock.naver.com`)을 루틴 환경의 네트워크 허용목록에 추가해야 함
- 루틴은 Pro/Max/Team/Enterprise + "웹에서 Claude Code" 활성화 계정에서 사용 가능

## 매일 자동 실행 ― 방법 B: Windows 작업 스케줄러 (로컬, PC 켜져 있어야 함)
`KOSPI200_Screener` 작업이 **매일 16:00**(장 마감·종가 확정 후)에 `run_daily.bat`을 실행하도록 등록되어 있습니다.

- 상태 확인: `schtasks /Query /TN "KOSPI200_Screener" /FO LIST /V`
- 즉시 실행: `schtasks /Run /TN "KOSPI200_Screener"`
- 시간 변경(예 15:40): `schtasks /Change /TN "KOSPI200_Screener" /ST 15:40`
- 삭제: `schtasks /Delete /TN "KOSPI200_Screener" /F`

## 저평가 스코어 조정
`config.py`의 `SCORE_WEIGHTS`에서 지표 가중치를 바꿀 수 있습니다(합계로 자동 정규화).
```python
SCORE_WEIGHTS = {"per": 30, "pbr": 25, "roe": 25, "op_growth": 20}
```
- PER·PBR: 낮을수록 우대(0 이하/결측은 해당 지표 최하위)
- ROE·영업이익 증가율: 높을수록 우대(최신 영업이익 적자면 증가율 최하위)
- 등락 기간 목록: `PERIODS`(라벨, 키, 거래일 수) / 기본 선택 기간: `DEFAULT_PERIOD_KEY`

## 산출물
- `output/dashboard.html` — 최신 대시보드(정렬·색상 하이라이트)
- `data/latest.csv` — 최신 전체 데이터
- `data/YYYYMMDD.csv` — 일자별 히스토리
- `data/log/YYYYMMDD.log` — 실행 로그

## 구조
```
config.py                 설정(경로·요청·가중치)
src/naver.py              공통 HTTP·파싱 유틸
src/fetch_constituents.py KOSPI200 구성종목
src/fetch_fundamentals.py 재무지표 + 업종
src/fetch_prices.py       주간 등락률
src/score.py             백분위 가중 스코어·분류
src/build_dashboard.py   HTML 렌더
src/main.py              통합 실행
run_daily.bat            스케줄러 진입점
```

## 주의
본 자료는 공개 데이터를 가공한 **개인 투자 참고용**이며, 투자 판단과 책임은 이용자 본인에게 있습니다. 네이버 페이지 구조가 바뀌면 파서 수정이 필요할 수 있습니다.
