#!/usr/bin/env python3
"""ジャイロの 2 状態の調査（計画 09）のログを表にする。PC 側だけで動く。

  uv run python scripts/gyro_trace_summary.py            … 全部のログ
  uv run python scripts/gyro_trace_summary.py 20260919   … 名前にこの文字を含むログだけ

読むもの:
  docs/logs/run_gyro_state_trace/*.log     … 実験 1（20ms ごとの記録。T, で始まる行）
  docs/logs/run_gyro_pedestal_check/*.log  … 実験 2（台の上の空転）
出すもの:
  docs/gyro_trace/<ログ名>.csv  … 時系列（単位を戻した値 ＋ エンコーダから計算した向き）
  画面                          … 走行ごとの A/B の判定と、ジャイロの向き 90° ごとの
                                  「ジャイロ ÷ エンコーダ」の比率・加速度のばらつき

A/B の判定: 当て直しで読んだ「1 周の読み」を校正前の目盛り（× heading_correction ÷ 360）に直し、
362.5 より大きければ A（約 365）、小さければ B（約 360）。
"""

import csv
import glob
import os
import re
import statistics
import sys

WHEEL_MM = 62.32  # setup.py の ROBOT_PROFILES と同じ
AXLE_MM = 114.48
SEGMENT_DEG = 90
AB_BORDER = 362.5

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS = os.path.join(ROOT, "docs", "logs")
OUT_DIR = os.path.join(ROOT, "docs", "gyro_trace")

NUM = r"(-?\d+(?:\.\d+)?)"


def find(text, pattern):
    m = re.search(pattern, text)
    return float(m.group(1)) if m else None


def heading_correction(text):
    m = re.search(r"# imu\.settings: \(.*?" + NUM + r"\)\s*$", text, re.M)
    return float(m.group(1)) if m else 360.0


def state_of(per_turn, correction):
    if per_turn is None:
        return "?", None
    raw = per_turn * correction / 360
    return ("A" if raw > AB_BORDER else "B"), raw


def summarize_trace(path):
    text = open(path, encoding="utf-8", errors="replace").read()
    rows = [
        [int(v) for v in line.split(",")[1:]]
        for line in text.splitlines()
        if line.startswith("T,") and line.count(",") == 10
    ]
    name = os.path.splitext(os.path.basename(path))[0]
    correction = heading_correction(text)
    state, raw = state_of(find(text, r"1 周の読み: " + NUM), correction)
    volt = find(text, r"# 電池: " + NUM)
    print(f"\n=== {name}  状態 {state}  1 周の読み(校正前の目盛り) {raw and round(raw, 2)}"
          f"  校正表 {correction}  電池 {volt and int(volt)} mV  記録 {len(rows)} 行")
    if len(rows) < 10:
        print("  （T, の行が足りない。記録が出おわる前に止めた？）")
        return None

    table = []
    for ms, h, rz, wz, ax, ay, az, left, right, still in rows:
        enc = (left - right) / 2 * WHEEL_MM / AXLE_MM  # エンコーダから計算した機体の向き (度)
        acc = (ax * ax + ay * ay + az * az) ** 0.5
        table.append([ms, h / 100, rz / 100, wz / 10, ax, ay, az, left, right, still, round(enc, 2), round(acc, 1)])
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, name + ".csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ms", "heading", "rotZ", "wz", "ax", "ay", "az", "left", "right",
                    "stationary", "enc_heading", "acc_abs"])
        w.writerows(table)

    print("  区間(ジャイロ)   ジャイロ÷エンコーダ  |rotZ|÷ジャイロ  加速度のSD(mm/s²)  静止判定")
    ratios = []
    start = 0
    edge = SEGMENT_DEG
    for i, r in enumerate(table):
        last = i == len(table) - 1
        if r[1] < edge and not last:
            continue
        seg = table[start:i + 1]
        d_gyro = seg[-1][1] - seg[0][1]
        d_enc = seg[-1][10] - seg[0][10]
        d_rz = abs(seg[-1][2] - seg[0][2])
        if d_gyro > SEGMENT_DEG / 2 and d_enc:
            ratio = d_gyro / d_enc
            ratios.append(ratio)
            sd = statistics.pstdev([s[11] for s in seg])
            still = sum(s[9] for s in seg)
            print(f"  {seg[0][1]:7.1f}〜{seg[-1][1]:7.1f}   {ratio:8.4f}           {d_rz / d_gyro:8.4f}"
                  f"       {sd:8.1f}          {still}/{len(seg)}")
        start = i
        edge += SEGMENT_DEG
    total = (table[-1][1] - table[0][1]) / (table[-1][10] - table[0][10])
    print(f"  全体の比率 {total:.4f} / 区間の最小〜最大 {min(ratios):.4f}〜{max(ratios):.4f}"
          f" / 加速度のSD(全体) {statistics.pstdev([r[11] for r in table]):.1f}")
    return {"name": name, "state": state, "ratio": total, "volt": volt}


def summarize_pedestal(path):
    text = open(path, encoding="utf-8", errors="replace").read()
    name = os.path.splitext(os.path.basename(path))[0]
    moved = find(text, r"動いたジャイロの向き: " + NUM)
    still = re.search(r"静止と判定 (\d+) / (\d+)", text)
    wz = re.search(r"Z 角速度の範囲: " + NUM + " 〜 " + NUM, text)
    volt = find(text, r"# 電池: " + NUM)
    print(f"  {name}  動いた向き {moved} 度  静止判定 {still.group(1) + '/' + still.group(2) if still else '?'}"
          f"  Z角速度 {wz.group(1) + '〜' + wz.group(2) if wz else '?'} deg/s  電池 {volt and int(volt)} mV")


def main():
    key = sys.argv[1] if len(sys.argv) > 1 else ""
    pedestal = sorted(p for p in glob.glob(os.path.join(LOGS, "run_gyro_pedestal_check", "*.log")) if key in p)
    if pedestal:
        print("=== 実験 2: 台の上の空転（機体は回らない。0 度なら振動・電流の影響なし）")
        for p in pedestal:
            summarize_pedestal(p)
    results = []
    for p in sorted(p for p in glob.glob(os.path.join(LOGS, "run_gyro_state_trace", "*.log")) if key in p):
        r = summarize_trace(p)
        if r:
            results.append(r)
    if results:
        print("\n=== 実験 1 のまとめ（状態ごとの「ジャイロ ÷ エンコーダ」）")
        for state in ("A", "B", "?"):
            rs = [r["ratio"] for r in results if r["state"] == state]
            if rs:
                print(f"  状態 {state}: n={len(rs)}  平均 {statistics.mean(rs):.4f}"
                      f"  最小〜最大 {min(rs):.4f}〜{max(rs):.4f}")
    if not pedestal and not results:
        print("ログがまだありません（docs/logs/run_gyro_pedestal_check・run_gyro_state_trace）")


if __name__ == "__main__":
    main()
