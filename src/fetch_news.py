# -*- coding: utf-8 -*-
"""종목별 최근 뉴스 기사량(버즈) 수집."""
import os
import sys
from datetime import datetime, timedelta, timezone

import naver

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

KST = timezone(timedelta(hours=9))
NEWS_URL = "https://m.stock.naver.com/api/news/stock/{code}?pageSize={n}&page=1"


def fetch_news_buzz(session, code, ref_date=None):
    """최근 NEWS_RECENT_DAYS일 기사 수 반환. 실패 시 None."""
    ref = ref_date or datetime.now(KST)
    cutoff = int((ref - timedelta(days=config.NEWS_RECENT_DAYS)).strftime("%Y%m%d"))
    data = naver.get_json(session, NEWS_URL.format(code=code, n=config.NEWS_PAGE_SIZE))
    if not isinstance(data, list):
        return None
    count = 0
    for cluster in data:
        for item in (cluster.get("items") or []):
            dt = str(item.get("datetime") or "")
            if len(dt) >= 8:
                try:
                    if int(dt[:8]) >= cutoff:
                        count += 1
                except ValueError:
                    pass
    return count


if __name__ == "__main__":
    s = naver.make_session()
    for code in ["005930", "000660", "071320"]:
        print(code, "최근%d일 기사수:" % config.NEWS_RECENT_DAYS, fetch_news_buzz(s, code))
