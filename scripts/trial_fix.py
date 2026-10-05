#!/usr/bin/env python3
"""
【試行記録を直す】（2026-10-03）
docs/trials/trials.csv に記録したあとで、成否やメモのまちがいに気づいたときに直す道具。PC 側だけで動く。

  uv run python scripts/trial_fix.py            # 直近 10 本から選んで直す
  uv run python scripts/trial_fix.py --last 30  # 直近 30 本から選ぶ

1. 直近の記録が番号つきで出る（新しいものが 1 番）。直したい番号を入れる
2. 走らせたときと同じ聞き方で、ミッションの順に成否を入れ直す（いまの値が [ ] の中に出るので、そのままなら Enter）
   b で 1 つ前に戻る。s を押すと「この記録を消す」（まちがえて記録したとき）
3. 確認の画面で Enter を押すと、その 1 行だけを書きかえて、ダッシュボードを作り直す

trials.csv は追記だけが決まりだが、この道具を通したときだけ、その 1 行の result・mission_results・part_results・note の
書きかえ（または行の削除）を許す。ほかの列と、ほかの行には触らない。仕様は docs/trial_log_spec.md の §9・§11。
項目のあるミッション（M12 の支柱とサポートタイなど）は、項目ごとに入れ直す（2026-10-05）。
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trial_results as tr  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRIALS_CSV = os.path.join(ROOT, "docs", "trials", "trials.csv")
COLUMNS = ["mission_results", "run_sec", "part_results"]  # 古い trials.csv の見出しに足す列

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def label_of(row):
    """一覧に出す 1 行ぶんの説明。"""
    pairs = tr.results_of(row)
    if row.get("result") == "error" or not pairs:
        what = tr.RESULT_LABEL.get(row.get("result", ""), row.get("result", ""))
    else:
        what = tr.describe_row(row)
    via = f" [{row['via']}]" if row.get("via") else ""
    note = f" ／ メモ: {row['note']}" if row.get("note") else ""
    return f"{row.get('date', '')[5:]} {row.get('time', '')[:5]}  {row.get('script', '')}{via}  {what}{note}"


def item_of(row):
    """いまの記録を、入れ直しの初期値にした 1 本ぶん。"""
    missions = tr.missions_of(row)
    title = f"{row.get('date', '')} {row.get('time', '')[:5]} {row.get('script', '')}"
    if missions:
        title += f"（{' → '.join(missions)}）"
    result = row.get("result", "")
    if result == "error":
        item = tr.new_item(title, missions, whole="e")
        item["whole_at"] = tr.first_step_key(missions)  # 最初の質問に「e」が出る
        return item
    parts = {}
    if missions:
        answers = {}
        for m, res in tr.results_of(row):
            if not tr.parts_of(m):
                answers[m] = tr.KEY_OF.get(res, "o")
            elif res == "unreached":
                answers[m] = "-"
            else:
                values = tr.values_in(
                    row, m, res
                )  # 項目の分からない古い「途中まで」は None → 既定値で聞く
                if values is not None:
                    parts[m] = {pid: key_of_value(m, pid, v) for pid, v in values.items()}
    else:
        answers = {None: tr.KEY_OF.get(result, "o")}
    return tr.new_item(title, missions, answers=answers, note=row.get("note", ""), parts=parts)


def key_of_value(mission, part_id, value):
    """項目の値 → 入れ直しの初期値のキー（yesno は o / x、個数・段階は x か数字）。"""
    part = next(p for p in tr.PARTS[mission] if p["id"] == part_id)
    if part["kind"] == "yesno":
        return "o" if value else "x"
    return str(value) if value else "x"


def main():
    ap = argparse.ArgumentParser(description="trials.csv の記録を 1 本えらんで直す")
    ap.add_argument("--last", type=int, default=10, help="一覧に出す本数（既定 10）")
    ap.add_argument("--csv", default=TRIALS_CSV, help="直す CSV（省略時は docs/trials/trials.csv）")
    args = ap.parse_args()

    if not os.path.exists(args.csv):
        print(f"記録がまだありません: {args.csv}")
        return 1
    tr.ensure_header(args.csv, COLUMNS)
    _, rows, _ = tr.read_rows(args.csv)
    if not rows:
        print("記録がまだありません")
        return 1

    shown = list(range(len(rows) - 1, max(-1, len(rows) - 1 - args.last), -1))
    print(f"── 直近 {len(shown)} 本の記録（新しい順）──")
    for n, index in enumerate(shown, 1):
        print(f" {n:>2}  {label_of(rows[index])}")
    try:
        key = input("直す番号（Enter=やめる）> ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return 0
    if not key:
        return 0
    if not key.isdigit() or not 1 <= int(key) <= len(shown):
        print(f"1〜{len(shown)} の番号を入れてね")
        return 1
    index = shown[int(key) - 1]
    row = rows[index]

    item = item_of(row)
    ok = tr.ask_trials(
        [item],
        heading="この内容に直します",
        skip_label="この記録を消す",
        ok_label="直す",
        cancel_label="直さずにやめる",
    )
    if not ok:
        print("直しませんでした")
        return 0

    result, mission_results = tr.item_results(item)
    if result is None:
        tr.replace_row(args.csv, index, None)
        print(f"🗑 消しました: {label_of(row)}")
    else:
        new = dict(
            row,
            result=result,
            mission_results=mission_results,
            part_results=tr.item_parts(item),
            note=item["note"],
        )
        tr.replace_row(args.csv, index, new)
        print(f"✓ 直しました: {label_of(new)}")

    try:
        import trial_dashboard

        trial_dashboard.build_all(csv_path=args.csv)
        print("📊 ダッシュボードを作り直しました（ブラウザで F5）")
    except Exception as e:
        print(f"⚠ ダッシュボードを作り直せませんでした: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
