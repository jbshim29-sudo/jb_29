# -*- coding: utf-8 -*-
"""HTML 대시보드 생성: 전체 랭킹(기간탭) + 업종별 TOP3 + 스코어 설명."""
import json
import math
import os
import sys

import numpy as np
import pandas as pd
from jinja2 import Template

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config

# UI에 노출되는 기간 탭: 맨 앞에 '토탈'(종합순위) 추가
UI_PERIODS = [("토탈", "total", 0)] + list(config.PERIODS)


def _plabel(period_key):
    if period_key == "total":
        return "종합(3개월내)"
    return next((l for l, k, d in UI_PERIODS if k == period_key), period_key)


TEMPLATE = Template(r"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>KOSPI 200 저평가 종목 스크리너</title>
<style>
  :root { color-scheme: light dark; }
  * { box-sizing: border-box; }
  body { font-family:"Malgun Gothic","맑은 고딕",system-ui,sans-serif; margin:0; background:#f5f6f8; color:#1b1f24; }
  header { background:#0f2540; color:#fff; padding:18px 24px; }
  header h1 { margin:0; font-size:20px; }
  header .sub { opacity:.8; font-size:13px; margin-top:4px; }
  .nav { display:flex; gap:4px; background:#13304f; padding:0 24px; }
  .navTab { background:transparent; color:#cdd7e5; border:0; padding:12px 18px; font-size:14px; cursor:pointer; border-bottom:3px solid transparent; }
  .navTab.active { color:#fff; border-bottom-color:#4da3ff; font-weight:700; }
  .navTab:hover { color:#fff; }
  .periodBar { display:flex; gap:6px; flex-wrap:wrap; align-items:center; padding:12px 24px; background:#e9edf2; border-bottom:1px solid #dce1e8; }
  .periodBar .cap { font-size:12px; color:#5a6472; margin-right:6px; }
  .periodTab { background:#fff; border:1px solid #cfd6df; color:#333; padding:6px 12px; border-radius:16px; font-size:13px; cursor:pointer; }
  .periodTab.active { background:#0f2540; color:#fff; border-color:#0f2540; font-weight:700; }
  .periodTab[data-k="total"] { font-weight:800; border-color:#c0392b; color:#c0392b; }
  .periodTab[data-k="total"].active { background:#c0392b; border-color:#c0392b; color:#fff; }
  .wrap { padding:20px 24px 60px; }
  .cards { display:flex; gap:14px; flex-wrap:wrap; margin-bottom:20px; }
  .card { background:#fff; border-radius:10px; padding:14px 18px; box-shadow:0 1px 3px rgba(0,0,0,.08); min-width:130px; }
  .card .n { font-size:24px; font-weight:700; }
  .card .l { font-size:12px; color:#667; margin-top:2px; }
  .up { color:#c0392b; } .down { color:#2563d1; } .flat { color:#667; }
  h2 { font-size:16px; margin:22px 0 10px; }
  .tablebox { overflow-x:auto; background:#fff; border-radius:10px; box-shadow:0 1px 3px rgba(0,0,0,.08); }
  table { border-collapse:collapse; width:100%; font-size:13px; white-space:nowrap; }
  th,td { padding:8px 10px; border-bottom:1px solid #eee; text-align:right; }
  th { background:#eef1f5; position:sticky; top:0; cursor:pointer; user-select:none; }
  th:hover { background:#e2e7ee; }
  td.l,th.l { text-align:left; }
  tbody tr:hover { background:#f0f6ff; }
  .score { font-weight:700; }
  .bar { display:inline-block; height:8px; border-radius:4px; background:#2e7d32; vertical-align:middle; margin-left:6px; }
  .pos { color:#c0392b; font-weight:600; } .neg { color:#2563d1; font-weight:600; }
  .badge { padding:2px 7px; border-radius:10px; font-size:11px; }
  .b-up { background:#fdecea; color:#c0392b; } .b-down { background:#e8f0fe; color:#2563d1; } .b-flat{ background:#eee; color:#667; }
  a.code { color:#2563d1; text-decoration:none; }
  .foot { margin-top:24px; font-size:12px; color:#889; line-height:1.6; }
  /* 업종별 */
  .sectorGrid { display:grid; grid-template-columns:repeat(auto-fill,minmax(360px,1fr)); gap:14px; }
  .sectorCard { background:#fff; border-radius:10px; box-shadow:0 1px 3px rgba(0,0,0,.08); overflow:hidden; }
  .sectorCard h3 { margin:0; font-size:14px; padding:11px 14px; background:#0f2540; color:#fff; }
  .sectorCard h3 .secAvg { font-weight:700; font-size:12px; margin-left:7px; padding:1px 8px; border-radius:9px; }
  .secAvg.up { background:rgba(224,80,73,.28); color:#ffb3ad; }
  .secAvg.down { background:rgba(59,125,216,.30); color:#aecbf5; }
  .secAvg.flat { background:rgba(255,255,255,.15); color:#cfd7e2; }
  .sectorCard table { font-size:12.5px; }
  .medal { font-weight:700; }
  .m1{color:#d4af37;} .m2{color:#9aa0a6;} .m3{color:#cd7f32;}
  /* 업종별 종목 등락률 바 */
  .stList { padding:8px 12px 12px; }
  .stRow { padding:5px 2px; }
  .stRow .lab { display:flex; justify-content:space-between; align-items:baseline; font-size:12px; margin-bottom:3px; }
  .stRow .lab .nm { font-weight:600; color:#2b3138; }
  .stRow .lab .nm .rk { color:#b7bec8; font-weight:700; margin-right:5px; }
  .stRow .lab .nm .per { color:#9aa2ad; font-weight:400; font-size:10.5px; margin-left:5px; }
  .stRow .lab .pc { font-weight:700; } .stRow .lab .pc.up{color:#c0392b;} .stRow .lab .pc.down{color:#2563d1;}
  .stRow .track { background:#eef1f5; border-radius:5px; height:10px; overflow:hidden; }
  .stRow .fill { height:100%; border-radius:5px; }
  .stRow .fill.up { background:linear-gradient(90deg,#f0a39c,#c0392b); }
  .stRow .fill.down { background:linear-gradient(90deg,#a9c6f0,#2563d1); }
  /* 설명 페이지 */
  .doc { background:#fff; border-radius:10px; box-shadow:0 1px 3px rgba(0,0,0,.08); padding:26px 30px; max-width:900px; line-height:1.7; }
  .doc h2 { margin-top:26px; } .doc h2:first-child { margin-top:0; }
  .doc p, .doc li { font-size:14px; color:#2b3138; }
  .doc code { background:#eef1f5; padding:1px 6px; border-radius:4px; }
  .formula { background:#0f2540; color:#fff; padding:14px 18px; border-radius:8px; font-size:14px; overflow-x:auto; }
  .wtable { border-collapse:collapse; margin:10px 0; }
  .wtable th,.wtable td { border:1px solid #e2e6ec; padding:7px 12px; text-align:left; font-size:13px; }
  .wtable th { background:#eef1f5; }

  /* ===== 요약 대시보드 (화이트) ===== */
  .statRow { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-bottom:18px; }
  .stat { background:#fff; border:1px solid #e7ebf0; border-radius:12px; padding:16px 18px; box-shadow:0 1px 3px rgba(0,0,0,.05); }
  .stat .t { font-size:12px; color:#8a93a0; margin-bottom:8px; }
  .stat .v { font-size:28px; font-weight:800; letter-spacing:-.5px; }
  .stat .v .u { font-size:15px; font-weight:600; color:#6b7480; margin-left:2px; }
  .stat .s { font-size:12.5px; margin-top:5px; color:#7b8492; }
  .stat .s.up { color:#c0392b; font-weight:700; } .stat .s.down { color:#2563d1; font-weight:700; }
  .panels { display:grid; grid-template-columns:1.35fr 1fr; gap:16px; margin-bottom:16px; }
  @media(max-width:1000px){ .statRow{grid-template-columns:repeat(2,1fr);} .panels{grid-template-columns:1fr;} }
  .panel { background:#fff; border:1px solid #e7ebf0; border-radius:12px; box-shadow:0 1px 3px rgba(0,0,0,.05); }
  .panel .ph { display:flex; justify-content:space-between; align-items:center; padding:13px 16px; border-bottom:1px solid #eef1f4; }
  .panel .ph b { font-size:14.5px; } .panel .ph .hint { font-size:11.5px; color:#9aa2ad; }
  .panel .pb { padding:6px 8px 12px; }
  .t10 { width:100%; border-collapse:collapse; font-size:13px; }
  .t10 th,.t10 td { padding:8px 10px; border-bottom:1px solid #f0f2f5; white-space:nowrap; }
  .t10 th { color:#8a93a0; font-weight:600; font-size:11.5px; text-align:right; }
  .t10 th.l,.t10 td.l { text-align:left; } .t10 td { text-align:right; }
  .t10 tbody tr:hover { background:#f7faff; }
  .t10 .nm { font-weight:700; } .t10 .sec { font-size:11px; color:#9aa2ad; }
  .t10 .rk { color:#b7bec8; font-weight:700; width:26px; }
  .sig { display:inline-block; min-width:30px; padding:2px 8px; border-radius:6px; font-weight:800; font-size:12px; color:#fff; }
  .sig.s1{background:#c0392b;} .sig.s2{background:#e0733a;} .sig.s3{background:#e0a92e;} .sig.s4{background:#8b93a1;}
  .sret.up{color:#c0392b;font-weight:700;} .sret.down{color:#2563d1;font-weight:700;}
  /* 섹터 강도 바 */
  .sbar { display:grid; grid-template-columns:96px 1fr 34px; align-items:center; gap:10px; padding:6px 14px; }
  .sbar .nm { font-size:12.5px; font-weight:600; } .sbar .nm small{ display:block; color:#9aa2ad; font-weight:400; font-size:10.5px; }
  .sbar .track { background:#eef1f5; border-radius:6px; height:12px; overflow:hidden; }
  .sbar .fill { height:100%; border-radius:6px; }
  .sbar .fill.pos{ background:linear-gradient(90deg,#f6c65a,#e08a2e); }
  .sbar .fill.neg{ background:linear-gradient(90deg,#8fb6ea,#3b7dd8); }
  .sbar .sc { font-size:12.5px; font-weight:800; text-align:right; }
  /* 버블맵 */
  .bubbleWrap { padding:8px 12px 14px; overflow-x:auto; }
  .bubbleWrap svg { display:block; min-width:820px; width:100%; height:auto; }
  .blegend { display:flex; gap:16px; flex-wrap:wrap; font-size:12px; color:#6b7480; padding:0 16px 12px; }
  .blegend i { display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:5px; vertical-align:middle; }
  .bub { cursor:pointer; transition:fill-opacity .1s; }
  .bub:hover { fill-opacity:0.95 !important; stroke:#0f2540; stroke-width:1.5; }
  .bubTip { position:absolute; display:none; z-index:999; pointer-events:none; background:#0f2540; color:#fff;
            padding:6px 10px; border-radius:7px; font-size:12px; line-height:1.4; box-shadow:0 2px 8px rgba(0,0,0,.25); white-space:nowrap; }
  .bubTip b { font-size:13px; }
  /* ETF 카드 */
  .etfGrid { display:grid; grid-template-columns:repeat(3,1fr); gap:14px; }
  @media(max-width:1000px){ .etfGrid{grid-template-columns:1fr;} }
  .etf { background:#fff; border:1px solid #e7ebf0; border-radius:12px; padding:14px 16px; box-shadow:0 1px 3px rgba(0,0,0,.05); }
  .etf .en { font-weight:700; font-size:14px; } .etf .tag { display:inline-block; margin-top:4px; font-size:11px; color:#7b8492; background:#f0f2f5; padding:1px 7px; border-radius:5px; }
  .etf .er { font-size:22px; font-weight:800; margin:8px 0 4px; }
  .etf .er.up{color:#c0392b;} .etf .er.down{color:#2563d1;}
  .etf .foot { display:flex; justify-content:space-between; align-items:center; font-size:11px; color:#9aa2ad; }
  .etf .track { background:#eef1f5; border-radius:5px; height:8px; margin-top:8px; overflow:hidden; }
  .etf .track .fill { height:100%; background:linear-gradient(90deg,#f6c65a,#e08a2e); border-radius:5px; }
  /* ETF 페이지 탭 */
  .etfTabs { display:flex; gap:8px; align-items:center; margin-bottom:16px; }
  .etfTab { background:#fff; border:1px solid #cfd6df; color:#333; padding:8px 16px; border-radius:8px; font-size:13.5px; cursor:pointer; font-weight:600; }
  .etfTab.active { background:#0f2540; color:#fff; border-color:#0f2540; }
  .etfPTab { background:#fff; border:1px solid #cfd6df; color:#333; padding:6px 13px; border-radius:16px; font-size:13px; cursor:pointer; }
  .etfPTab.active { background:#c0392b; color:#fff; border-color:#c0392b; font-weight:700; }
  .etfNote { font-size:12px; color:#9aa2ad; margin-left:6px; }
  .levTag { font-size:10px; background:#fbeaea; color:#c0392b; padding:1px 5px; border-radius:4px; margin-left:4px; }
  .etfTable td.l .nm { font-weight:600; }
</style>
</head>
<body>
<div id="bubTip" class="bubTip"></div>
<header>
  <h1>KOSPI 200 저평가 종목 스크리너</h1>
  <div class="sub">데이터 출처: 네이버 금융 · 생성 시각: {{ generated }} · 종목 수: {{ total }}개</div>
</header>

<div class="nav">
  <button class="navTab active" data-v="summary" onclick="showView('summary')">📊 요약 대시보드</button>
  <button class="navTab" data-v="rank" onclick="showView('rank')">💎 저평가 전체 랭킹</button>
  <button class="navTab" data-v="sector" onclick="showView('sector')">🏭 업종별 TOP3</button>
  <button class="navTab" data-v="etf" onclick="showView('etf')">📦 ETF 등락률</button>
  <button class="navTab" data-v="score" onclick="showView('score')">📐 스코어 산정 방식</button>
</div>

<div class="periodBar" id="periodBar">
  <span class="cap">순위 기준 (<b style="color:#c0392b">토탈</b>=3개월내 종합·저평가전환 가중 / 개별 기간 선택 시 그 기간 기준 재정렬)</span>
  {% for label, key, days in periods %}
  <button class="periodTab" data-k="{{ key }}" onclick="applyPeriod('{{ key }}')">{{ label }}</button>
  {% endfor %}
</div>

<div class="wrap">
  <!-- ============ 요약 대시보드 ============ -->
  <div class="view" id="view-summary">
    <div class="statRow">
      <div class="stat">
        <div class="t">KOSPI 200 지수</div>
        <div class="v">{{ sdef.index.value }}</div>
        <div class="s {{ 'up' if sdef.index.up else 'down' }}">{{ '▲' if sdef.index.up else '▼' }} {{ sdef.index.change }} ({{ sdef.index.rate }}%)</div>
      </div>
      <div class="stat">
        <div class="t">상승 종목 비율 (<span id="sumPlabel">{{ sdef.period_label }}</span> 누적)</div>
        <div class="v"><span id="sumUp">{{ sdef.up_cnt }}</span> <span class="u">/ {{ sdef.total }}</span></div>
        <div class="s" id="sumBreadth">시장 폭</div>
      </div>
      <div class="stat">
        <div class="t">평균 PER</div>
        <div class="v">{{ sdef.avg_per }}<span class="u">배</span></div>
        <div class="s">중앙값 {{ sdef.med_per }}배</div>
      </div>
      <div class="stat">
        <div class="t">평균 PBR</div>
        <div class="v">{{ sdef.avg_pbr }}<span class="u">배</span></div>
        <div class="s">중앙값 {{ sdef.med_pbr }}배</div>
      </div>
    </div>

    {% for pkey, s in sum_list %}
    <div class="sumBlock" data-k="{{ pkey }}" style="display:none">
      <div class="panels">
        <div class="panel">
          <div class="ph"><b>💡 유망종목 TOP 10</b><span class="hint">종합 스코어 상위 · {{ s.period_label }} 누적상승률</span></div>
          <div class="pb">
            <table class="t10">
              <thead><tr><th class="l">#</th><th class="l">종목 / 섹터</th><th>누적상승률</th><th>PER</th><th>PBR</th><th>시그널</th></tr></thead>
              <tbody>
              {% for r in s.top10 %}
                <tr>
                  <td class="l rk">{{ r.rank }}</td>
                  <td class="l"><span class="nm"><a class="code" href="https://finance.naver.com/item/main.naver?code={{ r.code }}" target="_blank">{{ r.name }}</a></span><span class="sec">{{ r.industry }}</span></td>
                  <td class="sret {{ 'up' if r.ret_raw is not none and r.ret_raw>0 else 'down' }}">{{ r.ret }}</td>
                  <td>{{ r.per }}</td><td>{{ r.pbr }}</td>
                  <td><span class="sig {{ r.sig_class }}">{{ r.sig }}</span></td>
                </tr>
              {% endfor %}
              </tbody>
            </table>
          </div>
        </div>
        <div class="panel">
          <div class="ph"><b>🏭 섹터 강도 랭킹</b><span class="hint">{{ s.period_label }} 평균 상승률 기준</span></div>
          <div class="pb">
            {% for sc in s.sectors %}
            <div class="sbar">
              <div class="nm">{{ sc.name }}<small>평균 {{ sc.avg }}</small></div>
              <div class="track"><div class="fill {{ 'pos' if sc.pos else 'neg' }}" style="width:{{ sc.width }}%"></div></div>
              <div class="sc">{{ sc.strength }}</div>
            </div>
            {% endfor %}
          </div>
        </div>
      </div>
      <div class="panel" style="margin-bottom:16px">
        <div class="ph"><b>🫧 밸류에이션 맵 — PER vs {{ s.period_label }} 누적상승률</b><span class="hint">버블 크기 = 시가총액</span></div>
        <div class="bubbleWrap">{{ s.svg }}</div>
        <div class="blegend">
          <span><i style="background:#d9534f"></i>상승 종목</span>
          <span><i style="background:#3b7dd8"></i>하락 종목</span>
          <span><i style="background:#e0a92e"></i>유망 구간 (저PER + 상승)</span>
          <span>버블 크기 = 시가총액</span>
        </div>
      </div>
    </div>
    {% endfor %}
    <div class="foot">⚠️ 개인 투자 참고용(네이버 금융 공개 데이터 가공). 누적상승률은 상단에서 선택한 기간 기준입니다. 투자 판단·책임은 이용자 본인에게 있습니다.</div>
  </div>

  <!-- ============ ETF 등락률 ============ -->
  <div class="view" id="view-etf" style="display:none">
    <div class="etfTabs">
      <button class="etfTab active" data-c="total" onclick="etfSetCat('total')">토탈</button>
      <button class="etfTab" data-c="lev" onclick="etfSetCat('lev')">레버리지 / 인버스</button>
      <button class="etfTab" data-c="normal" onclick="etfSetCat('normal')">일반</button>
      <span class="etfNote" id="etfCount"></span>
    </div>
    <div class="etfTabs">
      <span style="font-size:12px;color:#8a93a0;margin-right:2px;align-self:center">기간</span>
      <button class="etfPTab active" data-p="d1" onclick="etfSetPeriod('d1')">당일</button>
      <button class="etfPTab" data-p="w1" onclick="etfSetPeriod('w1')">1주</button>
      <button class="etfPTab" data-p="w2" onclick="etfSetPeriod('w2')">2주</button>
      <button class="etfPTab" data-p="w3" onclick="etfSetPeriod('w3')">3주</button>
      <button class="etfPTab" data-p="m1" onclick="etfSetPeriod('m1')">1개월</button>
      <button class="etfPTab" data-p="m3" onclick="etfSetPeriod('m3')">3개월</button>
    </div>
    <div class="panels">
      <div class="panel">
        <div class="ph"><b>📈 상승률 상위</b><span class="hint">선택 기간 등락률 기준 · 국내 주식형 ETF</span></div>
        <div class="pb"><table class="t10 etfTable"><thead><tr>
          <th class="l">#</th><th class="l">ETF</th><th>등락률</th><th>종합</th><th>거래대금</th>
        </tr></thead><tbody id="etfUp"></tbody></table></div>
      </div>
      <div class="panel">
        <div class="ph"><b>📉 하락률 상위</b><span class="hint">선택 기간 등락률 기준 · 국내 주식형 ETF</span></div>
        <div class="pb"><table class="t10 etfTable"><thead><tr>
          <th class="l">#</th><th class="l">ETF</th><th>등락률</th><th>종합</th><th>거래대금</th>
        </tr></thead><tbody id="etfDown"></tbody></table></div>
      </div>
    </div>
    <div class="foot">⚠️ 개인 투자 참고용. 국내 주식형 ETF(시장지수·업종/테마·레버리지/인버스) 중 유동성 있는 종목만 표시. 일간 등락률·3개월 수익률은 네이버 금융 기준입니다.</div>
  </div>

  <!-- ============ 전체 랭킹 ============ -->
  <div class="view" id="view-rank" style="display:none">
    <div class="cards">
      <div class="card"><div class="n up" id="upCnt">0</div><div class="l"><span id="periodLabel"></span> 상승</div></div>
      <div class="card"><div class="n down" id="downCnt">0</div><div class="l">하락</div></div>
      <div class="card"><div class="n flat" id="flatCnt">0</div><div class="l">보합/정보없음</div></div>
      <div class="card"><div class="n" id="topName">{{ top_name }}</div><div class="l">종합 1위 (스코어 <span id="topScore">{{ top_score }}</span>)</div></div>
    </div>
    <div class="tablebox">
      <table id="rankTable">
        <thead><tr>
          <th data-t="num">순위</th><th class="l" data-t="str">종목명</th><th class="l" data-t="str">코드</th>
          <th class="l" data-t="str">업종</th><th data-t="num">종합<br>스코어</th>
          <th data-t="num">PER</th><th data-t="num">PBR</th><th data-t="num">ROE(%)</th>
          <th data-t="num">영업이익<br>증가율(%)</th><th data-t="num">모멘텀<br>(1·3개월)</th>
          <th data-t="num">뉴스<br>(7일)</th>
          <th data-t="num">시총<br>순위</th><th data-t="num">등락(%)</th><th class="l" data-t="str">추세</th>
        </tr></thead>
        <tbody>
        {% for r in rows %}
          <tr class="dyn-row rankRow"{% for label,key,days in periods %} data-{{key}}="{{ r.rets[key] if r.rets[key] is not none else '' }}" data-sc-{{key}}="{{ r.pdata[key].sc if r.pdata[key].sc is not none else '' }}" data-rk-{{key}}="{{ r.pdata[key].rk if r.pdata[key].rk is not none else '' }}" data-mo-{{key}}="{{ r.pdata[key].mo if r.pdata[key].mo is not none else '' }}"{% endfor %}>
            <td class="rankCell">{{ r.rank }}</td>
            <td class="l">{{ r.name }}</td>
            <td class="l"><a class="code" href="https://finance.naver.com/item/main.naver?code={{ r.code }}" target="_blank">{{ r.code }}</a></td>
            <td class="l">{{ r.industry }}</td>
            <td class="score"><span class="scoreVal">{{ r.score }}</span><span class="bar" style="width:{{ r.barw }}px"></span></td>
            <td>{{ r.per }}</td><td>{{ r.pbr }}</td><td>{{ r.roe }}</td>
            <td class="{{ 'pos' if r.op_growth_raw is not none and r.op_growth_raw>0 else ('neg' if r.op_growth_raw is not none and r.op_growth_raw<0 else '') }}">{{ r.op_growth }}</td>
            <td class="momCell">{{ r.momentum }}</td>
            <td>{{ r.news_buzz }}</td>
            <td>{{ r.market_cap_rank }}</td>
            <td class="retCell">-</td>
            <td class="l trendCell"></td>
          </tr>
        {% endfor %}
        </tbody>
      </table>
    </div>
    <div class="foot">
      ⚠️ 개인 투자 참고용(네이버 금융 공개 데이터 가공). 투자 판단·책임은 이용자 본인에게 있습니다. · 표 헤더 클릭 시 정렬됩니다.
    </div>
  </div>

  <!-- ============ 업종별 종목 등락률 ============ -->
  <div class="view" id="view-sector" style="display:none">
    <h2>업종별 종목 등락률 — 선택 기간 · 상승률 순</h2>
    <div class="sectorGrid" id="sectorGrid"></div>
    <div class="foot">각 업종 내 종목을 <b>선택한 기간의 등락률 높은 순</b>으로 정렬한 막대입니다. 막대 길이는 업종 내 최대 변동폭 기준 상대값이며, 상단 기간 탭(토탈 포함)이 함께 적용됩니다. 업종 카드는 평균 등락률이 높은 순으로 배치됩니다.</div>
  </div>

  <!-- ============ 스코어 산정 방식 ============ -->
  <div class="view" id="view-score" style="display:none">
    <div class="doc">
      <h2>종합 스코어는 어떻게 만들어졌나</h2>
      <p>초기 버전은 <b>저평가(가치) 지표만</b> 봤기 때문에, “싸지만 계속 빠지는” <b>가치 함정</b> 종목이
         1위가 되는 문제가 있었습니다. 이를 바로잡기 위해 <b>가치 · 성장 · 추세(모멘텀) · 관심도</b>를
         함께 보는 7개 팩터로 재설계했습니다. 싼 것만이 아니라 <b>싸면서 실적이 늘고, 주가가 돌기 시작하며,
         업종·시장의 관심을 받는</b> 종목이 상위에 오도록 했습니다.</p>

      <h2>0. 토탈(종합) 순위 · 저평가→상승 전환 가중치</h2>
      <p>기간 탭 맨 앞의 <b style="color:#c0392b">토탈</b>은 여러 기간을 묶은 <b>종합순위</b>입니다.
         당일·3일·1주·2주·1개월·3개월 등락률을 가중 평균한 <b>종합 모멘텀</b>(6개월은 제외, 3개월까지만 반영)을
         기반으로 아래 7개 팩터를 계산하고, 여기에 <b>‘저평가 → 상승 전환’ 가중치({{ trans_w }})</b>를 더합니다.</p>
      <ul>
        <li><b>저평가 → 상승 전환</b>: 밸류에이션이 싸면서(저PER·저PBR), 최근 1~2주 상승이 1~3개월 흐름보다
            <b>가속(turn-up)</b>되는 종목에 가점합니다. “싸다가 이제 막 오르기 시작하는” 구간을 잡기 위한 지표입니다.</li>
        <li>기간 탭을 개별 기간(당일·1주일 등)으로 바꾸면 그 기간 기준 순위로, <b>토탈</b>이면 위 종합 기준으로 재정렬됩니다.</li>
      </ul>

      <h2>1. 7개 팩터와 방향</h2>
      <table class="wtable">
        <tr><th>팩터</th><th>의미 / 반영한 요청</th><th>좋은 방향</th><th>가중치</th></tr>
        <tr><td>PER</td><td>가치 · 저평가</td><td>낮을수록 ▲</td><td>{{ w.per }}</td></tr>
        <tr><td>PBR</td><td>가치 · 저평가</td><td>낮을수록 ▲</td><td>{{ w.pbr }}</td></tr>
        <tr><td>ROE</td><td>수익성 · 자본효율</td><td>높을수록 ▲</td><td>{{ w.roe }}</td></tr>
        <tr><td>성장대비 저평가 (PEG류)</td><td>영업이익 증가율 대비 아직 싼가 = 영업이익증가율 ÷ PER</td><td>높을수록 ▲</td><td>{{ w.peg }}</td></tr>
        <tr><td>가격 모멘텀</td><td>최근 1·3개월 상승 추세 (하락 종목 감점 = 가치함정 회피)</td><td>높을수록 ▲</td><td>{{ w.momentum }}</td></tr>
        <tr><td>업종 모멘텀</td><td>같은 업종의 평균 상승 (뜨는 업종 우대)</td><td>높을수록 ▲</td><td>{{ w.sector_mom }}</td></tr>
        <tr><td>대형주 상승 보너스</td><td>시가총액 상위 종목이 오를 때 가점 (시총순위 × 모멘텀)</td><td>높을수록 ▲</td><td>{{ w.largecap_mom }}</td></tr>
        <tr><td>뉴스 버즈</td><td>최근 7일 기사량 = 시장 관심도/전망 프록시</td><td>많을수록 ▲</td><td>{{ w.news_buzz }}</td></tr>
      </table>

      <h2>2. 각 팩터가 반영한 요청</h2>
      <ul>
        <li><b>① 최근 상승하는 업종 우대</b> → <b>업종 모멘텀</b> 팩터 (같은 업종 종목들의 평균 상승률).</li>
        <li><b>② 시총 큰 종목이 크게 오를 때 가점</b> → <b>대형주 상승 보너스</b> (시가총액 백분위 × 모멘텀).</li>
        <li><b>③ 영업이익 증가율 대비 저평가</b> → <b>성장대비 저평가(PEG류)</b> = 영업이익증가율 ÷ PER. 성장은 큰데 아직 싼 종목일수록 고득점.</li>
        <li><b>④ 전망 좋은/관심 많은 업종·업체</b> → <b>뉴스 버즈</b> (네이버 최근 기사량). ※ 기사 “내용의 긍정/부정”까지는 아직 판단하지 않고, 관심도(양)만 반영합니다.</li>
        <li>추가로 <b>가격 모멘텀</b>을 넣어, 아무리 싸도 <b>주가가 계속 빠지는 종목은 감점</b>되도록 했습니다(핵심 개선).</li>
      </ul>

      <h2>3. 백분위 정규화 & 합산</h2>
      <p>단위가 제각각인 팩터(PER 배, ROE %, 기사 수 …)를 그대로 더할 수 없어,
         각 팩터를 <b>KOSPI 200 안에서의 순위 백분위(0~100점)</b>로 변환한 뒤 가중 평균합니다.</p>
      <div class="formula">
        종합 스코어 = Σ ( 팩터별 백분위점수 × 가중치 ) ÷ {{ w_total }}&nbsp;&nbsp;→ 0~100
      </div>
      <p>높을수록 투자 우선순위가 앞섭니다. 가격/업종 모멘텀 컬럼은 랭킹 표에서 직접 확인할 수 있습니다.</p>

      <h2>4. 예외 처리</h2>
      <ul>
        <li>PER·PBR이 <b>0 이하</b>(적자·자본잠식)이거나 결측이면 해당 팩터 <b>최하위(0점)</b>.</li>
        <li>PEG는 <b>PER·영업이익증가율이 모두 양수</b>일 때만 계산(그 외 0점).</li>
        <li>모멘텀·업종모멘텀·뉴스 등 결측치는 해당 팩터만 0점, 나머지는 정상 반영.</li>
      </ul>

      <h2>5. 한계와 올바른 사용</h2>
      <ul>
        <li><b>상대평가</b>입니다. 시장 전체가 하락해도 “상대적으로 나은” 순위는 나옵니다.</li>
        <li>뉴스 버즈는 <b>기사 수(관심도)</b>일 뿐, 호재/악재 방향은 구분하지 않습니다. 상위 종목은 실제 기사를 직접 확인하세요.</li>
        <li>모멘텀 비중이 커진 만큼 <b>단기 추세에 민감</b>합니다. 급등 후 고점 매수 위험에 유의하세요.</li>
        <li>과거 확정 실적·최근 주가 기반이며 미래를 보장하지 않습니다. <b>참고 지표</b>로만 활용하세요.</li>
      </ul>
      <p>가중치는 <code>config.py</code>의 <code>SCORE_WEIGHTS</code>에서 조정할 수 있고, 변경 후 재실행하면 이 페이지 숫자도 함께 갱신됩니다.</p>
    </div>
  </div>
</div>

<script>
  function showView(v){
    document.querySelectorAll('.view').forEach(function(x){ x.style.display='none'; });
    document.getElementById('view-'+v).style.display='block';
    document.querySelectorAll('.navTab').forEach(function(b){ b.classList.toggle('active', b.dataset.v===v); });
    document.getElementById('periodBar').style.display = (v==='score' || v==='etf') ? 'none' : 'flex';
    if(v==='etf' && !document.getElementById('etfUp').innerHTML){ renderEtf(); }
  }

  // ---- 업종별 종목 등락률 ----
  var SECTORS = {{ sectors_json }};
  function renderSectors(key){
    var grid=document.getElementById('sectorGrid'); if(!grid) return;
    var barMax=1;
    SECTORS.forEach(function(s){ s.stocks.forEach(function(st){ var v=st.rets[key]; if(v!==null&&v!==undefined&&Math.abs(v)>barMax) barMax=Math.abs(v); }); });
    var cards = SECTORS.map(function(s){
      var vals = s.stocks.map(function(st){return st.rets[key];}).filter(function(v){return v!==null&&v!==undefined;});
      var avg = vals.length? vals.reduce(function(a,b){return a+b;},0)/vals.length : -Infinity;
      return {s:s, avg:avg};
    });
    cards.sort(function(a,b){ return b.avg-a.avg; });
    grid.innerHTML = cards.map(function(c){
      var s=c.s;
      var stocks = s.stocks.slice().sort(function(a,b){
        var x=a.rets[key], y=b.rets[key];
        x=(x===null||x===undefined)?-Infinity:x; y=(y===null||y===undefined)?-Infinity:y; return y-x;
      });
      var rows = stocks.map(function(st,i){
        var v=st.rets[key], has=(v!==null&&v!==undefined), up=has&&v>0;
        var w = has? Math.max(2, Math.min(100, Math.abs(v)/barMax*100)) : 0;
        var pc = has? ((v>0?'+':'')+v.toFixed(2)+'%') : '-';
        var per = (st.per!==null&&st.per!==undefined)? '<span class="per">PER '+st.per+'</span>' : '';
        return '<div class="stRow"><div class="lab">'+
          '<span class="nm"><span class="rk">'+(i+1)+'</span>'+
          '<a class="code" target="_blank" href="https://finance.naver.com/item/main.naver?code='+st.code+'">'+st.name+'</a>'+per+'</span>'+
          '<span class="pc '+(up?'up':(has&&v<0?'down':''))+'">'+pc+'</span></div>'+
          '<div class="track"><div class="fill '+(up?'up':'down')+'" style="width:'+w+'%"></div></div></div>';
      }).join('');
      var avgOk = c.avg!==-Infinity && isFinite(c.avg);
      var avgCls = !avgOk?'flat':(c.avg>0?'up':(c.avg<0?'down':'flat'));
      var avgTxt = !avgOk?'-':((c.avg>0?'+':'')+c.avg.toFixed(2)+'%');
      return '<div class="sectorCard"><h3>'+s.name+
        ' <span style="opacity:.7;font-weight:400">· '+s.count+'종목</span>'+
        ' <span class="secAvg '+avgCls+'">평균 '+avgTxt+'</span></h3>'+
        '<div class="stList">'+rows+'</div></div>';
    }).join('');
  }

  // ---- ETF 페이지 ----
  var ETFS = {{ etf_json }};
  function etfPct(v){ if(v===null||v===undefined) return '-'; return (v>0?'+':'')+v.toFixed(2)+'%'; }
  function etfAmt(v){ if(v===null||v===undefined) return '-'; return v>=10000?(v/10000).toFixed(1)+'조':Math.round(v).toLocaleString()+'억'; }
  function etfSig(sc){
    if(sc===null||sc===undefined) return '<span class="sig s4">-</span>';
    var c = sc>=75?'s1':(sc>=60?'s2':(sc>=45?'s3':'s4'));
    return '<span class="sig '+c+'">'+sc+'</span>';
  }
  var etfCat='total', etfPeriod='d1';
  function etfR(e){ return (e.rets && e.rets[etfPeriod]!==undefined) ? e.rets[etfPeriod] : null; }
  function etfRow(e,i){
    var lev = e.lev ? ' <span class="levTag">레버리지</span>' : '';
    var v = etfR(e);
    var chgc = (v>0)?'sret up':((v<0)?'sret down':'');
    return '<tr><td class="l rk">'+(i+1)+'</td>'+
      '<td class="l"><span class="nm"><a class="code" target="_blank" href="https://finance.naver.com/item/main.naver?code='+e.code+'">'+e.name+'</a></span>'+lev+'</td>'+
      '<td class="'+chgc+'">'+etfPct(v)+'</td>'+
      '<td>'+etfSig(e.sc)+'</td>'+
      '<td>'+etfAmt(e.amt)+'</td></tr>';
  }
  function etfSetCat(c){ etfCat=c; renderEtf(); }
  function etfSetPeriod(p){ etfPeriod=p; renderEtf(); }
  function renderEtf(){
    document.querySelectorAll('.etfTab').forEach(function(b){ b.classList.toggle('active', b.dataset.c===etfCat); });
    document.querySelectorAll('.etfPTab').forEach(function(b){ b.classList.toggle('active', b.dataset.p===etfPeriod); });
    var list = ETFS.filter(function(e){ return etfCat==='total' ? true : (etfCat==='lev'?e.lev:!e.lev); });
    var withR = list.filter(function(e){ var v=etfR(e); return v!==null && v!==undefined; });
    var up = withR.slice().sort(function(a,b){ return etfR(b)-etfR(a); }).slice(0,20);
    var down = withR.slice().sort(function(a,b){ return etfR(a)-etfR(b); }).slice(0,20);
    document.getElementById('etfUp').innerHTML = up.map(etfRow).join('');
    document.getElementById('etfDown').innerHTML = down.map(etfRow).join('');
    var c=document.getElementById('etfCount'); if(c) c.textContent='총 '+list.length+'개';
  }
  var SUM_UP = {{ up_by_period }};
  var SUM_TOTAL = {{ sdef.total }};

  function numAttr(tr, attr){ var v=tr.getAttribute(attr); return (v===null||v==='')?null:parseFloat(v); }

  function applyPeriod(key){
    document.querySelectorAll('.periodTab').forEach(function(b){ b.classList.toggle('active', b.dataset.k===key); });
    var plabel='';
    document.querySelectorAll('.periodTab').forEach(function(b){ if(b.dataset.k===key) plabel=b.textContent; });
    var lab=document.getElementById('periodLabel');
    if(lab) lab.textContent=plabel;

    // 요약 대시보드: 기간 블록 토글 + 상승비율 카드 갱신
    document.querySelectorAll('.sumBlock').forEach(function(b){ b.style.display = (b.dataset.k===key)?'block':'none'; });
    renderSectors(key);  // 업종별 등락률 바 재구성
    var su=document.getElementById('sumUp'), sl=document.getElementById('sumPlabel'), sb=document.getElementById('sumBreadth');
    if(sl) sl.textContent=plabel;
    if(su && SUM_UP[key]!==undefined){
      var uc=SUM_UP[key]; su.textContent=uc;
      if(sb){ var win=uc*2>=SUM_TOTAL; sb.textContent=win?'상승 우위 시장':'하락 우위 시장'; sb.className='s '+(win?'up':'down'); }
    }

    // 1) 모든 표의 등락/추세 셀 갱신 (랭킹 + 업종별)
    document.querySelectorAll('.dyn-row').forEach(function(tr){
      var raw = tr.getAttribute('data-'+key);
      var cell = tr.querySelector('.retCell');
      var badge = tr.querySelector('.trendCell');
      if(raw===null || raw===''){
        if(cell){ cell.textContent='-'; cell.className='retCell'; }
        if(badge){ badge.innerHTML='<span class="badge b-flat">정보없음</span>'; }
        return;
      }
      var n=parseFloat(raw);
      if(cell){ cell.textContent=(n>0?'+':'')+n.toFixed(2); cell.className='retCell '+(n>0?'pos':(n<0?'neg':'')); }
      if(badge){
        var t=n>0?'상승':(n<0?'하락':'보합');
        var cls=n>0?'b-up':(n<0?'b-down':'b-flat');
        badge.innerHTML='<span class="badge '+cls+'">'+t+'</span>';
      }
    });

    // 2) 랭킹표: 기간별 스코어/순위/모멘텀 갱신 후 스코어 내림차순 재정렬
    var tbody=document.querySelector('#rankTable tbody');
    var rows=[].slice.call(tbody.querySelectorAll('tr.rankRow'));
    var maxSc=1;
    rows.forEach(function(tr){ var sc=numAttr(tr,'data-sc-'+key); if(sc!==null && sc>maxSc) maxSc=sc; });
    rows.forEach(function(tr){
      var sc=numAttr(tr,'data-sc-'+key), rk=tr.getAttribute('data-rk-'+key), mo=numAttr(tr,'data-mo-'+key);
      var sv=tr.querySelector('.scoreVal'), bar=tr.querySelector('.bar'), rc=tr.querySelector('.rankCell'), mc=tr.querySelector('.momCell');
      if(sv) sv.textContent=(sc===null?'-':sc.toFixed(1));
      if(bar) bar.style.width=(sc===null?0:Math.round(sc/maxSc*60))+'px';
      if(rc) rc.textContent=(rk===null||rk===''?'-':rk);
      if(mc){ mc.textContent=(mo===null?'-':(mo>0?'+':'')+mo.toFixed(1)); mc.className='momCell '+(mo===null?'':(mo>0?'pos':(mo<0?'neg':''))); }
    });
    rows.sort(function(a,b){ var x=numAttr(a,'data-sc-'+key), y=numAttr(b,'data-sc-'+key); x=(x===null?-Infinity:x); y=(y===null?-Infinity:y); return y-x; });
    rows.forEach(function(tr){ tbody.appendChild(tr); });

    // 상단 '종합 1위' 카드 갱신
    if(rows.length){
      var tn=document.getElementById('topName'), ts=document.getElementById('topScore');
      if(tn) tn.textContent=rows[0].cells[1].innerText;
      if(ts){ var s0=numAttr(rows[0],'data-sc-'+key); ts.textContent=(s0===null?'-':s0.toFixed(1)); }
    }

    // 3) 요약 카운트
    var up=0,down=0,flat=0;
    rows.forEach(function(tr){
      var raw=tr.getAttribute('data-'+key);
      if(raw===null||raw===''){ flat++; return; }
      var n=parseFloat(raw); if(n>0)up++; else if(n<0)down++; else flat++;
    });
    var e;
    if(e=document.getElementById('upCnt')) e.textContent=up;
    if(e=document.getElementById('downCnt')) e.textContent=down;
    if(e=document.getElementById('flatCnt')) e.textContent=flat;
  }
  // 헤더 클릭 정렬 (랭킹 표)
  document.querySelectorAll('#rankTable thead th').forEach(function(th, idx){
    th.addEventListener('click', function(){
      var tbody=document.querySelector('#rankTable tbody');
      var rows=[].slice.call(tbody.rows);
      var type=th.dataset.t; var asc=th._asc=!th._asc;
      rows.sort(function(a,b){
        var x=a.cells[idx].innerText.trim(), y=b.cells[idx].innerText.trim();
        if(type==='num'){
          var nx=parseFloat(x.replace(/[^0-9.\-]/g,'')), ny=parseFloat(y.replace(/[^0-9.\-]/g,''));
          nx=isNaN(nx)?-Infinity:nx; ny=isNaN(ny)?-Infinity:ny;
          return asc?nx-ny:ny-nx;
        }
        return asc?x.localeCompare(y,'ko'):y.localeCompare(x,'ko');
      });
      rows.forEach(function(r){ tbody.appendChild(r); });
    });
  });
  // ---- 버블맵 마우스오버 툴팁 ----
  (function(){
    var tip=document.getElementById('bubTip');
    function isBub(t){ return t && t.classList && t.classList.contains('bub'); }
    document.addEventListener('mouseover', function(e){
      if(isBub(e.target)){
        tip.innerHTML='<b>'+e.target.getAttribute('data-nm')+'</b><br>PER '+e.target.getAttribute('data-per')+' · 등락 '+e.target.getAttribute('data-ret')+'%';
        tip.style.display='block';
      }
    });
    document.addEventListener('mousemove', function(e){
      if(tip.style.display==='block'){ tip.style.left=(e.pageX+12)+'px'; tip.style.top=(e.pageY+14)+'px'; }
    });
    document.addEventListener('mouseout', function(e){ if(isBub(e.target)) tip.style.display='none'; });
  })();

  // 초기화
  applyPeriod('{{ default_key }}');
  showView('summary');
</script>
</body>
</html>""")


def _fmt(v, nd=2):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "-"
    if isinstance(v, float):
        return f"{v:,.{nd}f}"
    return f"{v:,}" if isinstance(v, int) else str(v)


def _rets_dict(row):
    d = {}
    for _label, key, _days in UI_PERIODS:
        col = f"ret_{key}"
        v = row.get(col)
        d[key] = None if (v is None or pd.isna(v)) else round(float(v), 4)
    return d


def _pdata_dict(row):
    """기간별 {score, rank, mom} — JS 재랭킹용."""
    d = {}
    for _label, key, _days in UI_PERIODS:
        sc = row.get(f"pscore_{key}")
        rk = row.get(f"prank_{key}")
        mo = row.get(f"pmom_{key}")
        d[key] = {
            "sc": None if (sc is None or pd.isna(sc)) else round(float(sc), 2),
            "rk": None if (rk is None or pd.isna(rk)) else int(rk),
            "mo": None if (mo is None or pd.isna(mo)) else round(float(mo), 2),
        }
    return d


def _row_view(r, max_score):
    return {
        "rank": int(r["rank"]),
        "name": r["name"], "code": r["code"], "industry": r.get("industry") or "-",
        "score": _fmt(r["score"], 1),
        "barw": int(round((r["score"] / max_score) * 60)) if max_score else 0,
        "per": _fmt(r["per"]), "pbr": _fmt(r["pbr"]), "roe": _fmt(r["roe"]),
        "eps": _fmt(None if pd.isna(r["eps"]) else int(r["eps"])),
        "op_profit": _fmt(None if pd.isna(r["op_profit"]) else int(r["op_profit"])),
        "op_growth": _fmt(r["op_growth"], 1),
        "op_growth_raw": None if pd.isna(r["op_growth"]) else float(r["op_growth"]),
        "market_cap_rank": _fmt(None if pd.isna(r["market_cap_rank"]) else int(r["market_cap_rank"])),
        "momentum": _fmt(r.get("momentum"), 1),
        "momentum_raw": None if pd.isna(r.get("momentum")) else float(r.get("momentum")),
        "news_buzz": _fmt(None if pd.isna(r.get("news_buzz")) else int(r.get("news_buzz"))),
        "rets": _rets_dict(r),
        "pdata": _pdata_dict(r),
    }


def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _sig_class(score):
    if score >= 75:
        return "s1"
    if score >= 65:
        return "s2"
    if score >= 55:
        return "s3"
    return "s4"


_ETF_TAGS = [("반도체", "반도체"), ("2차전지", "2차전지"), ("전지", "2차전지"), ("AI", "AI"),
             ("전력", "전력"), ("바이오", "바이오"), ("헬스", "바이오"), ("로봇", "로봇"),
             ("자동차", "자동차"), ("조선", "조선"), ("방산", "방산"), ("우주", "우주항공"),
             ("금융", "금융"), ("은행", "금융"), ("인터넷", "인터넷"), ("게임", "게임"),
             ("IT", "IT"), ("네트워크", "인프라"), ("인프라", "인프라"), ("소부장", "소부장")]


def _etf_tag(name):
    for kw, tag in _ETF_TAGS:
        if kw in name:
            return tag
    return "테마"


def _amount_fmt(eok):
    if eok is None:
        return "-"
    if eok >= 10000:
        return f"{eok/10000:,.1f}조"
    return f"{eok:,.0f}억"


def _bubble_svg(df, ret_col):
    W, H, ML, MR, MT, MB = 1040, 440, 56, 24, 18, 42
    x0, x1, y0, y1 = ML, W - MR, MT, H - MB
    XMAX = 40.0
    pts = []
    for _, r in df.iterrows():
        per, ret, cap = r.get("per"), r.get(ret_col), r.get("market_cap_eok")
        if per is None or pd.isna(per) or per <= 0:
            continue
        if ret is None or pd.isna(ret):
            continue
        pts.append((float(per), float(ret),
                    float(cap) if (cap is not None and not pd.isna(cap)) else 0.0,
                    r["name"]))
    if not pts:
        return "<svg></svg>"
    yabs = float(max(6.0, min(18.0, np.percentile([abs(p[1]) for p in pts], 92))))
    maxcap = max(p[2] for p in pts) or 1.0

    def sx(per):
        return x0 + (min(per, XMAX) / XMAX) * (x1 - x0)

    def sy(ret):
        v = max(-yabs, min(yabs, ret))
        return y0 + (1 - (v + yabs) / (2 * yabs)) * (y1 - y0)

    def rad(cap):
        return 4 + 20 * math.sqrt(max(cap, 0) / maxcap)

    o = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">']
    for gx in range(0, 41, 10):
        X = sx(gx)
        o.append(f'<line x1="{X:.1f}" y1="{y0}" x2="{X:.1f}" y2="{y1}" stroke="#eef1f4"/>')
        o.append(f'<text x="{X:.1f}" y="{y1+16}" font-size="11" fill="#9aa2ad" text-anchor="middle">{gx}</text>')
    o.append(f'<text x="{x1}" y="{y1+31}" font-size="11" fill="#8a93a0" text-anchor="end">PER(배)</text>')
    for gy in [-yabs, -yabs/2, 0, yabs/2, yabs]:
        Y = sy(gy)
        col = "#d7dde4" if abs(gy) < 0.01 else "#f1f3f6"
        o.append(f'<line x1="{x0}" y1="{Y:.1f}" x2="{x1}" y2="{Y:.1f}" stroke="{col}"/>')
        o.append(f'<text x="{x0-8}" y="{Y+4:.1f}" font-size="11" fill="#9aa2ad" text-anchor="end">{gy:+.0f}%</text>')
    rx0, ry0, ry1 = sx(0), sy(yabs), sy(0)
    o.append(f'<rect x="{rx0:.1f}" y="{ry0:.1f}" width="{sx(12)-rx0:.1f}" height="{ry1-ry0:.1f}" '
             f'rx="8" fill="#e0a92e" fill-opacity="0.09" stroke="#e0a92e" stroke-opacity="0.55" stroke-dasharray="5 4"/>')
    o.append(f'<text x="{rx0+9:.1f}" y="{ry0+17:.1f}" font-size="11.5" fill="#b5851f" font-weight="700">★ 유망 구간 (저PER + 상승)</text>')
    pts_sorted = sorted(pts, key=lambda p: p[2], reverse=True)
    for per, ret, cap, name in pts_sorted:
        color = "#d9534f" if ret > 0 else "#3b7dd8"
        if per <= 12 and ret > 0:
            color = "#e0a92e"
        o.append(f'<circle class="bub" data-nm="{_esc(name)}" data-per="{per:.1f}" '
                 f'data-ret="{ret:+.2f}" cx="{sx(per):.1f}" cy="{sy(ret):.1f}" r="{rad(cap):.1f}" '
                 f'fill="{color}" fill-opacity="0.60" stroke="#fff" stroke-width="1"/>')
    # 시가총액 상위 종목은 이름을 직접 표기(나머지는 마우스 오버 시 표시)
    for per, ret, cap, name in pts_sorted[:16]:
        o.append(f'<text x="{sx(per):.1f}" y="{sy(ret)-rad(cap)-3:.1f}" font-size="10.5" '
                 f'fill="#4a5360" text-anchor="middle" style="pointer-events:none">{_esc(name)}</text>')
    o.append('</svg>')
    return "".join(o)


def _prepare_summary(df, market, period_key):
    ret_col = f"ret_{period_key}"
    plabel = _plabel(period_key)
    idx = market.get("index") or {}
    index = {
        "value": _fmt(idx.get("value"), 2), "change": _fmt(idx.get("change"), 2),
        "rate": _fmt(idx.get("rate"), 2), "up": bool(idx.get("up")),
    }
    rr = df[ret_col]
    up_cnt, total = int((rr > 0).sum()), len(df)
    per_v = df["per"][df["per"] > 0]
    pbr_v = df["pbr"][df["pbr"] > 0]

    def _trimmed_mean(s):
        """상·하위 5% 절사평균 (이상치로 인한 왜곡 방지)."""
        s = s.dropna()
        if len(s) < 5:
            return s.mean()
        lo, hi = s.quantile(0.05), s.quantile(0.95)
        return s[(s >= lo) & (s <= hi)].mean()

    # 선택 기간의 스코어로 재정렬해 TOP10 산출 (기간마다 종목·순위가 달라짐)
    pscore_col = f"pscore_{period_key}"
    dfp = df.sort_values(pscore_col, ascending=False) if pscore_col in df.columns else df
    top10 = []
    for i, (_, r) in enumerate(dfp.head(10).iterrows(), start=1):
        rv = r.get(ret_col)
        sc = r.get(pscore_col)
        sc = float(sc) if (sc is not None and not pd.isna(sc)) else float(r["score"])
        top10.append({
            "rank": i, "code": r["code"], "name": r["name"],
            "industry": r.get("industry") or "-",
            "ret": "-" if pd.isna(rv) else ("+" if rv > 0 else "") + f"{rv:,.1f}%",
            "ret_raw": None if pd.isna(rv) else float(rv),
            "per": _fmt(r["per"]), "pbr": _fmt(r["pbr"]),
            "sig": str(int(round(sc))), "sig_class": _sig_class(sc),
        })

    grp = df.groupby("industry").agg(avg=(ret_col, "mean"), n=(ret_col, "size"))
    grp2 = grp[grp["n"] >= 2]
    if len(grp2) >= 8:
        grp = grp2
    grp = grp.copy()
    grp["strength"] = (grp["avg"].rank(pct=True) * 100).round(0)
    grp = grp.sort_values("avg", ascending=False).head(11)
    sectors = []
    for name, row in grp.iterrows():
        av = float(row["avg"])
        sectors.append({
            "name": name if (name and not (isinstance(name, float) and pd.isna(name))) else "기타",
            "avg": ("+" if av > 0 else "") + f"{av:,.1f}%", "pos": av >= 0,
            "strength": int(row["strength"]), "width": max(6, int(row["strength"])),
        })

    return {
        "index": index, "up_cnt": up_cnt, "total": total, "period_label": plabel,
        "avg_per": _fmt(_trimmed_mean(per_v), 1), "med_per": _fmt(per_v.median(), 1),
        "avg_pbr": _fmt(_trimmed_mean(pbr_v), 2), "med_pbr": _fmt(pbr_v.median(), 2),
        "top10": top10, "sectors": sectors,
        "svg": _bubble_svg(df, ret_col),
    }


def _prepare_etf(market):
    """ETF 페이지용 JSON 직렬화 가능한 목록. 종합점수(일간+3개월 백분위 블렌드) 포함."""
    rows = market.get("etf_list") or []
    if not rows:
        return []
    dfe = pd.DataFrame(rows)
    d_pct = dfe["change_rate"].rank(pct=True)
    r_pct = dfe["rate3m"].rank(pct=True)
    d_pct = d_pct.fillna(d_pct.mean() if d_pct.notna().any() else 0.5)
    r_pct = r_pct.fillna(r_pct.mean() if r_pct.notna().any() else 0.5)
    dfe["sc"] = ((d_pct * 0.5 + r_pct * 0.5) * 100).round(0)
    out = []
    for _, e in dfe.iterrows():
        rets = e.get("rets") if isinstance(e.get("rets"), dict) else {}
        out.append({
            "name": e["name"], "code": e["code"],
            "amt": None if pd.isna(e.get("amount_eok")) else float(e.get("amount_eok")),
            "lev": bool(e.get("leverage")),
            "sc": None if pd.isna(e.get("sc")) else int(e.get("sc")),
            "rets": {k: (None if rets.get(k) is None else float(rets.get(k)))
                     for k in ["d1", "w1", "w2", "w3", "m1", "m3"]},
        })
    return out


def build(df, generated, market=None):
    market = market or {}
    max_score = df["score"].max() or 1
    rows = [_row_view(r, max_score) for _, r in df.iterrows()]

    # 업종별 종목 등락률 데이터 (JS 렌더링용)
    sectors_data = []
    for name, g in df.groupby("industry", dropna=False):
        nm = name if (name and not (isinstance(name, float) and pd.isna(name))) else "기타"
        stocks = []
        for _, r in g.iterrows():
            per = r.get("per")
            stocks.append({
                "name": r["name"], "code": r["code"],
                "per": None if (per is None or pd.isna(per)) else round(float(per), 2),
                "rets": _rets_dict(r),
            })
        sectors_data.append({"name": nm, "count": len(stocks), "stocks": stocks})
    sectors_json = json.dumps(sectors_data, ensure_ascii=False)

    top = df.iloc[0]
    w = config.SCORE_WEIGHTS
    # 기간별 요약 (기간 탭 반응용) — 토탈 포함
    sum_list = [(key, _prepare_summary(df, market, key)) for _l, key, _d in UI_PERIODS]
    sum_map = dict(sum_list)
    sdef = sum_map[config.DEFAULT_PERIOD_KEY]
    up_by_period = {key: s["up_cnt"] for key, s in sum_list}
    etf_json = json.dumps(_prepare_etf(market), ensure_ascii=False)
    html = TEMPLATE.render(
        generated=generated, total=len(df), periods=UI_PERIODS,
        default_key=config.DEFAULT_PERIOD_KEY,
        rows=rows, sectors_json=sectors_json,
        sum_list=sum_list, sdef=sdef, up_by_period=json.dumps(up_by_period),
        etf_json=etf_json,
        top_name=top["name"], top_score=_fmt(top["score"], 1),
        w=w, w_total=sum(w.values()), trans_w=config.TRANSITION_WEIGHT,
    )
    tmp = config.DASHBOARD_HTML + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(html)
    os.replace(tmp, config.DASHBOARD_HTML)
    return config.DASHBOARD_HTML
