"""
【新旧 setup.py の比較走行を 1 コマンドで走らせて記録する】（PC 側だけで動く。Step 9 用）

使い方（リポジトリのルートで実行する）:
  uv run python verification/compare.py new straight
  uv run python verification/compare.py old straight
      設定: new / old / oldfull      コース: straight / turn / square / mission
      ハブ名を変えるとき: --name "Pybricks Hub4"（省略時は Pybricks Hub3）

やること:
  1. cmp_<設定>_<コース>.py をハブへ送って走らせる（画面の出力はそのまま表示し、docs/logs/compare/ に保存）
  2. 走り終わったら、ものさしで測った値をターミナルで聞く（Enter だけなら空欄）
  3. docs/compare/compare_trials.csv に 1 行足す（所要時間・ジャイロ・ハブの距離・電池は出力から自動で読む）

置きミス・障害物のときは、最後の「メモ」に  除外 ぶつかった  のように「除外」から書く（行は消さない）。
2026-09-18: turn / square / mission の向きのズレは、走り終わりにハブのライトが緑になったら機体の左側面を定規に当て直して測る
  （ジャイロの差＝本当のズレ。右に回りすぎが＋）。出力から自動で拾うので、ターミナルでは聞かない。当て直しを忘れた回は「除外」にする。
ハブへ送るコード（setup.py / run_setup_compare.py）には手を入れない。
"""

import csv
import os
import re
import subprocess
import sys
from datetime import datetime

SETTINGS = ("new", "old", "oldfull")
COURSES = ("straight", "turn", "square", "mission")
FIELDS = [
    "日時", "設定", "コース", "試行", "所要時間_秒", "ジャイロ_度", "ハブ距離_mm", "電池_mV",
    "実測距離_mm", "向きのズレ_度", "終点のズレ_mm", "メモ", "ログ",
]  # fmt: skip

# コースごとに聞くもの（列名, 聞き方）
QUESTIONS = {
    "straight": [
        ("実測距離_mm", "ものさしで測った距離 (mm)"),
        ("向きのズレ_度", "止まった時の向きのズレ (度・右が＋・測れなければ Enter)"),
    ],
    "turn": [("向きのズレ_度", "スタートの向きとのズレ (度・右に回りすぎが＋)")],
    "square": [("終点のズレ_mm", "終点のスタートからのズレ (mm)")],
    "mission": [("終点のズレ_mm", "終点のスタートからのズレ (mm)")],
}


def parse_output(text):
    """ハブの出力から数字を拾う（無ければ空欄）"""

    def find(pattern):
        m = re.search(pattern, text)
        return m.group(1) if m else ""

    return {
        "所要時間_秒": find(r"# 所要時間: ([\d.]+)"),
        "ジャイロ_度": find(r"# ジャイロの向き: (-?[\d.]+)"),
        "ハブ距離_mm": find(r"# エンコーダの距離: (-?[\d.]+)"),
        "電池_mV": find(r"電池: (\d+)"),
        # 2026-09-18: turn / square / mission は走り終わりに手で定規に当て直し、ジャイロの差で本当の向きのズレを出す
        "向きのズレ_度": find(r"# 向きの実測ズレ_右が＋: (-?[\d.]+)"),
    }


def ask_number(label):
    while True:
        ans = input(f"  {label}: ").strip().replace("，", ",").replace("．", ".")
        if ans == "":
            return ""
        try:
            float(ans)
            return ans
        except ValueError:
            print("  ! 数字で入れてね（空欄なら Enter だけ）")


def next_trial(path, setting, course):
    if not os.path.exists(path):
        return 1
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["設定"] == setting and r["コース"] == course]
    return len(rows) + 1


def main():
    args = sys.argv[1:]
    hub_name = "Pybricks Hub3"
    if "--name" in args:
        i = args.index("--name")
        hub_name = args[i + 1]
        del args[i : i + 2]
    if len(args) != 2 or args[0] not in SETTINGS or args[1] not in COURSES:
        print(
            "Usage: python verification/compare.py <new|old|oldfull> <straight|turn|square|mission> [--name <hub>]"
        )
        sys.exit(1)
    setting, course = args

    here = os.path.dirname(os.path.abspath(__file__))  # verification/
    root = os.path.dirname(here)  # リポジトリのルート（setup.py・docs/ がある）
    run_file = os.path.join(here, f"cmp_{setting}_{course}.py")
    if not os.path.exists(run_file):
        print(f"! {os.path.basename(run_file)} がありません")
        sys.exit(1)

    start = datetime.now()
    log_dir = os.path.join(root, "docs", "logs", "compare")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"{start.strftime('%Y%m%d_%H%M%S')}_{setting}_{course}.log")
    csv_path = os.path.join(root, "docs", "compare", "compare_trials.csv")
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    trial = next_trial(csv_path, setting, course)

    print(f"📝 比較走行: {setting} / {course} / この組の {trial} 本目 / ハブ: {hub_name}\n")
    # -u と PYTHONUNBUFFERED: パイプにつなぐと pybricksdev の出力がまとめて届き、走行中の「★測って★」を拾えない（2026-09-18）
    # pybricksdev は送るスクリプトと同じフォルダからしか import を探さないので、setup.py と一緒に .hub_stage/ へ写す
    sys.path.insert(0, root)
    from run_with_log import stage_for_hub

    hub_file = stage_for_hub(run_file, root)
    cmd = [sys.executable, "-u", "-m", "pybricksdev", "run", "ble", hub_file, "--name", hub_name]
    env = dict(os.environ, PYTHONUNBUFFERED="1", PYTHONIOENCODING="utf-8")
    lines = []
    answered = {}  # 走行の途中でターミナルに入れてもらった値（square / mission の終点のズレ）
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    try:
        for line in process.stdout:
            print(line, end="")
            lines.append(line)
            if "# ★測って★" in line:
                # 2026-09-18: ハブは右ボタン（▶）が押されるまで待っている。ここで測った値を入れてもらう
                print("\n━━━ いま測って入れてね（ハブは黄色で待っています）━━━")
                for key, label in QUESTIONS[course]:
                    if key == "向きのズレ_度":
                        continue  # 向きは当て直しで自動
                    answered[key] = ask_number(label)
                print(
                    "  ✓ 入れました。ハブの右ボタン（▶）を押して、ライトが緑になったら当て直してね\n"
                )
    except KeyboardInterrupt:
        print("\n⏹ 停止しました")
        lines.append("\n[Ctrl+C で停止]\n")
        try:
            process.terminate()
            process.wait(timeout=5)
        except Exception:
            process.kill()
    process.wait()
    text = "".join(lines)
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(text)

    row = dict.fromkeys(FIELDS, "")
    row.update(parse_output(text))
    row.update({k: v for k, v in answered.items() if v != ""})
    row.update(
        {
            "日時": start.strftime("%Y-%m-%d %H:%M:%S"),
            "設定": setting,
            "コース": course,
            "試行": trial,
            "ログ": os.path.relpath(log_path, root).replace("\\", "/"),
        }
    )

    print("\n━━━ ものさしで測った値を入れてね（Enter だけなら空欄）━━━")
    if row["所要時間_秒"] == "":
        print("  ※ 走行が最後まで終わっていないようです。メモに「除外 理由」と書いてね")
    for key, label in QUESTIONS[course]:
        if row.get(key):  # 出力から拾えたものは聞かない（向きのズレ＝当て直しの結果）
            print(f"  {label}: {row[key]}（当て直しの結果を自動で記録）")
            continue
        row[key] = ask_number(label)
    row["メモ"] = input("  メモ（なければ Enter・外すときは「除外 理由」）: ").strip()

    new_file = not os.path.exists(csv_path)
    # BOM は新規作成のときだけ付ける（追記で utf-8-sig を使うと行の途中に BOM が入る）
    with open(csv_path, "a", encoding="utf-8-sig" if new_file else "utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            w.writeheader()
        w.writerow(row)
    print(f"✓ 記録しました: docs/compare/compare_trials.csv（{setting}/{course} の {trial} 本目）")


if __name__ == "__main__":
    main()
