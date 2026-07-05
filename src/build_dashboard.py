# -*- coding: utf-8 -*-
"""HTML 대시보드 생성: 전체 랭킹(기간탭) + 업종별 TOP3 + 스코어 설명."""
import os
import sys

import pandas as pd
from jinja2 import Template

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config

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
  .sectorCard table { font-size:12.5px; }
  .medal { font-weight:700; }
  .m1{color:#d4af37;} .m2{color:#9aa0a6;} .m3{color:#cd7f32;}
  /* 설명 페이지 */
  .doc { background:#fff; border-radius:10px; box-shadow:0 1px 3px rgba(0,0,0,.08); padding:26px 30px; max-width:900px; line-height:1.7; }
  .doc h2 { margin-top:26px; } .doc h2:first-child { margin-top:0; }
  .doc p, .doc li { font-size:14px; color:#2b3138; }
  .doc code { background:#eef1f5; padding:1px 6px; border-radius:4px; }
  .formula { background:#0f2540; color:#fff; padding:14px 18px; border-radius:8px; font-size:14px; overflow-x:auto; }
  .wtable { border-collapse:collapse; margin:10px 0; }
  .wtable th,.wtable td { border:1px solid #e2e6ec; padding:7px 12px; text-align:left; font-size:13px; }
  .wtable th { background:#eef1f5; }
</style>
</head>
<body>
<header>
  <h1>KOSPI 200 저평가 종목 스크리너</h1>
  <div class="sub">데이터 출처: 네이버 금융 · 생성 시각: {{ generated }} · 종목 수: {{ total }}개</div>
</header>

<div class="nav">
  <button class="navTab active" data-v="rank" onclick="showView('rank')">💎 저평가 전체 랭킹</button>
  <button class="navTab" data-v="sector" onclick="showView('sector')">🏭 업종별 TOP3</button>
  <button class="navTab" data-v="score" onclick="showView('score')">📐 스코어 산정 방식</button>
</div>

<div class="periodBar" id="periodBar">
  <span class="cap">등락 기간 (선택하면 해당 기간 기준으로 순위 재정렬)</span>
  {% for label, key, days in periods %}
  <button class="periodTab" data-k="{{ key }}" onclick="applyPeriod('{{ key }}')">{{ label }}</button>
  {% endfor %}
</div>

<div class="wrap">
  <!-- ============ 전체 랭킹 ============ -->
  <div class="view" id="view-rank">
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

  <!-- ============ 업종별 TOP3 ============ -->
  <div class="view" id="view-sector" style="display:none">
    <h2>업종 테마별 저평가 상위 종목 (업종 내 종합 스코어 1~3위)</h2>
    <div class="sectorGrid">
      {% for s in sectors %}
      <div class="sectorCard">
        <h3>{{ s.name }} <span style="opacity:.7;font-weight:400">· {{ s.count }}종목</span></h3>
        <table>
          <thead><tr>
            <th class="l">순위</th><th class="l">종목명</th><th>스코어</th>
            <th>PER</th><th>PBR</th><th>ROE</th><th>등락(%)</th><th class="l">추세</th>
          </tr></thead>
          <tbody>
          {% for r in s.rows %}
            <tr class="dyn-row"{% for label,key,days in periods %} data-{{key}}="{{ r.rets[key] if r.rets[key] is not none else '' }}"{% endfor %}>
              <td class="l medal m{{ r.medal }}">{{ r.medal }}위</td>
              <td class="l"><a class="code" href="https://finance.naver.com/item/main.naver?code={{ r.code }}" target="_blank">{{ r.name }}</a></td>
              <td class="score">{{ r.score }}</td>
              <td>{{ r.per }}</td><td>{{ r.pbr }}</td><td>{{ r.roe }}</td>
              <td class="retCell">-</td><td class="l trendCell"></td>
            </tr>
          {% endfor %}
          </tbody>
        </table>
      </div>
      {% endfor %}
    </div>
    <div class="foot">각 업종에서 종합 스코어 상위 1~3위 종목입니다. 상단 기간 탭이 등락/추세에 함께 적용됩니다.</div>
  </div>

  <!-- ============ 스코어 산정 방식 ============ -->
  <div class="view" id="view-score" style="display:none">
    <div class="doc">
      <h2>종합 스코어는 어떻게 만들어졌나</h2>
      <p>초기 버전은 <b>저평가(가치) 지표만</b> 봤기 때문에, “싸지만 계속 빠지는” <b>가치 함정</b> 종목이
         1위가 되는 문제가 있었습니다. 이를 바로잡기 위해 <b>가치 · 성장 · 추세(모멘텀) · 관심도</b>를
         함께 보는 7개 팩터로 재설계했습니다. 싼 것만이 아니라 <b>싸면서 실적이 늘고, 주가가 돌기 시작하며,
         업종·시장의 관심을 받는</b> 종목이 상위에 오도록 했습니다.</p>

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
    document.getElementById('periodBar').style.display = (v==='score') ? 'none' : 'flex';
  }
  function numAttr(tr, attr){ var v=tr.getAttribute(attr); return (v===null||v==='')?null:parseFloat(v); }

  function applyPeriod(key){
    document.querySelectorAll('.periodTab').forEach(function(b){ b.classList.toggle('active', b.dataset.k===key); });
    var lab=document.getElementById('periodLabel');
    document.querySelectorAll('.periodTab').forEach(function(b){ if(b.dataset.k===key && lab) lab.textContent=b.textContent; });

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
  // 초기화
  applyPeriod('{{ default_key }}');
  showView('rank');
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
    for _label, key, _days in config.PERIODS:
        col = f"ret_{key}"
        v = row.get(col)
        d[key] = None if (v is None or pd.isna(v)) else round(float(v), 4)
    return d


def _pdata_dict(row):
    """기간별 {score, rank, mom} — JS 재랭킹용."""
    d = {}
    for _label, key, _days in config.PERIODS:
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


def build(df, generated):
    max_score = df["score"].max() or 1
    rows = [_row_view(r, max_score) for _, r in df.iterrows()]

    # 업종별 TOP3
    sectors = []
    for name, g in df.groupby("industry", dropna=False):
        if not name or (isinstance(name, float) and pd.isna(name)):
            name = "기타"
        g = g.sort_values("score", ascending=False)
        top = g.head(3)
        srows = []
        for i, (_, r) in enumerate(top.iterrows(), start=1):
            v = _row_view(r, max_score)
            v["medal"] = i
            srows.append(v)
        sectors.append({"name": name, "count": int(len(g)), "rows": srows,
                        "max_score": float(g["score"].max())})
    sectors.sort(key=lambda s: s["max_score"], reverse=True)

    top = df.iloc[0]
    w = config.SCORE_WEIGHTS
    html = TEMPLATE.render(
        generated=generated, total=len(df), periods=config.PERIODS,
        default_key=config.DEFAULT_PERIOD_KEY,
        rows=rows, sectors=sectors,
        top_name=top["name"], top_score=_fmt(top["score"], 1),
        w=w, w_total=sum(w.values()),
    )
    tmp = config.DASHBOARD_HTML + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(html)
    os.replace(tmp, config.DASHBOARD_HTML)
    return config.DASHBOARD_HTML
