# -*- coding: utf-8 -*-
"""KOSPI 200 구성종목 목록 수집 (Naver KPI200 페이지)."""
import re

import naver

LIST_URL = "https://finance.naver.com/sise/entryJongmok.naver?type=KPI200&page={page}"


def fetch_constituents(session, max_pages=30):
    """[(code, name), ...] 반환. 중복 제거, 순서 유지."""
    seen = {}
    for page in range(1, max_pages + 1):
        html = naver.get_text(session, LIST_URL.format(page=page))
        if not html:
            break
        # <a href="/item/main.naver?code=005930">삼성전자</a>
        rows = re.findall(
            r'/item/main\.naver\?code=(\d{6})"[^>]*>\s*([^<]+?)\s*</a>', html
        )
        if not rows:
            break
        new = 0
        for code, name in rows:
            if code not in seen:
                seen[code] = name.strip()
                new += 1
        if new == 0:  # 더 이상 새 종목 없음 = 마지막 페이지 반복
            break
    return list(seen.items())


if __name__ == "__main__":
    s = naver.make_session()
    items = fetch_constituents(s)
    print(f"구성종목 {len(items)}개")
    for code, name in items[:10]:
        print(code, name)
