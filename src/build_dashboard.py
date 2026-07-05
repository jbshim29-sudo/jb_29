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
  <span class="cap">등락 기간</span>
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
      <div class="card"><div class="n">{{ top_name }}</div><div class="l">저평가 1위 (스코어 {{ top_score }})</div></div>
    </div>
    <div class="tablebox">
      <table id="rankTable">
        <thead><tr>
          <th data-t="num">순위</th><th class="l" data-t="str">종목명</th><th class="l" data-t="str">코드</th>
          <th class="l" data-t="str">업종</th><th data-t="num">종합<br>스코어</th>
          <th data-t="num">PER</th><th data-t="num">PBR</th><th data-t="num">ROE(%)</th>
          <th data-t="num">EPS</th><th data-t="num">영업이익<br>(억)</th><th data-t="num">영업이익<br>증가율(%)</th>
          <th data-t="num">시총<br>순위</th><th data-t="num">등락(%)</th><th class="l" data-t="str">추세</th>
        </tr></thead>
        <tbody>
        {% for r in rows %}
          <tr class="dyn-row"{% for label,key,days in periods %} data-{{key}}="{{ r.rets[key] if r.rets[key] is not none else '' }}"{% endfor %}>
            <td>{{ r.rank }}</td>
            <td class="l">{{ r.name }}</td>
            <td class="l"><a class="code" href="https://finance.naver.com/item/main.naver?code={{ r.code }}" target="_blank">{{ r.code }}</a></td>
            <td class="l">{{ r.industry }}</td>
            <td class="score">{{ r.score }}<span class="bar" style="width:{{ r.barw }}px"></span></td>
            <td>{{ r.per }}</td><td>{{ r.pbr }}</td><td>{{ r.roe }}</td>
            <td>{{ r.eps }}</td><td>{{ r.op_profit }}</td>
            <td class="{{ 'pos' if r.op_growth_raw is not none and r.op_growth_raw>0 else ('neg' if r.op_growth_raw is not none and r.op_growth_raw<0 else '') }}">{{ r.op_growth }}</td>
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
      <p>“저평가이면서 우량한” 종목을 하나의 숫자로 줄 세우기 위해, 성격이 다른 4개 지표를
         <b>가치(저평가) · 수익성 · 성장성</b> 관점에서 골고루 반영했습니다.</p>

      <h2>1. 사용 지표와 방향</h2>
      <table class="wtable">
        <tr><th>지표</th><th>관점</th><th>좋은 방향</th><th>가중치</th></tr>
        <tr><td>PER (주가수익비율)</td><td>가치 / 저평가</td><td>낮을수록 ▲</td><td>{{ w.per }}</td></tr>
        <tr><td>PBR (주가순자산비율)</td><td>가치 / 저평가</td><td>낮을수록 ▲</td><td>{{ w.pbr }}</td></tr>
        <tr><td>ROE (자기자본이익률)</td><td>수익성 / 자본효율</td><td>높을수록 ▲</td><td>{{ w.roe }}</td></tr>
        <tr><td>영업이익 증가율(전년比)</td><td>성장성 / 실적개선</td><td>높을수록 ▲</td><td>{{ w.op_growth }}</td></tr>
      </table>
      <p>PER·PBR은 “싼가”를, ROE는 “돈을 잘 버는가”를, 영업이익 증가율은 “좋아지고 있는가”를 봅니다.
         저평가 함정(싸지만 부실한 기업)을 피하기 위해 수익성·성장성을 함께 넣었습니다.</p>

      <h2>2. 백분위(퍼센타일) 정규화</h2>
      <p>PER(배), ROE(%), 증가율(%)은 단위와 범위가 제각각이라 그대로 더할 수 없습니다.
         그래서 각 지표를 <b>KOSPI 200 유니버스 안에서의 순위 백분위(0~100점)</b>로 변환합니다.
         예를 들어 PER이 전체 종목 중 가장 낮으면(가장 싸면) PER 항목에서 100점에 가깝습니다.
         이렇게 하면 모든 지표가 “동일한 0~100 척도”가 되어 공정하게 합산됩니다.</p>

      <h2>3. 종합 점수 계산</h2>
      <div class="formula">
        종합 스코어 = ( PER점수×{{ w.per }} + PBR점수×{{ w.pbr }} + ROE점수×{{ w.roe }} + 영업이익증가율점수×{{ w.op_growth }} ) ÷ {{ w_total }}
      </div>
      <p>각 항목 점수는 0~100의 백분위이며, 가중 평균이므로 종합 스코어도 0~100입니다. 높을수록 투자 우선순위가 앞섭니다.</p>

      <h2>4. 예외 처리</h2>
      <ul>
        <li>PER·PBR이 <b>0 이하</b>(적자·자본잠식)이거나 값이 없으면 해당 지표는 <b>최하위(0점)</b>로 처리합니다. (음수 PER을 “싸다”고 오인하지 않도록)</li>
        <li>최신 <b>영업이익이 적자</b>인 종목은 증가율 지표를 0점 처리합니다.</li>
        <li>결측치는 해당 항목만 0점이 되고 나머지 지표는 정상 반영됩니다.</li>
      </ul>

      <h2>5. 한계와 올바른 사용</h2>
      <ul>
        <li>이 점수는 <b>상대평가</b>입니다. 시장 전체가 고평가여도 “상대적으로 나은” 순위는 나옵니다.</li>
        <li>업종마다 적정 PER·ROE 수준이 다릅니다. 이를 보완하려면 <b>업종별 TOP3</b> 시트를 함께 보세요.</li>
        <li>재무는 과거 확정 실적 기준이며, 미래 실적·재료·수급은 반영되지 않습니다. <b>참고 지표</b>로만 활용하세요.</li>
      </ul>
      <p>가중치는 <code>config.py</code>의 <code>SCORE_WEIGHTS</code>에서 자유롭게 조정할 수 있으며, 변경 후 재실행하면 이 페이지의 숫자도 함께 갱신됩니다.</p>
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
  function applyPeriod(key){
    document.querySelectorAll('.periodTab').forEach(function(b){ b.classList.toggle('active', b.dataset.k===key); });
    var lab=document.getElementById('periodLabel');
    document.querySelectorAll('.periodTab').forEach(function(b){ if(b.dataset.k===key && lab) lab.textContent=b.textContent; });
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
    var up=0,down=0,flat=0;
    document.querySelectorAll('#rankTable tbody tr').forEach(function(tr){
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
        "rets": _rets_dict(r),
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
