"""
【試行記録のダッシュボード】
docs/trials/trials.csv（run_with_log.py が貯める記録）から、ブラウザで開ける 1 枚の HTML を作る。
PC 側だけで動く。ハブには関係ない。外部のライブラリもネット接続もいらない。

【使い方】
  uv run python scripts/trial_dashboard.py          # docs/trials/dashboard.html を作る
  uv run python scripts/trial_dashboard.py --open   # 作ってからブラウザで開く

run_with_log.py で成否を記録するたびに自動で作り直されるので、ふだんは
docs/trials/dashboard.html をブラウザで開いて、再読みこみ（F5）するだけでよい。

【見られるもの】（開発の進め方「① run ファイルで要素開発 → ② セレクターから通し」に合わせてある）
  ・いまの見こみ点（満点 × 直近 10 本の成功率 の合計）と、ミッションの進み
  ・点数マップ: 15 ミッションの満点・段階（未着手／要素開発中／単体で安定／通しに入れた／通しで安定）・成功率・見こみ点
  ・① 要素開発: run ファイルごとの成功率・平均秒・コードの版の数・直近の成否の並び
  ・② 通し: セレクターで続けて走らせた 1 回ごとの見こみ点と時間（試合は 150 秒）
  ・日ごとの成功率と試行数／メンバーごと／最近の試行の一覧（メモ・ログの場所つき）
  期間・走らせ方（単体／通し）・ミッション・メンバー・ハブでしぼりこめる。
  点数の表は scripts/bioglow_missions.py（公式の採点表とルールブックから。合計 530 点）。

成功率の分母は 成功 + 途中まで + 失敗。「動かなかった (error)」は、チェックを入れたときだけ数える。
dashboard.html は生成物なので git には入れない（.gitignore）。表とグラフの PNG が要るときは trial_report.py。
"""

import argparse
import csv
import json
import os
import sys
import webbrowser
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bioglow_missions as bm  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRIALS_CSV = os.path.join(ROOT, "docs", "trials", "trials.csv")
OUT_HTML = os.path.join(ROOT, "docs", "trials", "dashboard.html")

FIELDS = (
    "trial_id",
    "date",
    "time",
    "script",
    "mission",
    "member",
    "hub",
    "result",
    "elapsed_sec",
    "commit",
    "note",
    "log_path",
    "code_hash",
    "via",
)


def load_rows(csv_path):
    if not os.path.exists(csv_path):
        return []
    rows = []
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            if r.get("date") and r.get("result"):
                rows.append({k: (r.get(k) or "") for k in FIELDS})
    return rows


def build(csv_path=TRIALS_CSV, out_path=OUT_HTML):
    """trials.csv を読んで dashboard.html を書き出し、書き出した行数を返す。"""
    rows = load_rows(csv_path)
    data = {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "today": datetime.now().strftime("%Y-%m-%d"),
        "rows": rows,
        "missions": [
            {"id": m["id"], "name": m["name"], "en": m["en"], "max": m["max"], "items": m["items"]}
            for m in bm.MISSIONS
        ],
        "missionMax": bm.MISSION_MAX_TOTAL,
        "inspection": bm.EQUIPMENT_INSPECTION,
        "tokensMax": bm.PRECISION_TOKENS[6],
        "grandTotal": bm.GRAND_TOTAL,
        "matchSec": bm.MATCH_SECONDS,
    }
    # </script> で HTML が切れないように "<" を逃がす
    payload = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(TEMPLATE.replace("/*__DATA__*/null", payload))
    return len(rows)


TEMPLATE = r"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>試行記録ダッシュボード</title>
<style>
:root {
  color-scheme: light;
  --page: #f9f9f7; --surface: #fcfcfb; --ink: #0b0b0b; --ink2: #52514e; --muted: #898781;
  --grid: #e1e0d9; --axis: #c3c2b7; --border: rgba(11,11,11,0.10);
  --series: #2a78d6; --track: #cde2fb; --good: #0ca30c; --warning: #fab219; --critical: #d03b3b; --neutral: #c3c2b7;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    color-scheme: dark;
    --page: #0d0d0d; --surface: #1a1a19; --ink: #ffffff; --ink2: #c3c2b7; --muted: #898781;
    --grid: #2c2c2a; --axis: #383835; --border: rgba(255,255,255,0.10);
    --series: #3987e5; --track: #104281; --neutral: #52514e;
  }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--page); color: var(--ink);
  font-family: system-ui, -apple-system, "Segoe UI", "Yu Gothic UI", "Hiragino Sans", sans-serif; font-size: 14px; line-height: 1.6; }
main { max-width: 1120px; margin: 0 auto; padding: 24px 16px 48px; }
h1 { font-size: 22px; margin: 0 0 2px; }
h2 { font-size: 16px; margin: 0 0 2px; }
h2 small { font-weight: 400; color: var(--muted); font-size: 12.5px; margin-left: 6px; }
.sub { color: var(--ink2); font-size: 12.5px; margin: 0 0 10px; }
.filters { display: flex; flex-wrap: wrap; gap: 8px 14px; align-items: center; margin: 16px 0;
  padding: 10px 12px; background: var(--surface); border: 1px solid var(--border); border-radius: 10px; }
.filters label { color: var(--ink2); font-size: 12.5px; display: flex; gap: 6px; align-items: center; }
select { font: inherit; color: var(--ink); background: var(--surface); border: 1px solid var(--axis); border-radius: 6px; padding: 3px 6px; }
.kpis { display: grid; grid-template-columns: 1.4fr repeat(3, 1fr); gap: 12px; margin-bottom: 12px; }
@media (max-width: 760px) { .kpis { grid-template-columns: 1fr 1fr; } }
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 14px 16px; margin-bottom: 12px; }
.kpi { margin: 0; }
.kpi .label { color: var(--ink2); font-size: 12.5px; }
.kpi .value { font-size: 30px; font-weight: 600; line-height: 1.25; }
.kpi .value small { font-size: 15px; font-weight: 400; color: var(--muted); }
.kpi.hero .value { font-size: 48px; }
.kpi .note { color: var(--muted); font-size: 12px; }
.grid2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 12px; }
.legend { display: flex; flex-wrap: wrap; gap: 4px 14px; color: var(--ink2); font-size: 12.5px; margin: 2px 0 8px; }
.legend i, .dot { display: inline-block; width: 9px; height: 9px; border-radius: 50%; margin-right: 5px; vertical-align: 0; }
svg { display: block; width: 100%; height: auto; overflow: visible; }
svg text { fill: var(--ink2); font-size: 11.5px; }
svg text.val { fill: var(--ink); }
svg .hit { fill: transparent; }
.scroll { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-size: 13px; }
th, td { text-align: left; padding: 5px 8px; border-bottom: 1px solid var(--grid); white-space: nowrap; vertical-align: middle; }
th { color: var(--ink2); font-weight: 600; }
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
td.wrap { white-space: normal; min-width: 12em; }
tr.idle td { color: var(--muted); }
.meter { display: inline-block; width: 90px; height: 8px; border-radius: 4px; background: var(--track); vertical-align: middle; margin-right: 8px; overflow: hidden; }
.meter b { display: block; height: 100%; background: var(--series); border-radius: 4px 0 0 4px; }
.meter.over b { background: var(--critical); }
.strip i { display: inline-block; width: 8px; height: 14px; border-radius: 2px; margin-right: 2px; vertical-align: middle; }
.empty { color: var(--muted); padding: 14px 0; }
#tip { position: fixed; pointer-events: none; background: var(--ink); color: var(--page); padding: 6px 9px; border-radius: 6px;
  font-size: 12px; line-height: 1.5; opacity: 0; transition: opacity .08s; z-index: 10; max-width: 300px; }
details summary { cursor: pointer; color: var(--ink2); font-size: 12.5px; margin-top: 8px; }
.how { color: var(--ink2); font-size: 12.5px; margin: 8px 0 0; }
</style>
</head>
<body>
<main>
  <h1>試行記録ダッシュボード <small style="font-size:13px;font-weight:400;color:var(--muted)">BIOGLOW 2026-27</small></h1>
  <p class="sub">走らせるたびに記録した 成功・失敗 のまとめ。作成: <span id="gen"></span> ／ もとのデータ: docs/trials/trials.csv</p>

  <div class="filters">
    <label>期間 <select id="f-period">
      <option value="all">ぜんぶ</option><option value="today">今日</option>
      <option value="7">この 7 日</option><option value="30">この 30 日</option></select></label>
    <label>走らせ方 <select id="f-via">
      <option value="">ぜんぶ</option><option value="single">① 単体（run ファイル）</option><option value="selector">② 通し（セレクター）</option></select></label>
    <label>ミッション <select id="f-mission"></select></label>
    <label>メンバー <select id="f-member"></select></label>
    <label>ハブ <select id="f-hub"></select></label>
    <label><input type="checkbox" id="f-error"> 「動かなかった」も数える</label>
  </div>

  <div class="kpis" id="kpis"></div>

  <div class="card">
    <h2>点数マップ <small>15 ミッションのどこまで来たか</small></h2>
    <p class="sub">見こみ点 ＝ 満点 × 直近 10 本の成功率。点の高いミッションで成功率を上げるほど、合計がのびる。</p>
    <div class="legend" id="legend-stage"></div>
    <div class="scroll" id="table-score"></div>
    <details><summary>採点の条件を見る（採点表の 1 行ずつ）</summary><div class="scroll" id="table-items"></div></details>
    <p class="how">段階の決め方: 記録なし＝未着手 ／ 単体の記録だけ＝要素開発中 ／ 直近 10 本（5 本以上）で 80% 以上＝単体で安定 ／ セレクターから走らせた記録あり＝通しに入れた（80% 以上なら 通しで安定）。
      見こみ点は、成功＝満点・それ以外＝0 点で数えた目安（ボーナスだけ取れた・一部だけ取れた、は数えていない）。</p>
  </div>

  <div class="card">
    <h2>① 要素開発 <small>run ファイルを 1 本ずつ走らせた記録</small></h2>
    <p class="sub">「直近の並び」は左が古く右が新しい。緑がつづいたら、セレクターに入れるころあい。</p>
    <div class="legend" id="legend-result"></div>
    <div class="scroll" id="table-scripts"></div>
  </div>

  <div class="card">
    <h2>② 通し <small>セレクターから続けて走らせた記録</small></h2>
    <p class="sub">通し 1 回 ＝ セレクターで続けて走らせたひとまとまり（同じプログラムをもう一度走らせたとき、または 90 秒あいたときに、次の回として数える）。
      時間は、最初のスタートから最後のゴールまで（ホームでのつけかえの時間をふくむ）。試合は 150 秒。</p>
    <div id="chart-rounds"></div>
    <div class="scroll" id="table-rounds"></div>
  </div>

  <div class="grid2">
    <div class="card"><h2>日ごとの成功率</h2><p class="sub">その日の 成功 ÷ 試行（%）。</p><div id="chart-rate"></div></div>
    <div class="card"><h2>日ごとの試行数</h2><p class="sub">その日に記録した本数。</p><div id="chart-count"></div></div>
  </div>

  <div class="card"><h2>メンバーごと</h2><p class="sub">たくさん試した人ほど、ロボットのくせが分かる。</p><div class="scroll" id="table-member"></div></div>
  <div class="card"><h2>最近の試行 <small>新しい順・30 本まで</small></h2><div class="scroll" id="table-recent"></div></div>
</main>
<div id="tip"></div>

<script>
const DATA = /*__DATA__*/null;
const RESULTS = [
  { key: "success", label: "成功", color: "var(--good)" },
  { key: "partial", label: "途中まで", color: "var(--warning)" },
  { key: "fail", label: "失敗", color: "var(--critical)" },
  { key: "error", label: "動かなかった", color: "var(--neutral)" },
];
const RES = Object.fromEntries(RESULTS.map(r => [r.key, r]));
const STAGES = [
  { key: "none", label: "未着手", color: "var(--neutral)" },
  { key: "dev", label: "要素開発中", color: "var(--warning)" },
  { key: "stable", label: "単体で安定", color: "var(--series)" },
  { key: "sel", label: "通しに入れた", color: "var(--series)", ring: true },
  { key: "selstable", label: "通しで安定", color: "var(--good)" },
];
const STAGE = Object.fromEntries(STAGES.map(s => [s.key, s]));
const RECENT_N = 10, STABLE_RATE = 80, STABLE_MIN = 5, ROUND_GAP_SEC = 90;
const $ = id => document.getElementById(id);
const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const NS = "http://www.w3.org/2000/svg";

function svgEl(tag, attrs, parent, text) {
  const e = document.createElementNS(NS, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  if (text != null) e.textContent = text;
  if (parent) parent.appendChild(e);
  return e;
}
const tip = $("tip");
function bindTip(el, html) {
  el.addEventListener("mousemove", ev => {
    tip.innerHTML = html; tip.style.opacity = 1;
    const x = Math.min(ev.clientX + 12, window.innerWidth - tip.offsetWidth - 8);
    tip.style.left = x + "px"; tip.style.top = (ev.clientY + 14) + "px";
  });
  el.addEventListener("mouseleave", () => { tip.style.opacity = 0; });
}
function fillSelect(id, values, allLabel) {
  $(id).innerHTML = `<option value="">${allLabel}</option>` + values.map(v => `<option value="${esc(v)}">${esc(v)}</option>`).join("");
}
const uniq = key => [...new Set(DATA.rows.map(r => r[key]).filter(Boolean))].sort();
const missionsOf = r => (r.mission || "").split("+").filter(Boolean);
const isSelector = r => (r.via || "").startsWith("selector");
const stamp = r => r.date + " " + r.time;
const byTime = (a, b) => (stamp(a) < stamp(b) ? -1 : 1);
function daysAgo(n) {
  const d = new Date(DATA.today + "T00:00:00"); d.setDate(d.getDate() - (n - 1));
  return d.toISOString().slice(0, 10);
}
function filtered() {
  const p = $("f-period").value, via = $("f-via").value, m = $("f-mission").value, mem = $("f-member").value, hub = $("f-hub").value;
  const counted = $("f-error").checked ? ["success", "partial", "fail", "error"] : ["success", "partial", "fail"];
  const from = p === "all" ? "" : p === "today" ? DATA.today : daysAgo(+p);
  return DATA.rows.filter(r => counted.includes(r.result) && (!from || r.date >= from) &&
    (!via || (via === "selector") === isSelector(r)) &&
    (!m || missionsOf(r).includes(m) || (m === "（なし）" && !r.mission)) && (!mem || r.member === mem) && (!hub || r.hub === hub)).sort(byTime);
}
function tally(rows) {
  const t = { n: rows.length, success: 0, partial: 0, fail: 0, error: 0 };
  rows.forEach(r => { t[r.result]++; });
  t.rate = t.n ? Math.round(100 * t.success / t.n) : null;
  return t;
}
function groupBy(rows, fn) {
  const m = new Map();
  rows.forEach(r => { const k = fn(r); if (!m.has(k)) m.set(k, []); m.get(k).push(r); });
  return m;
}
const pct = t => t.rate == null ? "–" : t.rate + "%";
const recent = rows => tally(rows.slice(-RECENT_N));
function meanSec(rows) {
  const ok = rows.filter(r => r.result === "success" && +r.elapsed_sec > 0);
  return ok.length ? (ok.reduce((a, r) => a + +r.elapsed_sec, 0) / ok.length).toFixed(1) : "–";
}
const meter = (rate, cls) => rate == null ? "" : `<span class="meter ${cls || ""}"><b style="width:${Math.min(rate, 100)}%"></b></span>`;
const dotStyle = s => s.ring ? `background:transparent;box-shadow:inset 0 0 0 2px ${s.color}` : `background:${s.color}`;
const stageCell = k => `<span class="dot" style="${dotStyle(STAGE[k])}"></span>${STAGE[k].label}`;
const resCell = k => `<span class="dot" style="background:${(RES[k] || {}).color || "var(--neutral)"}"></span>${(RES[k] || { label: k }).label}`;
function strip(rows) {
  return '<span class="strip">' + rows.slice(-20).map(r =>
    `<i style="background:${(RES[r.result] || {}).color}" title="${r.date} ${r.time.slice(0, 5)} ${(RES[r.result] || {}).label}"></i>`).join("") + "</span>";
}
function table(heads, rows, numCols, rowClass) {
  numCols = numCols || [];
  return "<table><thead><tr>" + heads.map((h, i) => `<th class="${numCols.includes(i) ? "num" : ""}">${h}</th>`).join("") +
    "</tr></thead><tbody>" + rows.map((r, ri) => `<tr class="${rowClass ? rowClass(ri) : ""}">` + r.map((c, i) =>
      `<td class="${numCols.includes(i) ? "num" : ""}${heads[i] === "メモ" ? " wrap" : ""}">${c}</td>`).join("") + "</tr>").join("") + "</tbody></table>";
}

// ===== 点数マップ =====
function scoreMap(rows) {
  return DATA.missions.map(m => {
    const mine = rows.filter(r => missionsOf(r).includes(m.id));
    const t = tally(mine), rec = recent(mine), sel = mine.some(isSelector);
    const stable = rec.n >= STABLE_MIN && rec.rate >= STABLE_RATE;
    const stage = !t.n ? "none" : sel ? (stable ? "selstable" : "sel") : stable ? "stable" : "dev";
    return { m, mine, t, rec, stage, expected: rec.n ? m.max * rec.rate / 100 : 0 };
  });
}
function renderKpis(rows, map) {
  const all = tally(rows), today = tally(rows.filter(r => r.date === DATA.today));
  const expected = Math.round(map.reduce((a, x) => a + x.expected, 0));
  const started = map.filter(x => x.t.n).length, stable = map.filter(x => x.stage === "stable" || x.stage === "selstable").length;
  const inSel = map.filter(x => x.stage === "sel" || x.stage === "selstable").length;
  const tiles = [
    ["いまの見こみ点（ミッション）", `${expected} <small>/ ${DATA.missionMax} 点</small>`,
      `ほかに 装備の点検 ${DATA.inspection} 点・精密トークン 最大 ${DATA.tokensMax} 点（合計 ${DATA.grandTotal} 点）`, true],
    ["ミッションの進み", `${started} <small>/ ${map.length} に着手</small>`, `安定 ${stable}・通しに入れた ${inSel}`],
    ["成功率", pct(all), `成功 ${all.success} ／ 試行 ${all.n}（途中まで ${all.partial}・失敗 ${all.fail}）`],
    ["今日の試行", today.n, today.n ? `成功率 ${pct(today)}` : "まだ記録なし"],
  ];
  $("kpis").innerHTML = tiles.map(([l, v, n, hero]) =>
    `<div class="card kpi${hero ? " hero" : ""}"><div class="label">${l}</div><div class="value">${v}</div><div class="note">${n}</div></div>`).join("");
}
function renderScore(map) {
  $("legend-stage").innerHTML = STAGES.map(s => `<span><i style="${dotStyle(s)}"></i>${s.label}</span>`).join("");
  $("table-score").innerHTML = table(
    ["ミッション", "満点", "段階", "試行", "成功 / 途中 / 失敗", `直近 ${RECENT_N} 本の成功率`, "見こみ点", "平均秒", "担当", "直近の並び"],
    map.map(x => [`<b>${x.m.id}</b> ${esc(x.m.name)} <span style="color:var(--muted)">${esc(x.m.en)}</span>`, x.m.max, stageCell(x.stage), x.t.n || "",
      x.t.n ? `${x.t.success} / ${x.t.partial} / ${x.t.fail}` : "", x.rec.n ? meter(x.rec.rate) + pct(x.rec) + `（${x.rec.success}/${x.rec.n}）` : "",
      x.t.n ? Math.round(x.expected) : "", x.t.n ? meanSec(x.mine) : "", esc([...new Set(x.mine.map(r => r.member).filter(Boolean))].join("・")), strip(x.mine)]),
    [1, 3, 6, 7], i => map[i].t.n ? "" : "idle");
  $("table-items").innerHTML = table(["ミッション", "条件", "点"],
    DATA.missions.flatMap(m => m.items.map(([c, p], i) => [i ? "" : `<b>${m.id}</b> ${esc(m.name)}`, esc(c), p])), [2]);
}

// ===== ① 要素開発 =====
function renderScripts(rows) {
  $("legend-result").innerHTML = RESULTS.filter(r => r.key !== "error" || $("f-error").checked)
    .map(r => `<span><i style="background:${r.color}"></i>${r.label}</span>`).join("");
  const g = [...groupBy(rows.filter(r => !isSelector(r)), r => r.script)].map(([k, v]) => [k, v])
    .sort((a, b) => (stamp(b[1][b[1].length - 1]) < stamp(a[1][a[1].length - 1]) ? -1 : 1));
  $("table-scripts").innerHTML = g.length ? table(
    ["run ファイル", "ミッション", "担当", "試行", `直近 ${RECENT_N} 本`, "通算", "平均秒", "コードの版", "最後の日", "直近の並び"],
    g.map(([k, v]) => { const t = tally(v), rec = recent(v); return [esc(k), esc(v[v.length - 1].mission), esc(v[v.length - 1].member), t.n,
      meter(rec.rate) + pct(rec), pct(t), meanSec(v), new Set(v.map(r => r.code_hash).filter(Boolean)).size || "", v[v.length - 1].date.slice(5).replace("-", "/"), strip(v)]; }),
    [3, 5, 6, 7]) : '<p class="empty">単体で走らせた記録はまだありません。「📝 Robot N + Log」で run ファイルを走らせると、ここに出ます。</p>';
}

// ===== ② 通し =====
function toRounds(rows) {
  const rounds = [];
  [...groupBy(rows.filter(isSelector), r => r.log_path || r.date)].forEach(([, v]) => {
    let cur = null, lastEnd = 0;
    v.sort(byTime).forEach(r => {
      const start = new Date(r.date + "T" + r.time).getTime() / 1000, end = start + (+r.elapsed_sec || 0);
      if (!cur || cur.rows.some(x => x.script === r.script) || start - lastEnd > ROUND_GAP_SEC) { cur = { rows: [], start }; rounds.push(cur); }
      cur.rows.push(r); cur.end = end; lastEnd = end;
    });
  });
  const maxOf = Object.fromEntries(DATA.missions.map(m => [m.id, m.max]));
  rounds.forEach(x => {
    x.t = tally(x.rows); x.sec = Math.round(x.end - x.start);
    const okMissions = new Set(x.rows.filter(r => r.result === "success").flatMap(missionsOf));
    x.points = [...okMissions].reduce((a, id) => a + (maxOf[id] || 0), 0);
    x.label = x.rows[0].date.slice(5).replace("-", "/") + " " + x.rows[0].time.slice(0, 5);
  });
  return rounds.sort((a, b) => a.start - b.start);
}
function renderRounds(rows) {
  const rounds = toRounds(rows);
  if (!rounds.length) {
    $("chart-rounds").innerHTML = "";
    $("table-rounds").innerHTML = '<p class="empty">通しの記録はまだありません。selector.py を「📝 Robot N + Log」で走らせると、プログラムごとに成否を聞かれて、ここに出ます。</p>';
    return;
  }
  drawSeries($("chart-rounds"), rounds.map(x => ({ label: x.label, value: x.points,
    tip: `<b>${x.label}</b><br>見こみ点 ${x.points} 点<br>成功 ${x.t.success} / ${x.t.n} 本・${x.sec} 秒` })),
    { yMax: DATA.missionMax, unit: " 点", height: 200, width: 1000 });
  $("table-rounds").innerHTML = table(["はじめた時刻", "走らせた本数", "成功", "見こみ点", `時間（試合は ${DATA.matchSec} 秒）`, "走らせた順（結果）", "ハブ"],
    [...rounds].reverse().slice(0, 20).map(x => [x.label, x.t.n, x.t.success, x.points,
      meter(100 * x.sec / DATA.matchSec, x.sec > DATA.matchSec ? "over" : "") + x.sec + " 秒" + (x.sec > DATA.matchSec ? "（オーバー）" : ""),
      x.rows.map(r => `<span title="${esc(r.script)}">${resCell(r.result).replace(/<\/span>.*/, "</span>")}${esc(r.mission || r.script)}</span>`).join("　"), esc(x.rows[0].hub)]),
    [1, 2, 3]);
}

// ===== 日ごと =====
function niceTicks(max) {
  const step = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000].find(s => max / s <= 5) || 2000;
  const out = []; for (let v = 0; v < max + step; v += step) out.push(v);
  return out;
}
function drawSeries(box, pts, opt) {
  const W = opt.width || 520, H = opt.height || 230, left = 40, right = 56, top = 14, bottom = 28;
  const plotW = W - left - right, plotH = H - top - bottom;
  const ticks = opt.ticks || niceTicks(opt.yMax || Math.max(...pts.map(p => p.value), 1));
  const yMax = ticks[ticks.length - 1];
  const xOf = i => left + (pts.length === 1 ? plotW / 2 : plotW * (0.03 + 0.94 * i / (pts.length - 1)));
  const yOf = v => top + plotH * (1 - v / yMax);
  box.innerHTML = "";
  const svg = svgEl("svg", { viewBox: `0 0 ${W} ${H}`, role: "img" }, box);
  ticks.forEach(t => {
    svgEl("line", { x1: left, x2: W - right, y1: yOf(t), y2: yOf(t), stroke: t ? "var(--grid)" : "var(--axis)", "stroke-width": 1 }, svg);
    svgEl("text", { x: left - 6, y: yOf(t) + 4, "text-anchor": "end" }, svg, t + (opt.unit === "%" ? "%" : ""));
  });
  const every = Math.ceil(pts.length / (W > 600 ? 10 : 6)), last = pts.length - 1;
  pts.forEach((p, i) => {
    if ((i % every === 0 && last - i >= Math.max(every, 2)) || i === last) svgEl("text", { x: xOf(i), y: H - 8, "text-anchor": "middle" }, svg, p.label);
  });
  if (opt.bars) {
    const bw = Math.min(24, plotW / pts.length * 0.6);
    pts.forEach((p, i) => {
      const h = plotH * p.value / yMax, r = Math.min(4, bw / 2, h), x = xOf(i) - bw / 2, y = yOf(p.value);
      svgEl("path", { d: `M${x},${y + h}v${-(h - r)}a${r},${r} 0 0 1 ${r},${-r}h${bw - 2 * r}a${r},${r} 0 0 1 ${r},${r}v${h - r}z`, fill: "var(--series)" }, svg);
    });
    const pi = pts.reduce((a, p, i) => (p.value > pts[a].value ? i : a), 0);
    svgEl("text", { x: xOf(pi), y: yOf(pts[pi].value) - 6, "text-anchor": "middle", class: "val" }, svg, pts[pi].value);
  } else {
    const xy = pts.map((p, i) => [xOf(i), yOf(p.value)]);
    if (xy.length > 1) svgEl("path", { d: "M" + xy.map(p => p.join(",")).join("L"), fill: "none", stroke: "var(--series)",
      "stroke-width": 2, "stroke-linejoin": "round", "stroke-linecap": "round" }, svg);
    xy.forEach(p => svgEl("circle", { cx: p[0], cy: p[1], r: 4, fill: "var(--series)", stroke: "var(--surface)", "stroke-width": 2 }, svg));
    svgEl("text", { x: xy[last][0] + 8, y: xy[last][1] + 4, class: "val" }, svg, pts[last].value + (opt.unit || ""));
  }
  const slot = pts.length === 1 ? plotW : plotW * 0.94 / (pts.length - 1);
  pts.forEach((p, i) => bindTip(svgEl("rect", { x: xOf(i) - slot / 2, y: top, width: slot, height: plotH, class: "hit" }, svg), p.tip));
}
function renderDaily(rows) {
  const days = [...groupBy(rows, r => r.date)].map(([d, v]) => [d, tally(v)]).sort((a, b) => (a[0] < b[0] ? -1 : 1));
  if (!days.length) { ["chart-rate", "chart-count"].forEach(id => { $(id).innerHTML = '<p class="empty">記録はまだありません。</p>'; }); return; }
  const tipOf = (d, t) => `<b>${d}</b><br>成功率 ${pct(t)}<br>成功 ${t.success}・途中まで ${t.partial}・失敗 ${t.fail}（試行 ${t.n}）`;
  const lab = d => d.slice(5).replace("-", "/");
  drawSeries($("chart-rate"), days.map(([d, t]) => ({ label: lab(d), value: t.rate, tip: tipOf(d, t) })), { ticks: [0, 25, 50, 75, 100], unit: "%" });
  drawSeries($("chart-count"), days.map(([d, t]) => ({ label: lab(d), value: t.n, tip: tipOf(d, t) })), { bars: true });
}

function renderMembers(rows) {
  const g = [...groupBy(rows, r => r.member || "（なし）")].map(([k, v]) => [k, tally(v), recent(v), new Set(v.flatMap(missionsOf)).size])
    .sort((a, b) => b[1].n - a[1].n);
  $("table-member").innerHTML = g.length ? table(["メンバー", "試行", "成功", "途中まで", "失敗", "通算の成功率", `直近 ${RECENT_N} 本`, "ミッションの数"],
    g.map(([k, t, rec, m]) => [esc(k), t.n, t.success, t.partial, t.fail, pct(t), meter(rec.rate) + pct(rec), m]), [1, 2, 3, 4, 5, 7]) : '<p class="empty">記録はまだありません。</p>';
}
function renderRecent(rows) {
  const r = [...rows].reverse().slice(0, 30);
  $("table-recent").innerHTML = r.length ? table(["日時", "走らせ方", "スクリプト", "ミッション", "メンバー", "ハブ", "結果", "秒", "メモ", "ログ"],
    r.map(x => [`${x.date} ${x.time.slice(0, 5)}`, isSelector(x) ? "② 通し" : "① 単体", esc(x.script), esc(x.mission), esc(x.member), esc(x.hub),
      resCell(x.result), x.elapsed_sec, esc(x.note), x.log_path ? `<a href="../../${esc(x.log_path)}">ログ</a>` : ""]), [7]) : '<p class="empty">記録はまだありません。</p>';
}

function render() {
  const rows = filtered(), map = scoreMap(rows);
  renderKpis(rows, map); renderScore(map); renderScripts(rows); renderRounds(rows); renderDaily(rows); renderMembers(rows); renderRecent(rows);
}
$("gen").textContent = DATA.generated + "（ぜんぶで " + DATA.rows.length + " 行）";
fillSelect("f-mission", DATA.missions.map(m => m.id).concat(DATA.rows.some(r => !r.mission) ? ["（なし）"] : []), "ぜんぶ");
fillSelect("f-member", uniq("member"), "ぜんぶ");
fillSelect("f-hub", uniq("hub"), "ぜんぶ");
["f-period", "f-via", "f-mission", "f-member", "f-hub", "f-error"].forEach(id => $(id).addEventListener("change", render));
render();
</script>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser(
        description="試行記録のダッシュボード (docs/trials/dashboard.html) を作る"
    )
    ap.add_argument(
        "--csv", default=TRIALS_CSV, help="読みこむ CSV（省略時は docs/trials/trials.csv）"
    )
    ap.add_argument("--out", default=OUT_HTML, help="書き出す HTML")
    ap.add_argument("--open", action="store_true", help="作ったあとブラウザで開く")
    args = ap.parse_args()
    n = build(args.csv, args.out)
    print(f"📊 ダッシュボードを作りました: {args.out}（{n} 行）")
    if n == 0:
        print("   記録がまだありません。「📝 Robot N + Log」で走らせて成否を入れると行が増えます。")
    if args.open:
        webbrowser.open("file://" + os.path.abspath(args.out).replace(os.sep, "/"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
