"""
【試行記録のダッシュボード】
docs/trials/trials.csv（run_with_log.py が貯める記録）から、ブラウザで開ける 1 枚の HTML を作る。
PC 側だけで動く。ハブには関係ない。外部のライブラリもネット接続もいらない。

【使い方】
  uv run python scripts/trial_dashboard.py          # docs/trials/dashboard.html を作る
  uv run python scripts/trial_dashboard.py --open   # 作ってからブラウザで開く

run_with_log.py で成否を記録するたびに自動で作り直されるので、ふだんは
docs/trials/dashboard.html をブラウザで開いて、再読みこみ（F5）するだけでよい。

【見られるもの】
  ・全体の試行数・成功率・今日の試行数
  ・ミッションごとの 成功 / 途中まで / 失敗 の本数と成功率
  ・日ごとの成功率と試行数
  ・メンバーごとの試行数と成功率
  ・最近の試行の一覧（メモ・ログの場所つき）
  期間・ミッション・メンバー・ハブでしぼりこめる。

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
  --series: #2a78d6; --good: #0ca30c; --warning: #fab219; --critical: #d03b3b; --neutral: #c3c2b7;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    color-scheme: dark;
    --page: #0d0d0d; --surface: #1a1a19; --ink: #ffffff; --ink2: #c3c2b7; --muted: #898781;
    --grid: #2c2c2a; --axis: #383835; --border: rgba(255,255,255,0.10);
    --series: #3987e5; --neutral: #52514e;
  }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--page); color: var(--ink);
  font-family: system-ui, -apple-system, "Segoe UI", "Yu Gothic UI", "Hiragino Sans", sans-serif; font-size: 14px; line-height: 1.6; }
main { max-width: 1080px; margin: 0 auto; padding: 24px 16px 48px; }
h1 { font-size: 22px; margin: 0 0 2px; }
h2 { font-size: 15px; margin: 0 0 2px; }
.sub { color: var(--ink2); font-size: 12.5px; margin: 0 0 12px; }
.filters { display: flex; flex-wrap: wrap; gap: 8px 14px; align-items: center; margin: 16px 0;
  padding: 10px 12px; background: var(--surface); border: 1px solid var(--border); border-radius: 10px; }
.filters label { color: var(--ink2); font-size: 12.5px; display: flex; gap: 6px; align-items: center; }
select { font: inherit; color: var(--ink); background: var(--surface); border: 1px solid var(--axis); border-radius: 6px; padding: 3px 6px; }
.kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin-bottom: 12px; }
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 14px 16px; margin-bottom: 12px; }
.kpi .label { color: var(--ink2); font-size: 12.5px; }
.kpi .value { font-size: 30px; font-weight: 600; line-height: 1.25; }
.kpi.hero .value { font-size: 48px; }
.kpi .note { color: var(--muted); font-size: 12px; }
.grid2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 12px; }
.legend { display: flex; flex-wrap: wrap; gap: 4px 14px; color: var(--ink2); font-size: 12.5px; margin: 6px 0 8px; }
.legend i { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 5px; vertical-align: -1px; }
svg { display: block; width: 100%; height: auto; overflow: visible; }
svg text { fill: var(--ink2); font-size: 11.5px; }
svg text.val { fill: var(--ink); }
svg .hit { fill: transparent; cursor: default; }
.scroll { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-size: 13px; }
th, td { text-align: left; padding: 5px 8px; border-bottom: 1px solid var(--grid); white-space: nowrap; }
th { color: var(--ink2); font-weight: 600; }
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
td.wrap { white-space: normal; min-width: 12em; }
.res { display: inline-flex; align-items: center; gap: 5px; }
.res i { width: 9px; height: 9px; border-radius: 50%; display: inline-block; }
.empty { color: var(--muted); padding: 18px 0; }
#tip { position: fixed; pointer-events: none; background: var(--ink); color: var(--page); padding: 6px 9px; border-radius: 6px;
  font-size: 12px; line-height: 1.5; opacity: 0; transition: opacity .08s; z-index: 10; max-width: 260px; }
details summary { cursor: pointer; color: var(--ink2); font-size: 12.5px; margin-top: 8px; }
</style>
</head>
<body>
<main>
  <h1>試行記録ダッシュボード</h1>
  <p class="sub">走らせるたびに記録した 成功・失敗 のまとめ。作成: <span id="gen"></span> ／ もとのデータ: docs/trials/trials.csv</p>

  <div class="filters">
    <label>期間 <select id="f-period">
      <option value="all">ぜんぶ</option><option value="today">今日</option>
      <option value="7">この 7 日</option><option value="30">この 30 日</option></select></label>
    <label>ミッション <select id="f-mission"></select></label>
    <label>メンバー <select id="f-member"></select></label>
    <label>ハブ <select id="f-hub"></select></label>
    <label><input type="checkbox" id="f-error"> 「動かなかった」も数える</label>
  </div>

  <div class="kpis" id="kpis"></div>

  <div class="card">
    <h2>ミッションごとの結果</h2>
    <p class="sub">バーの長さは試行の数。右の数字は 成功率（成功 ÷ 試行）。</p>
    <div class="legend" id="legend"></div>
    <div id="chart-mission"></div>
    <details><summary>表で見る</summary><div class="scroll" id="table-mission"></div></details>
  </div>

  <div class="grid2">
    <div class="card"><h2>日ごとの成功率</h2><p class="sub">その日の 成功 ÷ 試行（%）。</p><div id="chart-rate"></div></div>
    <div class="card"><h2>日ごとの試行数</h2><p class="sub">その日に記録した本数。</p><div id="chart-count"></div></div>
  </div>

  <div class="card"><h2>メンバーごと</h2><p class="sub">たくさん試した人ほど、ロボットのくせが分かる。</p><div class="scroll" id="table-member"></div></div>
  <div class="card"><h2>最近の試行（新しい順・30 本まで）</h2><div class="scroll" id="table-recent"></div></div>
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
  $(id).innerHTML = `<option value="">${allLabel}</option>` +
    values.map(v => `<option value="${esc(v)}">${esc(v)}</option>`).join("");
}
function uniq(key) {
  return [...new Set(DATA.rows.map(r => r[key]).filter(Boolean))].sort();
}
function daysAgo(n) {
  const d = new Date(DATA.today + "T00:00:00"); d.setDate(d.getDate() - (n - 1));
  return d.toISOString().slice(0, 10);
}
function filtered() {
  const p = $("f-period").value, m = $("f-mission").value, mem = $("f-member").value, hub = $("f-hub").value;
  const counted = $("f-error").checked ? ["success", "partial", "fail", "error"] : ["success", "partial", "fail"];
  const from = p === "all" ? "" : p === "today" ? DATA.today : daysAgo(+p);
  return DATA.rows.filter(r => counted.includes(r.result) && (!from || r.date >= from) &&
    (!m || (r.mission || "（なし）") === m) && (!mem || r.member === mem) && (!hub || r.hub === hub));
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

function renderKpis(rows) {
  const all = tally(rows), today = tally(rows.filter(r => r.date === DATA.today));
  const missions = new Set(rows.map(r => r.mission).filter(Boolean)).size;
  const tiles = [
    ["成功率", pct(all), `成功 ${all.success} ／ 試行 ${all.n}`, true],
    ["試行の数", all.n.toLocaleString(), `途中まで ${all.partial}・失敗 ${all.fail}`],
    ["今日の試行", today.n, today.n ? `成功率 ${pct(today)}` : "まだ記録なし"],
    ["ミッションの数", missions, "記録のあるミッション"],
  ];
  $("kpis").innerHTML = tiles.map(([l, v, n, hero]) =>
    `<div class="card kpi${hero ? " hero" : ""}" style="margin:0"><div class="label">${l}</div><div class="value">${v}</div><div class="note">${n}</div></div>`).join("");
}

function renderMission(rows) {
  const box = $("chart-mission");
  const groups = [...groupBy(rows, r => r.mission || "（なし）")].map(([k, v]) => [k, tally(v)])
    .sort((a, b) => a[0].localeCompare(b[0], "ja", { numeric: true }));
  const shown = RESULTS.filter(r => r.key !== "error" || $("f-error").checked);
  $("legend").innerHTML = shown.map(r => `<span><i style="background:${r.color}"></i>${r.label}</span>`).join("");
  if (!groups.length) { box.innerHTML = '<p class="empty">この条件の記録はまだありません。</p>'; $("table-mission").innerHTML = ""; return; }
  const W = 1000, left = 110, right = 130, rowH = 30, barH = 16, top = 6;
  const plotW = W - left - right, maxN = Math.max(...groups.map(g => g[1].n));
  const H = top + groups.length * rowH + 22;
  box.innerHTML = "";
  const svg = svgEl("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": "ミッションごとの結果" }, box);
  const ticks = niceTicks(maxN);
  ticks.forEach(t => {
    const x = left + plotW * t / ticks[ticks.length - 1];
    svgEl("line", { x1: x, x2: x, y1: top, y2: H - 20, stroke: "var(--grid)", "stroke-width": 1 }, svg);
    svgEl("text", { x, y: H - 5, "text-anchor": "middle" }, svg, t);
  });
  const scale = plotW / ticks[ticks.length - 1];
  groups.forEach(([name, t], i) => {
    const y = top + i * rowH + (rowH - barH) / 2;
    svgEl("text", { x: left - 10, y: y + barH - 4, "text-anchor": "end", class: "val" }, svg, name);
    let x = left;
    const segs = shown.filter(r => t[r.key] > 0);
    segs.forEach((r, j) => {
      const w = t[r.key] * scale, last = j === segs.length - 1, gap = last ? 0 : 2;
      const rect = svgEl("path", { d: barPath(x, y, Math.max(w - gap, 1), barH, last ? 4 : 0), fill: r.color }, svg);
      bindTip(rect, `<b>${esc(name)}</b><br>${r.label}: ${t[r.key]} 本（${Math.round(100 * t[r.key] / t.n)}%）`);
      x += w;
    });
    svgEl("text", { x: x + 8, y: y + barH - 4, class: "val" }, svg, `${pct(t)}（${t.success}/${t.n}）`);
  });
  svgEl("line", { x1: left, x2: left, y1: top, y2: H - 20, stroke: "var(--axis)", "stroke-width": 1 }, svg);
  $("table-mission").innerHTML = table(["ミッション", "試行", "成功", "途中まで", "失敗", "動かなかった", "成功率"],
    groups.map(([k, t]) => [esc(k), t.n, t.success, t.partial, t.fail, t.error, pct(t)]), [1, 2, 3, 4, 5, 6]);
}
function barPath(x, y, w, h, r) {
  r = Math.min(r, w / 2);
  return `M${x},${y}h${w - r}a${r},${r} 0 0 1 ${r},${r}v${h - 2 * r}a${r},${r} 0 0 1 ${-r},${r}h${-(w - r)}z`;
}
function niceTicks(max) {
  const step = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000].find(s => max / s <= 5) || 2000;
  const out = []; for (let v = 0; v < max + step; v += step) out.push(v);
  return out;
}

function renderDaily(rows) {
  const days = [...groupBy(rows, r => r.date)].map(([d, v]) => [d, tally(v)]).sort((a, b) => a[0] < b[0] ? -1 : 1);
  drawDaily($("chart-rate"), days, "rate");
  drawDaily($("chart-count"), days, "n");
}
function drawDaily(box, days, key) {
  if (!days.length) { box.innerHTML = '<p class="empty">記録はまだありません。</p>'; return; }
  const W = 520, H = 230, left = 38, right = 44, top = 14, bottom = 28;
  const plotW = W - left - right, plotH = H - top - bottom;
  const ticks = key === "rate" ? [0, 25, 50, 75, 100] : niceTicks(Math.max(...days.map(d => d[1].n)));
  const yMax = ticks[ticks.length - 1];
  const xOf = i => left + (days.length === 1 ? plotW / 2 : plotW * i / (days.length - 1) * 0.94 + plotW * 0.03);
  const yOf = v => top + plotH * (1 - v / yMax);
  box.innerHTML = "";
  const svg = svgEl("svg", { viewBox: `0 0 ${W} ${H}`, role: "img" }, box);
  ticks.forEach(t => {
    svgEl("line", { x1: left, x2: W - right, y1: yOf(t), y2: yOf(t), stroke: t ? "var(--grid)" : "var(--axis)", "stroke-width": 1 }, svg);
    svgEl("text", { x: left - 6, y: yOf(t) + 4, "text-anchor": "end" }, svg, key === "rate" ? t + "%" : t);
  });
  const every = Math.ceil(days.length / 6);
  days.forEach(([d], i) => {
    const last = days.length - 1;
    if ((i % every === 0 && last - i >= every / 2) || i === last)
      svgEl("text", { x: xOf(i), y: H - 8, "text-anchor": "middle" }, svg, d.slice(5).replace("-", "/"));
  });
  if (key === "rate") {
    const pts = days.map(([, t], i) => [xOf(i), yOf(t.rate)]);
    if (pts.length > 1)
      svgEl("path", { d: "M" + pts.map(p => p.join(",")).join("L"), fill: "none", stroke: "var(--series)",
        "stroke-width": 2, "stroke-linejoin": "round", "stroke-linecap": "round" }, svg);
    pts.forEach(p => svgEl("circle", { cx: p[0], cy: p[1], r: 4, fill: "var(--series)", stroke: "var(--surface)", "stroke-width": 2 }, svg));
    const lastP = pts[pts.length - 1];
    svgEl("text", { x: lastP[0] + 8, y: lastP[1] + 4, class: "val" }, svg, days[days.length - 1][1].rate + "%");
  } else {
    const bw = Math.min(24, plotW / days.length * 0.6);
    days.forEach(([, t], i) => {
      const h = plotH * t.n / yMax, x = xOf(i) - bw / 2, y = yOf(t.n);
      svgEl("path", { d: colPath(x, y, bw, h, 4), fill: "var(--series)" }, svg);
    });
    const peak = days.reduce((a, b) => b[1].n > a[1].n ? b : a), pi = days.indexOf(peak);
    svgEl("text", { x: xOf(pi), y: yOf(peak[1].n) - 6, "text-anchor": "middle", class: "val" }, svg, peak[1].n);
  }
  const slot = days.length === 1 ? plotW : plotW / (days.length - 1);
  days.forEach(([d, t], i) => {
    const hit = svgEl("rect", { x: xOf(i) - slot / 2, y: top, width: slot, height: plotH, class: "hit" }, svg);
    bindTip(hit, `<b>${d}</b><br>成功率 ${pct(t)}<br>成功 ${t.success}・途中まで ${t.partial}・失敗 ${t.fail}（試行 ${t.n}）`);
  });
}
function colPath(x, y, w, h, r) {
  r = Math.min(r, w / 2, h);
  return `M${x},${y + h}v${-(h - r)}a${r},${r} 0 0 1 ${r},${-r}h${w - 2 * r}a${r},${r} 0 0 1 ${r},${r}v${h - r}z`;
}

function table(heads, rows, numCols) {
  numCols = numCols || [];
  return "<table><thead><tr>" + heads.map((h, i) => `<th class="${numCols.includes(i) ? "num" : ""}">${h}</th>`).join("") +
    "</tr></thead><tbody>" + rows.map(r => "<tr>" + r.map((c, i) =>
      `<td class="${numCols.includes(i) ? "num" : ""}${heads[i] === "メモ" ? " wrap" : ""}">${c}</td>`).join("") + "</tr>").join("") + "</tbody></table>";
}
const resCell = k => `<span class="res"><i style="background:${(RES[k] || {}).color || "var(--neutral)"}"></i>${(RES[k] || { label: k }).label}</span>`;

function renderMembers(rows) {
  const g = [...groupBy(rows, r => r.member || "（なし）")].map(([k, v]) => [k, tally(v), new Set(v.map(r => r.mission).filter(Boolean)).size])
    .sort((a, b) => b[1].n - a[1].n);
  $("table-member").innerHTML = g.length ? table(["メンバー", "試行", "成功", "途中まで", "失敗", "成功率", "ミッションの数"],
    g.map(([k, t, m]) => [esc(k), t.n, t.success, t.partial, t.fail, pct(t), m]), [1, 2, 3, 4, 5, 6]) : '<p class="empty">記録はまだありません。</p>';
}
function renderRecent(rows) {
  const r = [...rows].sort((a, b) => (a.date + a.time < b.date + b.time ? 1 : -1)).slice(0, 30);
  $("table-recent").innerHTML = r.length ? table(["日時", "スクリプト", "ミッション", "メンバー", "ハブ", "結果", "秒", "メモ", "ログ"],
    r.map(x => [`${x.date} ${x.time.slice(0, 5)}`, esc(x.script) + (x.via ? `（${esc(x.via)}）` : ""), esc(x.mission), esc(x.member), esc(x.hub),
      resCell(x.result), x.elapsed_sec, esc(x.note), x.log_path ? `<a href="../../${esc(x.log_path)}">ログ</a>` : ""]), [6]) : '<p class="empty">記録はまだありません。</p>';
}

function render() {
  const rows = filtered();
  renderKpis(rows); renderMission(rows); renderDaily(rows); renderMembers(rows); renderRecent(rows);
}
$("gen").textContent = DATA.generated + "（ぜんぶで " + DATA.rows.length + " 行）";
fillSelect("f-mission", [...new Set(DATA.rows.map(r => r.mission || "（なし）"))].sort(), "ぜんぶ");
fillSelect("f-member", uniq("member"), "ぜんぶ");
fillSelect("f-hub", uniq("hub"), "ぜんぶ");
["f-period", "f-mission", "f-member", "f-hub", "f-error"].forEach(id => $(id).addEventListener("change", render));
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
