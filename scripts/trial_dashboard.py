"""
【試行記録のダッシュボード】
docs/trials/trials.csv（run_with_log.py が貯める記録）から、ブラウザや Obsidian で開ける 1 枚の HTML を作る。
PC 側だけで動く。ハブには関係ない。外部のライブラリもネット接続もいらない。

答える問い: 「いま何点取れそうで、次にどのミッションに手を入れるか」

【使い方】
  uv run python scripts/trial_dashboard.py          # docs/trials/dashboard.html を作る
  uv run python scripts/trial_dashboard.py --open   # 作ってからブラウザで開く
  uv run python scripts/trial_dashboard.py --include-error   # 「動かなかった (error)」も試行に数える

run_with_log.py で成否を記録するたびに自動で作り直されるので、ふだんは開いたまま再読みこみするだけでよい。

【作り】（2026-09-19 見直し）
  ・数字はぜんぶこの Python で計算し、出てくる HTML にはスクリプトが 1 行も無い
    （Obsidian の HTML ビューアーの Safe モードでもそのまま読める。計算は関数ごとに分けてあり、単体で確かめられる）
  ・見た目は make-html スキルの weekly 型（html-effectiveness の ja/11-status-report.html）。
    CSS は scripts/dashboard_style.css に見本のまま写してあり、足した部品は下の EXTRA_CSS だけ
  ・点数の表は scripts/bioglow_missions.py（公式の採点表とルールブックから。合計 530 点）

【節の並び】（開発の進め方「① run ファイルで要素開発 → ② セレクターから通し」に合わせてある）
  数字 4 つ → ハイライト → 点数マップ（15 ミッション）→ ① 要素開発（run ファイルごと）→ ② 通し（セレクター）
  → 日ごとの試行 → メンバーごと → 最近の試行 → 次に手を入れるところ

成功率の分母は 成功 + 途中まで + 失敗。見こみ点は「成功＝満点・それ以外＝0 点」で数えた目安。
dashboard.html は生成物なので git には入れない（.gitignore）。プレゼン用の表と PNG は trial_report.py。
"""

import argparse
import csv
import os
import sys
import webbrowser
from collections import OrderedDict
from datetime import datetime, timedelta
from html import escape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bioglow_missions as bm  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRIALS_CSV = os.path.join(ROOT, "docs", "trials", "trials.csv")
OUT_HTML = os.path.join(ROOT, "docs", "trials", "dashboard.html")
STYLE_CSS = os.path.join(ROOT, "scripts", "dashboard_style.css")
SCORESHEET_URL = (
    "https://firstinspires.blob.core.windows.net/fll/challenge/2026-27/"
    "fll-challenge-bioglow-software-scoresheet.pdf"
)

COUNTED = ("success", "partial", "fail")  # 成功率の分母に入れる結果
RESULT_LABEL = {"success": "成功", "partial": "途中まで", "fail": "失敗", "error": "動かなかった"}
RESULT_DOT = {"success": "low", "partial": "med", "fail": "high", "error": "none"}

RECENT_N = 10  # 「直近」の本数
STABLE_RATE = 80  # 安定とみなす成功率 (%)
STABLE_MIN = 5  # 安定とみなすのに要る本数
ROUND_GAP_SEC = 90  # 通しの途中でこれ以上あいたら、次の回として数える (秒)
STRIP_N = 10  # 「直近の並び」に出す本数
CHART_DAYS = 14  # グラフに出す日数
RECENT_ROWS = 20  # 「最近の試行」に出す本数
ROUND_ROWS = 10  # 「通し」に出す回数

STAGES = OrderedDict(
    [
        ("none", ("未着手", "none")),
        ("dev", ("要素開発中", "med")),
        ("stable", ("単体で安定", "low")),
        ("sel", ("通しに入れた", "med")),
        ("selstable", ("通しで安定", "low")),
    ]
)

# 見本に無い部品のぶんだけ足す CSS（色は見本の変数だけを使う）
EXTRA_CSS = """
  /* ---------- 足した部品（trial_dashboard.py） ---------- */
  .table-wrap { overflow-x: auto; }
  table.shipped td.num, table.shipped th.num { text-align: right; font-variant-numeric: tabular-nums; }
  table.shipped thead th { white-space: nowrap; padding: 11px 10px; }
  table.shipped tbody td { white-space: nowrap; padding: 11px 10px; }
  table.shipped tbody td.note { white-space: normal; min-width: 12em; color: var(--gray-700); font-size: 13px; }
  table.shipped tbody tr.idle td { color: var(--gray-500); }
  .mission-en { display: block; color: var(--gray-500); font-size: 11px; }
  .risk-dot.none { background: var(--gray-300); }
  .stat-num small { font-size: 16px; color: var(--gray-500); }
  .stat-delta.down { color: var(--rust); }
  .meter { display: inline-block; width: 72px; height: 7px; border-radius: 4px; background: var(--gray-100);
           vertical-align: middle; margin-right: 8px; overflow: hidden; }
  .meter b { display: block; height: 100%; background: var(--olive); }
  .meter.over b { background: var(--rust); }
  .strip i { display: inline-block; width: 7px; height: 13px; border-radius: 2px; margin-right: 2px; vertical-align: middle; }
  .strip .low { background: var(--olive); } .strip .med { background: var(--clay); }
  .strip .high { background: var(--rust); } .strip .none { background: var(--gray-300); }
  .legend { display: flex; flex-wrap: wrap; gap: 4px 16px; margin: -8px 0 14px; }
  details { margin-top: 12px; } summary { cursor: pointer; color: var(--gray-500); font-size: 13px; }
  .lead { color: var(--gray-700); font-size: 14px; margin: -10px 0 16px; }
  .gap { height: 14px; }
"""


# ===== 読みこみ =====
def load_rows(csv_path, include_error=False):
    """trials.csv を読んで、数える行だけを時刻の順に返す。"""
    if not os.path.exists(csv_path):
        return []
    rows = []
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            result = r.get("result") or ""
            if not r.get("date") or not (
                result in COUNTED or (include_error and result == "error")
            ):
                continue
            rows.append({k: (v or "") for k, v in r.items() if k})
    rows.sort(key=stamp)
    return rows


def stamp(row):
    return row["date"] + " " + row.get("time", "")


def missions_of(row):
    """'M07+M09' → ['M07', 'M09']"""
    return [m for m in row.get("mission", "").split("+") if m]


def is_selector(row):
    return row.get("via", "").startswith("selector")


def seconds_of(row):
    try:
        return float(row.get("elapsed_sec") or 0)
    except ValueError:
        return 0.0


# ===== 集計 =====
def tally(rows):
    t = {"n": len(rows), "success": 0, "partial": 0, "fail": 0, "error": 0}
    for r in rows:
        t[r["result"]] = t.get(r["result"], 0) + 1
    t["rate"] = round(100 * t["success"] / t["n"]) if t["n"] else None
    return t


def recent(rows):
    return tally(rows[-RECENT_N:])


def mean_seconds(rows):
    ok = [seconds_of(r) for r in rows if r["result"] == "success" and seconds_of(r) > 0]
    return sum(ok) / len(ok) if ok else None


def members_of(rows):
    return "・".join(OrderedDict((r["member"], 1) for r in rows if r.get("member")))


def score_map(rows):
    """15 ミッションぶんの 段階・成功率・見こみ点。"""
    out = []
    for m in bm.MISSIONS:
        mine = [r for r in rows if m["id"] in missions_of(r)]
        t, rec = tally(mine), recent(mine)
        stable = rec["n"] >= STABLE_MIN and rec["rate"] >= STABLE_RATE
        in_selector = any(is_selector(r) for r in mine)
        if not mine:
            stage = "none"
        elif in_selector:
            stage = "selstable" if stable else "sel"
        else:
            stage = "stable" if stable else "dev"
        expected = m["max"] * rec["rate"] / 100 if rec["n"] else 0.0
        out.append({"m": m, "rows": mine, "t": t, "rec": rec, "stage": stage, "expected": expected})
    return out


def gain_of(x):
    """そのミッションが安定したら、見こみ点があと何点ふえるか。"""
    return x["m"]["max"] - x["expected"]


def script_table(rows):
    """① 要素開発: 単体で走らせた run ファイルごと（新しく走らせた順）。"""
    groups = OrderedDict()
    for r in rows:
        if not is_selector(r):
            groups.setdefault(r["script"], []).append(r)
    return sorted(groups.items(), key=lambda kv: stamp(kv[1][-1]), reverse=True)


def to_rounds(rows):
    """② 通し: セレクターの記録を「通し 1 回」にまとめる。

    同じログ（＝セレクターを 1 回起動したあいだ）の中で、同じプログラムがもう一度出たとき、
    または前のゴールから ROUND_GAP_SEC より長くあいたときに、次の回として数える。
    """
    max_of = {m["id"]: m["max"] for m in bm.MISSIONS}
    by_log = OrderedDict()
    for r in rows:
        if is_selector(r):
            by_log.setdefault(r.get("log_path") or r["date"], []).append(r)
    rounds = []
    for runs in by_log.values():
        current, last_end = None, None
        for r in runs:
            start = datetime.strptime(stamp(r), "%Y-%m-%d %H:%M:%S")
            end = start + timedelta(seconds=seconds_of(r))
            repeated = current is not None and any(
                x["script"] == r["script"] for x in current["rows"]
            )
            gap = last_end is not None and (start - last_end).total_seconds() > ROUND_GAP_SEC
            if current is None or repeated or gap:
                current = {"rows": [], "start": start}
                rounds.append(current)
            current["rows"].append(r)
            current["end"] = end
            last_end = end
    for x in rounds:
        x["t"] = tally(x["rows"])
        x["sec"] = round((x["end"] - x["start"]).total_seconds())
        done = {m for r in x["rows"] if r["result"] == "success" for m in missions_of(r)}
        x["points"] = sum(max_of.get(m, 0) for m in done)
    rounds.sort(key=lambda x: x["start"])
    return rounds


def daily(rows):
    days = OrderedDict()
    for r in rows:
        days.setdefault(r["date"], []).append(r)
    return [(d, tally(v)) for d, v in days.items()][-CHART_DAYS:]


def member_table(rows):
    groups = OrderedDict()
    for r in rows:
        groups.setdefault(r.get("member") or "（なし）", []).append(r)
    return sorted(groups.items(), key=lambda kv: len(kv[1]), reverse=True)


def window_rate(rows, today, first_day_ago, last_day_ago):
    """today から数えて first_day_ago〜last_day_ago 日前（両端ふくむ）の集計。"""
    lo = (today - timedelta(days=first_day_ago)).strftime("%Y-%m-%d")
    hi = (today - timedelta(days=last_day_ago)).strftime("%Y-%m-%d")
    return tally([r for r in rows if lo <= r["date"] <= hi])


# ===== 部品 =====
def pct(t):
    return "–" if t["rate"] is None else f"{t['rate']}%"


def dot(kind, label):
    return f'<span class="risk"><span class="risk-dot {kind}"></span>{escape(label)}</span>'


def meter(rate, over=False):
    if rate is None:
        return ""
    cls = "meter over" if over else "meter"
    return f'<span class="{cls}"><b style="width:{min(rate, 100):.0f}%"></b></span>'


def strip(rows):
    cells = "".join(
        f'<i class="{RESULT_DOT.get(r["result"], "none")}" '
        f'title="{escape(r["date"])} {escape(r.get("time", "")[:5])} {RESULT_LABEL.get(r["result"], "")}"></i>'
        for r in rows[-STRIP_N:]
    )
    return f'<span class="strip">{cells}</span>'


def table(heads, rows, num_cols=(), row_classes=None):
    th = "".join(
        f'<th class="{"num" if i in num_cols else ""}">{h}</th>' for i, h in enumerate(heads)
    )
    body = []
    for ri, r in enumerate(rows):
        cls = row_classes[ri] if row_classes else ""
        tds = "".join(
            f'<td class="{"num" if i in num_cols else "note" if heads[i] == "メモ" else ""}">{c}</td>'
            for i, c in enumerate(r)
        )
        body.append(f'<tr class="{cls}">{tds}</tr>')
    return (
        '<div class="table-wrap"><table class="shipped"><thead><tr>'
        + th
        + "</tr></thead><tbody>"
        + "".join(body)
        + "</tbody></table></div>"
    )


def bar_chart(points, label, unit="", y_max=None):
    """見本（ベロシティ）と同じ棒グラフ。points = [(x の字, 値, 補足)]。いちばん高い棒だけ色を変える。"""
    if not points:
        return ""
    base_y, top_y, left, right = 140, 20, 48, 620
    top = y_max or max(v for _, v, _ in points) or 1
    slot = (right - left) / len(points)
    bar_w = min(56, slot * 0.7)
    peak = max(range(len(points)), key=lambda i: points[i][1])
    text = '<text x="{x:.1f}" y="{y:.1f}" text-anchor="{a}" font-family="system-ui" font-size="11" fill="{f}"{w}>{s}</text>'
    out = [f'<svg viewBox="0 0 640 180" role="img" aria-label="{escape(label)}">']
    for frac in (0, 1 / 3, 2 / 3, 1):
        y = base_y - (base_y - top_y) * frac
        color, width = ("#D1CFC5", 1.5) if frac == 0 else ("#F0EEE6", 1)
        out.append(
            f'<line x1="{left}" y1="{y:.0f}" x2="{right}" y2="{y:.0f}" stroke="{color}" stroke-width="{width}"/>'
        )
        out.append(text.format(x=40, y=y + 4, a="end", f="#87867F", w="", s=f"{top * frac:.0f}"))
    for i, (x_label, value, note) in enumerate(points):
        cx = left + slot * (i + 0.5)
        h = (base_y - top_y) * value / top
        fill, ink, weight = (
            ("#D97757", "#3D3D3A", ' font-weight="600"')
            if i == peak
            else ("#E3DACC", "#87867F", "")
        )
        out.append(
            f'<rect x="{cx - bar_w / 2:.1f}" y="{base_y - h:.1f}" width="{bar_w:.1f}" height="{h:.1f}" rx="6" fill="{fill}">'
            f"<title>{escape(note)}</title></rect>"
        )
        out.append(
            text.format(x=cx, y=base_y - h - 6, a="middle", f=ink, w=weight, s=f"{value:.0f}{unit}")
        )
        out.append(text.format(x=cx, y=158, a="middle", f="#87867F", w="", s=escape(x_label)))
    out.append("</svg>")
    return "".join(out)


def chart_panel(chart, caption):
    return f'<div class="chart-panel">{chart}<div class="chart-caption">{caption}</div></div>'


def section(title, inner, lead=""):
    lead_html = f'<p class="lead">{lead}</p>' if lead else ""
    return f'<section><h2>{title}</h2><hr class="rule">{lead_html}{inner}</section>'


def mission_name(m):
    return f'<strong>{m["id"]}</strong> {escape(m["name"])} <span class="mission-en">{escape(m["en"])}</span>'


def short_date(d):
    return d[5:].replace("-", "/")


def round_labels(rounds):
    """通しの回の短い名前。同じ日に何回もあるので「09/19 ②」のように、その日の何回目かを添える。"""
    seen, labels = {}, []
    for x in rounds:
        day = x["start"].strftime("%m/%d")
        seen[day] = seen.get(day, 0) + 1
        labels.append(f"{day} {'①②③④⑤⑥⑦⑧⑨⑩'[min(seen[day], 10) - 1]}")
    return labels


# ===== 節 =====
def render_summary(rows, smap, today):
    expected = round(sum(x["expected"] for x in smap))
    started = sum(1 for x in smap if x["t"]["n"])
    stable = sum(1 for x in smap if x["stage"] in ("stable", "selstable"))
    in_selector = sum(1 for x in smap if x["stage"] in ("sel", "selstable"))
    this_week, last_week = window_rate(rows, today, 6, 0), window_rate(rows, today, 13, 7)
    today_t = tally([r for r in rows if r["date"] == today.strftime("%Y-%m-%d")])
    if this_week["rate"] is None or last_week["rate"] is None:
        delta, delta_cls = "前の 7 日の記録なし", "flat"
    else:
        diff = this_week["rate"] - last_week["rate"]
        delta = f"前の 7 日より {diff:+d} ポイント"
        delta_cls = "up" if diff > 0 else "down" if diff < 0 else "flat"
    today_note = f"成功 {today_t['success']} 本" if today_t["n"] else "まだ記録なし"
    cards = [
        (
            f"{expected}<small> / {bm.MISSION_MAX_TOTAL}</small>",
            "いまの見こみ点",
            f"満点は合計 {bm.GRAND_TOTAL} 点",
            "flat",
        ),
        (
            f"{started}<small> / {len(smap)}</small>",
            "着手したミッション",
            f"安定 {stable}・通しに入れた {in_selector}",
            "flat",
        ),
        (pct(this_week), "この 7 日の成功率", delta, delta_cls),
        (str(today_t["n"]), "今日の試行", today_note, "flat"),
    ]
    inner = "".join(
        f'<div class="stat-card{" warn" if cls == "down" else ""}"><div class="stat-num">{num}</div>'
        f'<div class="stat-label">{label}</div><div class="stat-delta {cls}">{sub}</div></div>'
        for num, label, sub, cls in cards
    )
    return f'<section><div class="summary-band">{inner}</div></section>'


def render_highlights(rows, smap, rounds):
    items = []
    if not rows:
        items.append(
            "<strong>まだ記録がない。</strong> 「📝 Robot N + Log」で run ファイルを走らせ、成否を 1 キーで入れると、ここに集計が出る。"
        )
    growing = [x for x in smap if x["stage"] in ("dev", "sel")]
    if growing:
        x = max(growing, key=gain_of)
        items.append(
            f"<strong>{x['m']['id']} {escape(x['m']['name'])} がいちばんのびしろが大きい。</strong> "
            f"直近の成功率は {pct(x['rec'])} で、安定すれば見こみ点が {round(gain_of(x))} 点ふえる。"
        )
    ready = [x for x in smap if x["stage"] == "stable"]
    if ready:
        names = "・".join(x["m"]["id"] for x in ready)
        items.append(
            f"<strong>{names} は単体で安定した。</strong> セレクターに入れて、通しで確かめる段階に来ている。"
        )
    if rounds:
        x = rounds[-1]
        fit = "をこえている" if x["sec"] > bm.MATCH_SECONDS else "に収まっている"
        items.append(
            f"<strong>最新の通しは見こみ {x['points']} 点。</strong> "
            f"かかった時間は {x['sec']} 秒で、試合の {bm.MATCH_SECONDS} 秒{fit}。"
        )
    if not items:
        return ""
    return section(
        "ハイライト", '<ul class="highlights">' + "".join(f"<li>{i}</li>" for i in items) + "</ul>"
    )


def render_score_map(smap):
    legend = (
        '<div class="legend">'
        + "".join(dot(kind, label) for label, kind in STAGES.values())
        + "</div>"
    )
    body, classes = [], []
    for x in smap:
        t, rec = x["t"], x["rec"]
        sec = mean_seconds(x["rows"])
        label, kind = STAGES[x["stage"]]
        body.append(
            [
                mission_name(x["m"]),
                x["m"]["max"],
                dot(kind, label),
                t["n"] or "",
                meter(rec["rate"]) + f"{pct(rec)}（{rec['success']}/{rec['n']}）"
                if rec["n"]
                else "",
                round(x["expected"]) if t["n"] else "",
                f"{sec:.1f}" if sec else "",
                escape(members_of(x["rows"])),
                strip(x["rows"]),
            ]
        )
        classes.append("" if t["n"] else "idle")
    heads = [
        "ミッション",
        "満点",
        "段階",
        "試行",
        f"直近 {RECENT_N} 本",
        "見こみ点",
        "平均秒",
        "担当",
        "並び",
    ]
    conditions = table(
        ["ミッション", "条件", "点"],
        [
            [mission_name(m) if i == 0 else "", escape(cond), pts]
            for m in bm.MISSIONS
            for i, (cond, pts) in enumerate(m["items"])
        ],
        num_cols=(2,),
    )
    lead = f"見こみ点は 満点 × 直近 {RECENT_N} 本の成功率。安定は 直近 {STABLE_MIN} 本以上で {STABLE_RATE}% 以上。"
    inner = legend + table(heads, body, num_cols=(1, 3, 5, 6), row_classes=classes)
    inner += f"<details><summary>採点の条件を見る</summary>{conditions}</details>"
    return section("点数マップ", inner, lead)


def render_scripts(rows):
    groups = script_table(rows)
    if not groups:
        return ""
    body = []
    for script, runs in groups:
        t, rec, sec = tally(runs), recent(runs), mean_seconds(runs)
        versions = len({r["code_hash"] for r in runs if r.get("code_hash")})
        body.append(
            [
                f'<span class="pr-link">{escape(script)}</span>',
                escape(runs[-1].get("mission", "")),
                f'<span class="author">{escape(runs[-1].get("member", ""))}</span>',
                t["n"],
                meter(rec["rate"]) + pct(rec),
                pct(t),
                f"{sec:.1f}" if sec else "",
                versions or "",
                short_date(runs[-1]["date"]),
                strip(runs),
            ]
        )
    heads = [
        "run ファイル",
        "ミッション",
        "担当",
        "試行",
        f"直近 {RECENT_N} 本",
        "通算",
        "平均秒",
        "版",
        "最後の日",
        "並び",
    ]
    legend = (
        '<div class="legend">'
        + "".join(dot(RESULT_DOT[k], RESULT_LABEL[k]) for k in COUNTED)
        + "</div>"
    )
    lead = "run ファイルを 1 本ずつ走らせた記録。並びは左が古く右が新しい。"
    return section("① 要素開発", legend + table(heads, body, num_cols=(3, 5, 6, 7)), lead)


def render_rounds(rounds):
    if not rounds:
        return ""
    shown = rounds[-ROUND_ROWS:]
    body = []
    for x in reversed(shown):
        over = x["sec"] > bm.MATCH_SECONDS
        order = "　".join(
            dot(RESULT_DOT.get(r["result"], "none"), r.get("mission") or r["script"])
            for r in x["rows"]
        )
        body.append(
            [
                x["start"].strftime("%m/%d %H:%M"),
                x["t"]["n"],
                x["t"]["success"],
                x["points"],
                meter(100 * x["sec"] / bm.MATCH_SECONDS, over)
                + f"{x['sec']} 秒"
                + ("・オーバー" if over else ""),
                order,
            ]
        )
    chart = bar_chart(
        [
            (
                label,
                x["points"],
                f"{x['start']:%m/%d %H:%M} 成功 {x['t']['success']} / {x['t']['n']} 本・{x['sec']} 秒",
            )
            for label, x in zip(round_labels(rounds)[-ROUND_ROWS:], shown, strict=True)
        ],
        "通しの 1 回ごとの見こみ点",
    )
    best = max(rounds, key=lambda x: x["points"])
    caption = f"通しの 1 回ごとの見こみ点。これまでの最高は {best['start'].strftime('%m/%d %H:%M')} の回である。"
    lead = f"セレクターから続けて走らせた記録。時間は最初のスタートから最後のゴールまでで、試合は {bm.MATCH_SECONDS} 秒。"
    heads = ["はじめた時刻", "本数", "成功", "見こみ点", "時間", "走らせた順"]
    inner = (
        chart_panel(chart, caption)
        + '<div class="gap"></div>'
        + table(heads, body, num_cols=(1, 2, 3))
    )
    return section("② 通し", inner, lead)


def render_daily(rows):
    days = daily(rows)
    if not days:
        return ""

    def note(d, t):
        return f"{d} 成功 {t['success']}・途中まで {t['partial']}・失敗 {t['fail']}"

    counts = bar_chart([(short_date(d), t["n"], note(d, t)) for d, t in days], "日ごとの試行数")
    rates = bar_chart(
        [(short_date(d), t["rate"], note(d, t)) for d, t in days],
        "日ごとの成功率",
        unit="%",
        y_max=100,
    )
    busiest = max(days, key=lambda x: x[1]["n"])
    best = max(days, key=lambda x: x[1]["rate"])
    panels = chart_panel(
        counts, f"日ごとの試行数。いちばん多く走らせたのは {short_date(busiest[0])} である。"
    )
    panels += '<div class="gap"></div>'
    panels += chart_panel(
        rates, f"日ごとの成功率。いちばん高かったのは {short_date(best[0])} である。"
    )
    return section("日ごとの試行", panels)


def render_members(rows):
    groups = member_table(rows)
    if not groups:
        return ""
    body = []
    for name, runs in groups:
        t, rec = tally(runs), recent(runs)
        missions = len({m for r in runs for m in missions_of(r)})
        body.append(
            [
                f'<span class="author">{escape(name)}</span>',
                t["n"],
                t["success"],
                pct(t),
                meter(rec["rate"]) + pct(rec),
                missions,
            ]
        )
    heads = ["メンバー", "試行", "成功", "通算の成功率", f"直近 {RECENT_N} 本", "ミッションの数"]
    return section("メンバーごと", table(heads, body, num_cols=(1, 2, 3, 5)))


def render_recent(rows):
    if not rows:
        return ""
    body = []
    for r in reversed(rows[-RECENT_ROWS:]):
        log = (
            f'<a class="pr-link" href="../../{escape(r["log_path"])}">ログ</a>'
            if r.get("log_path")
            else ""
        )
        body.append(
            [
                f"{short_date(r['date'])} {r.get('time', '')[:5]}",
                "② 通し" if is_selector(r) else "① 単体",
                f'<span class="pr-link">{escape(r["script"])}</span>',
                escape(r.get("mission", "")),
                f'<span class="author">{escape(r.get("member", ""))}</span>',
                dot(
                    RESULT_DOT.get(r["result"], "none"), RESULT_LABEL.get(r["result"], r["result"])
                ),
                r.get("elapsed_sec", ""),
                escape(r.get("note", "")),
                log,
            ]
        )
    heads = ["日時", "走らせ方", "スクリプト", "ミッション", "担当", "結果", "秒", "メモ", "ログ"]
    return section("最近の試行", table(heads, body, num_cols=(6,)))


def render_next(smap, rounds):
    """見本の「持ち越し」にあたる節。次に手を入れるところを、のびしろの大きい順に出す。"""
    items = []
    growing = sorted((x for x in smap if x["stage"] in ("dev", "sel")), key=gain_of, reverse=True)
    for x in growing[:2]:
        body = f"{x['m']['id']} {escape(x['m']['name'])} &mdash; 直近の成功率は {pct(x['rec'])}。安定すれば {round(gain_of(x))} 点ふえる。"
        items.append(("のびしろ", body, members_of(x["rows"])))
    for x in [x for x in smap if x["stage"] == "stable"][:2]:
        body = f"{x['m']['id']} {escape(x['m']['name'])} &mdash; 単体で安定した。セレクターの programs に足す。"
        items.append(("通しへ", body, members_of(x["rows"])))
    if rounds and rounds[-1]["sec"] > bm.MATCH_SECONDS:
        items.append(
            (
                "時間",
                f"最新の通しは {rounds[-1]['sec']} 秒かかった。走らせる順とホームでのつけかえを見直す。",
                "",
            )
        )
    idle = sorted(
        (x for x in smap if x["stage"] == "none"), key=lambda x: x["m"]["max"], reverse=True
    )
    for x in idle[:2]:
        items.append(
            (
                "未着手",
                f"{x['m']['id']} {escape(x['m']['name'])} &mdash; 満点 {x['m']['max']} 点。まだ記録がない。",
                "",
            )
        )
    if not items:
        return ""
    inner = "".join(
        f'<div class="carry-item"><span class="carry-tag">{tag}</span><div class="carry-body">{body}'
        + (f' <span class="who">&middot; {escape(who)}</span>' if who else "")
        + "</div></div>"
        for tag, body, who in items
    )
    return section("次に手を入れるところ", f'<div class="carryover">{inner}</div>')


# ===== 組み立て =====
def build(csv_path=TRIALS_CSV, out_path=OUT_HTML, include_error=False, now=None):
    """trials.csv を読んで dashboard.html を書き出し、数えた行数を返す。"""
    now = now or datetime.now()
    rows = load_rows(csv_path, include_error)
    smap, rounds = score_map(rows), to_rounds(rows)
    period = (
        f"{rows[0]['date']} 〜 {rows[-1]['date']}・{len(rows)} 本"
        if rows
        else "記録はまだありません"
    )
    commit = next((r["commit"] for r in reversed(rows) if r.get("commit")), "")
    repo = os.path.basename(ROOT) + (f" @ {commit}" if commit else "")
    sources = " &middot; ".join(
        [
            escape(os.path.abspath(csv_path)),
            escape(os.path.join(ROOT, "scripts", "bioglow_missions.py")),
            SCORESHEET_URL,
        ]
    )
    body = "".join(
        [
            '<header><div class="header-top"><h1>ロボットゲームの試行記録</h1><span class="auto-pill">自動生成</span></div>'
            f'<div class="date-range">{escape(period)} &nbsp;&middot;&nbsp; <span class="repo">{escape(repo)}</span></div></header>',
            render_summary(rows, smap, now),
            render_highlights(rows, smap, rounds),
            render_score_map(smap),
            render_scripts(rows),
            render_rounds(rounds),
            render_daily(rows),
            render_members(rows),
            render_recent(rows),
            render_next(smap, rounds),
            f"<footer>出典: {sources} &nbsp;&mdash;&nbsp; {now.strftime('%Y年%m月%d日 %H:%M')} 生成"
            f"{'（「動かなかった」も数えた）' if include_error else ''}</footer>",
        ]
    )
    with open(STYLE_CSS, encoding="utf-8") as f:
        css = f.read()
    html = (
        '<!DOCTYPE html>\n<html lang="ja">\n<head>\n<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>ロボットゲームの試行記録</title>\n"
        "<!-- make-html weekly 型（見本 ja/11-status-report.html）。scripts/trial_dashboard.py が trials.csv から生成 -->\n"
        f'<style>\n{css}{EXTRA_CSS}</style>\n</head>\n<body>\n  <div class="page">\n{body}\n  </div>\n</body>\n</html>\n'
    )
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    return len(rows)


def main():
    ap = argparse.ArgumentParser(
        description="試行記録のダッシュボード (docs/trials/dashboard.html) を作る"
    )
    ap.add_argument(
        "--csv", default=TRIALS_CSV, help="読みこむ CSV（省略時は docs/trials/trials.csv）"
    )
    ap.add_argument("--out", default=OUT_HTML, help="書き出す HTML")
    ap.add_argument(
        "--include-error", action="store_true", help="「動かなかった (error)」も試行に数える"
    )
    ap.add_argument("--open", action="store_true", help="作ったあとブラウザで開く")
    args = ap.parse_args()
    n = build(args.csv, args.out, args.include_error)
    print(f"📊 ダッシュボードを作りました: {args.out}（{n} 行）")
    if n == 0:
        print("   記録がまだありません。「📝 Robot N + Log」で走らせて成否を入れると行が増えます。")
    if args.open:
        webbrowser.open("file://" + os.path.abspath(args.out).replace(os.sep, "/"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
