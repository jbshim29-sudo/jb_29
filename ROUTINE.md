# 클라우드 루틴 설정 가이드 (PC 없이 매일 자동 갱신)

이 프로젝트를 [Claude Code 루틴](https://code.claude.com/docs/ko/routines)으로 매일 클라우드에서 실행해, `docs/index.html` 대시보드를 GitHub Pages 고정 URL로 자동 갱신하는 절차입니다.

## 전체 흐름
```
매일 정해진 시각 → 클라우드 루틴 실행
  → 저장소 clone → pip install → python src/main.py (네이버 수집)
  → docs/index.html 갱신 → main 브랜치에 커밋·푸시
  → GitHub Pages가 고정 URL로 최신 대시보드 서빙
```

## 사전 준비 (사용자 계정 작업)

### 1. GitHub 저장소 준비
- 이 폴더를 새 **private** GitHub 저장소로 push (로컬에서 git init·초기 커밋은 완료되어 있음).
- push 방법은 아래 "저장소 push" 참고.

### 2. Claude Code에 GitHub 연결
- CLI에서 `/web-setup` 실행(저장소 접근 권한 부여) 또는 [claude.ai/code](https://claude.ai/code)에서 GitHub 연결.
- 루틴이 저장소를 clone하려면 필수.

### 3. 루틴 생성
CLI에서:
```
/schedule 매일 오전 6시 KOSPI200 저평가 대시보드 갱신
```
또는 [claude.ai/code/routines](https://claude.ai/code/routines)에서 **새 루틴 → 원격**으로 생성하고 아래 프롬프트를 붙여넣습니다.

**루틴 프롬프트(그대로 복사):**
```
KOSPI 200 저평가 스크리너의 일일 데이터 갱신 작업이다.
저장소 루트에서 다음을 순서대로 수행하라.
1) pip install -r requirements.txt
2) python src/main.py   (네이버 금융에서 데이터를 수집해 docs/index.html 과 data/ CSV를 생성한다)
3) 변경된 docs/index.html 을 스테이지하고 "chore: 대시보드 자동 갱신" 메시지로 main 브랜치에 커밋 후 push 하라.
성공 기준: src/main.py 가 오류 없이 완료되고 docs/index.html 이 새로 갱신되어 main 에 커밋됨.
주의: 네트워크로 finance.naver.com 과 m.stock.naver.com 에 접근해야 한다. 접근이 막히면 그 사실을 보고하라.
```
- **모델**: 데이터 수집·커밋만 하므로 가벼운 모델로 충분.
- **저장소**: 이 저장소 선택.
- **트리거**: 일정(매일). 최소 간격 1시간. 장 마감·데이터 확정을 고려하면 다음날 새벽(예: 06:00)이 안전.
- **권한**: `docs/index.html`을 main에 직접 push 하려면 해당 저장소에 **"제한 없는 브랜치 푸시 허용"** 활성화. (끄면 `claude/` 브랜치로만 push되어 Pages가 갱신되지 않음)

### 4. 네트워크 허용목록에 네이버 추가 (중요)
기본 클라우드 환경은 임의 도메인을 차단합니다. 루틴 편집 → 환경 설정 → **네트워크 액세스: 사용자 정의**에서 아래를 허용목록에 추가하고 "기본 패키지 관리자 목록도 포함"을 체크:
```
finance.naver.com
m.stock.naver.com
```
(추가 안 하면 데이터 수집이 403 host_not_allowed로 실패합니다.)

### 5. GitHub Pages 켜기
- 저장소 **Settings → Pages → Source: Deploy from a branch → Branch: main / 폴더: /docs** 저장.
- 잠시 후 `https://<사용자명>.github.io/<레포명>/` 에서 대시보드 확인.
- ⚠️ **private 저장소의 Pages는 GitHub Pro/Team 이상에서만** 동작합니다. 무료 계정이면 저장소를 public으로 바꾸거나, 대시보드용 public 저장소를 따로 두세요.

## 저장소 push (참고)
gh CLI가 설치되어 있으면:
```
gh auth login
gh repo create kospi200-screener --private --source . --remote origin --push
```
또는 웹에서 빈 private 레포를 만든 뒤:
```
git remote add origin https://github.com/<사용자명>/<레포명>.git
git branch -M main
git push -u origin main
```

## 확인
- 루틴 세부 페이지에서 **지금 실행**으로 1회 테스트 → 실행 세션 로그에서 오류 없이 커밋됐는지 확인.
- 실행 목록의 녹색 표시는 "인프라 오류 없음"일 뿐 작업 성공을 보장하지 않으므로, 세션을 열어 실제 로그를 확인하세요.
