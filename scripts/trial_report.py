"""
【試行記録の集計・グラフ作成】
docs/trials/trials.csv（run_with_log.py が貯める記録）を集計して、
プレゼンで使える表とグラフを作る。PC 側だけで動く。ハブには関係ない。

【使い方】
  python scripts/trial_report.py                # 全期間
  python scripts/trial_report.py --since 2026-09-01
  python scripts/trial_report.py --mission M01  # 1 ミッションだけ
  python scripts/trial_report.py --by day       # 週ごとではなく日ごとに集計
  python scripts/trial_report.py --diff         # コード変更の差分も report.md に添える
  python scripts/trial_report.py --include-error  # 「動かなかった (error)」も試行に数える

【出力】
  docs/trials/report.md                         … 表（ミッション別 × 週別の試行数・成功率など）
  docs/trials/charts/success_rate_<mission>.png … ミッション別グラフ（成功率の折れ線 + 試行数の棒）
  docs/trials/charts/all_missions.png           … 全体の累計試行回数と成功率

グラフには matplotlib が必要（requirements-dev.txt に入っている）。
無ければ表だけ作って、グラフはスキップする。
"""

import argparse
import csv
import difflib
import os
import sys
from collections import OrderedDict, defaultdict
from datetime import datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRIALS_DIR = os.path.join(ROOT, "docs", "trials")
TRIALS_CSV = os.path.join(TRIALS_DIR, "trials.csv")
REPORT_MD = os.path.join(TRIALS_DIR, "report.md")
CHARTS_DIR = os.path.join(TRIALS_DIR, "charts")

COUNTED = ("success", "fail", "partial")  # 成功率の分母に入れる結果


# ===== 読み込み =====
def load_trials(include_error):
    if not os.path.exists(TRIALS_CSV):
        print(f"記録がまだありません: {TRIALS_CSV}")
        sys.exit(1)
    rows = []
    with open(TRIALS_CSV, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if not r.get("date") or not r.get("result"):
                continue
            if r["result"] not in COUNTED and not (include_error and r["result"] == "error"):
                continue
            r["_date"] = datetime.strptime(r["date"], "%Y-%m-%d").date()
            r["_mission"] = r.get("mission") or os.path.splitext(r.get("script", ""))[0]
            rows.append(r)
    rows.sort(key=lambda r: (r["date"], r.get("time", "")))
    return rows


def bucket_of(d, by):
    """集計の区切り。week なら その週の月曜日、day ならその日。"""
    if by == "day":
        return d
    return d - timedelta(days=d.weekday())


def bucket_label(b, by):
    if by == "day":
        return b.strftime("%m/%d")
    return b.strftime("%m/%d") + "週"


# ===== 集計 =====
def summarize(rows, by):
    """mission -> OrderedDict(bucket -> {"n", "ok"}) を返す。"""
    per = defaultdict(lambda: defaultdict(lambda: {"n": 0, "ok": 0}))
    for r in rows:
        b = bucket_of(r["_date"], by)
        cell = per[r["_mission"]][b]
        cell["n"] += 1
        if r["result"] == "success":
            cell["ok"] += 1
    return {m: OrderedDict(sorted(v.items())) for m, v in per.items()}


def code_changes(rows):
    """mission -> [(初出日, code_hash, snapshot), ...] コードが切り替わった点。"""
    out = defaultdict(list)
    seen = defaultdict(set)
    for r in rows:
        h = r.get("code_hash", "")
        if not h or h in seen[r["_mission"]]:
            continue
        seen[r["_mission"]].add(h)
        out[r["_mission"]].append((r["_date"], h, r.get("snapshot", "")))
    return out


def rate(ok, n):
    return f"{100 * ok / n:.0f}%" if n else "-"


# ===== report.md =====
def snapshot_diff(prev_dir, cur_dir):
    """2 つのスナップショットで同名ファイルの差分を unified diff で返す。"""
    chunks = []
    for name in sorted(os.listdir(os.path.join(ROOT, cur_dir))):
        a = os.path.join(ROOT, prev_dir, name)
        b = os.path.join(ROOT, cur_dir, name)
        if not os.path.exists(a):
            chunks.append(f"（{name} は新規）")
            continue
        with open(a, encoding="utf-8") as fa, open(b, encoding="utf-8") as fb:
            d = list(
                difflib.unified_diff(
                    fa.readlines(),
                    fb.readlines(),
                    fromfile=f"{prev_dir}/{name}",
                    tofile=f"{cur_dir}/{name}",
                    n=2,
                )
            )
        if d:
            chunks.append("".join(d))
    return "\n".join(chunks) if chunks else "（差分なし）"


def write_report(rows, summary, changes, by, args):
    lines = []
    lines.append("# 試行記録レポート")
    lines.append("")
    lines.append(f"生成: {datetime.now().strftime('%Y-%m-%d %H:%M')}  ")
    period = f"{rows[0]['date']} 〜 {rows[-1]['date']}" if rows else "-"
    lines.append(f"期間: {period}  ")
    n = len(rows)
    ok = sum(1 for r in rows if r["result"] == "success")
    lines.append(f"試行: **{n} 回**、成功: **{ok} 回**、成功率: **{rate(ok, n)}**")
    lines.append("")
    lines.append(
        "> 成功率 = success ÷ (success + fail + partial)。"
        + ("error も分母に含む。" if args.include_error else "error（動かなかった）は除外。")
    )
    lines.append("")

    unit = "日" if by == "day" else "週"
    lines.append(f"## ミッション別 × {unit}別")
    lines.append("")
    for mission in sorted(summary):
        buckets = summary[mission]
        total_n = sum(c["n"] for c in buckets.values())
        total_ok = sum(c["ok"] for c in buckets.values())
        lines.append(f"### {mission}（{total_n} 回、成功率 {rate(total_ok, total_n)}）")
        lines.append("")
        lines.append(f"| {unit} | 試行 | 成功 | 成功率 |")
        lines.append("|---|---:|---:|---:|")
        for b, c in buckets.items():
            lines.append(
                f"| {bucket_label(b, by)} | {c['n']} | {c['ok']} | {rate(c['ok'], c['n'])} |"
            )
        lines.append("")
        if changes.get(mission):
            lines.append("コードの切り替わり:")
            lines.append("")
            for d, h, snap in changes[mission]:
                lines.append(f"- {d} から `{h}`（{snap}）")
            lines.append("")
            if args.diff:
                prev = None
                for d, h, snap in changes[mission]:
                    if prev and snap and os.path.isdir(os.path.join(ROOT, snap)):
                        lines.append(f"<details><summary>{prev[1]} → {h} の差分</summary>")
                        lines.append("")
                        lines.append("```diff")
                        lines.append(snapshot_diff(prev[2], snap))
                        lines.append("```")
                        lines.append("</details>")
                        lines.append("")
                    prev = (d, h, snap)

    lines.append("## メンバー別の試行数")
    lines.append("")
    per_member = defaultdict(lambda: {"n": 0, "ok": 0})
    for r in rows:
        m = r.get("member") or "(不明)"
        per_member[m]["n"] += 1
        per_member[m]["ok"] += r["result"] == "success"
    lines.append("| メンバー | 試行 | 成功 | 成功率 |")
    lines.append("|---|---:|---:|---:|")
    for m, c in sorted(per_member.items(), key=lambda kv: -kv[1]["n"]):
        lines.append(f"| {m} | {c['n']} | {c['ok']} | {rate(c['ok'], c['n'])} |")
    lines.append("")

    lines.append("## 直近 10 試行")
    lines.append("")
    lines.append("| 日時 | ミッション | 結果 | メモ | コード |")
    lines.append("|---|---|---|---|---|")
    for r in rows[-10:][::-1]:
        lines.append(
            f"| {r['date']} {r.get('time', '')} | {r['_mission']} | {r['result']} "
            f"| {r.get('note', '')} | `{r.get('code_hash', '')}` |"
        )
    lines.append("")

    if os.path.isdir(CHARTS_DIR):
        lines.append("## グラフ")
        lines.append("")
        for name in sorted(os.listdir(CHARTS_DIR)):
            if name.endswith(".png"):
                lines.append(f"![{name}](charts/{name})")
                lines.append("")

    os.makedirs(TRIALS_DIR, exist_ok=True)
    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"📄 表を書き出しました: {os.path.relpath(REPORT_MD, ROOT)}")


# ===== グラフ =====
def setup_matplotlib():
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib import font_manager
    except ImportError:
        print("⚠ matplotlib が無いのでグラフは作りません（pip install -r requirements-dev.txt）")
        return None
    # 日本語フォントがあれば使う。無ければ英語ラベルにする
    candidates = [
        "Meiryo",
        "Yu Gothic",
        "MS Gothic",
        "Noto Sans CJK JP",
        "IPAGothic",
        "TakaoGothic",
    ]
    available = {f.name for f in font_manager.fontManager.ttflist}
    for c in candidates:
        if c in available:
            plt.rcParams["font.family"] = c
            return plt, True
    return plt, False


def label_set(ja):
    if ja:
        return {
            "rate": "成功率 (%)",
            "n": "試行回数",
            "cum": "累計試行回数",
            "change": "コード変更",
        }
    return {
        "rate": "Success rate (%)",
        "n": "Trials",
        "cum": "Cumulative trials",
        "change": "code change",
    }


def chart_mission(plt, ja, mission, buckets, changes, by):
    L = label_set(ja)
    xs = list(buckets.keys())
    ns = [c["n"] for c in buckets.values()]
    rates = [100 * c["ok"] / c["n"] if c["n"] else 0 for c in buckets.values()]
    width = 0.8 if by == "day" else 5.0

    fig, ax1 = plt.subplots(figsize=(8, 4))
    ax1.bar(xs, ns, width=width, color="#c9d6e8", label=L["n"])
    ax1.set_ylabel(L["n"])
    ax1.set_ylim(0, max(ns + [1]) * 1.3)
    ax2 = ax1.twinx()
    ax2.plot(xs, rates, color="#d9480f", marker="o", linewidth=2, label=L["rate"])
    ax2.set_ylabel(L["rate"])
    ax2.set_ylim(0, 105)
    for d, h, _ in changes[1:]:  # 最初のコードは「変更」ではないので線を引かない
        ax2.axvline(d, color="#868e96", linestyle=":", linewidth=1)
        ax2.text(d, 100, h, rotation=90, va="top", ha="right", fontsize=7, color="#868e96")
    ax1.set_title(f"{mission}")
    fig.autofmt_xdate()
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=8)
    fig.tight_layout()
    path = os.path.join(CHARTS_DIR, f"success_rate_{mission.replace('+', '_')}.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def chart_all(plt, ja, rows, by):
    L = label_set(ja)
    per_day = defaultdict(lambda: {"n": 0, "ok": 0})
    for r in rows:
        b = bucket_of(r["_date"], by)
        per_day[b]["n"] += 1
        per_day[b]["ok"] += r["result"] == "success"
    xs = sorted(per_day)
    cum, total = [], 0
    for x in xs:
        total += per_day[x]["n"]
        cum.append(total)
    rates = [100 * per_day[x]["ok"] / per_day[x]["n"] for x in xs]

    fig, ax1 = plt.subplots(figsize=(8, 4))
    ax1.plot(xs, cum, color="#1c7ed6", marker="s", linewidth=2, label=L["cum"])
    ax1.set_ylabel(L["cum"])
    ax1.set_ylim(0, max(cum + [1]) * 1.15)
    ax2 = ax1.twinx()
    ax2.plot(xs, rates, color="#d9480f", marker="o", linewidth=2, label=L["rate"])
    ax2.set_ylabel(L["rate"])
    ax2.set_ylim(0, 105)
    ax1.set_title("All missions" if not ja else "全ミッション")
    fig.autofmt_xdate()
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=8)
    fig.tight_layout()
    path = os.path.join(CHARTS_DIR, "all_missions.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def make_charts(rows, summary, changes, by):
    mp = setup_matplotlib()
    if mp is None:
        return
    plt, ja = mp
    os.makedirs(CHARTS_DIR, exist_ok=True)
    for old in os.listdir(CHARTS_DIR):
        if old.endswith(".png"):
            os.remove(os.path.join(CHARTS_DIR, old))
    for mission, buckets in summary.items():
        p = chart_mission(plt, ja, mission, buckets, changes.get(mission, []), by)
        print(f"📈 {os.path.relpath(p, ROOT)}")
    p = chart_all(plt, ja, rows, by)
    print(f"📈 {os.path.relpath(p, ROOT)}")


# ===== main =====
def main():
    ap = argparse.ArgumentParser(description="試行記録の集計とグラフ作成")
    ap.add_argument("--since", help="この日以降だけ集計 (YYYY-MM-DD)")
    ap.add_argument("--mission", help="このミッションだけ (例: M01)")
    ap.add_argument("--by", choices=["week", "day"], default="week", help="集計の区切り")
    ap.add_argument("--diff", action="store_true", help="コード変更の差分を report.md に添える")
    ap.add_argument("--include-error", action="store_true", help="error も試行に数える")
    ap.add_argument("--no-charts", action="store_true", help="グラフを作らない")
    args = ap.parse_args()

    rows = load_trials(args.include_error)
    if args.since:
        since = datetime.strptime(args.since, "%Y-%m-%d").date()
        rows = [r for r in rows if r["_date"] >= since]
    if args.mission:
        rows = [r for r in rows if r["_mission"] == args.mission]
    if not rows:
        print("条件に合う記録がありません")
        sys.exit(1)

    summary = summarize(rows, args.by)
    changes = code_changes(rows)
    if not args.no_charts:
        make_charts(rows, summary, changes, args.by)
    write_report(rows, summary, changes, args.by, args)


if __name__ == "__main__":
    main()
