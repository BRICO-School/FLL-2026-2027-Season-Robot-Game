#!/usr/bin/env python3
"""手押しティーチング: 手で押して動かした記録（teach_record.py のログ）から run ファイルのコードを起こす。PC 側だけで動く。

  uv run python scripts/teach.py --name "Pybricks Hub3"            … 記録して、そのままコードにする
  uv run python scripts/teach.py                                   … いちばん新しい記録をコードにする
  uv run python scripts/teach.py docs/logs/teach_record/<日時>.log  … 指定した記録をコードにする
  uv run python scripts/teach.py --out run_M05_kanna.py            … run_template.py の形で run ファイルに書き出す
      （--name と --out はいっしょに使える。すでにあるファイルには書かない）

読むもの: docs/logs/teach_record/*.log（# teach: の行と P, で始まる行。記録の手順は teach_record.py）
出すもの: 画面 … run() の中にそのまま貼れるコード / --out … run ファイル

コードの起こし方:
  1. タイヤが --pause ms 以上回らなかったところで区切る（手を止めたところ）。アームはアームごとに同じように区切る
  2. 区切りの中は「進んだ距離」と「向き」のグラフを折れ線で近似して（許すずれ --tol mm）、1 本ずつ
       ・進んだ距離が --min-dist mm より小さい、または回る中心が機体の中心から --min-radius mm 以内 → 回転 turn
       ・向きが 10° 以内しか変わらず、まっすぐな線からのはみ出しが --tol mm 以内           → 直進 straight
       ・それ以外 → カーブ curve
     に分ける（回転の 1° は「タイヤの間隔の半分」の円の 1° ぶんの弧の長さ (mm) に直して、距離とそろえる）
  3. 続けて同じ向きに回った・進んだものは 1 つにまとめる（持ちかえで止まったぶん）
  4. 回転とカーブの角度は、ジャイロの向き（スタートからの値）に合わせて決める。Pybricks は命令した
     角度の合計を目標の向きとして覚えているので、押したときのふらつきは次の回転で取り戻される。
     直進は、押した始まりと終わりを結ぶ向きが --min-turn 度以上ずれていたら、先に向きを合わせる
  5. 起こしたコードを計算の上で走らせて、手で押した終点とのずれを出す（タイヤのすべり・機体のくせは入っていない）

アームの速さは --arm-speed（deg/s）。直進・回転・カーブの速さは指定しない（setup.py の既定値で走る）。
"""

import argparse
import glob
import math
import os
import re
import subprocess
import sys
from dataclasses import dataclass

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RECORDER = "teach_record.py"
LOG_DIR = os.path.join(ROOT, "docs", "logs", "teach_record")
TEMPLATE = os.path.join(ROOT, "run_template.py")
TEMPLATE_SAMPLE = re.compile(r"^\s*await robot\.straight\(500, speed=500\).*$")
TEMPLATE_MARK = "# ここにロボットの動作を記述してください"

# ログに # teach: の行が無いとき（setup.py の DEFAULT_PROFILE と同じ）
DEFAULT_WHEEL = 62.32
DEFAULT_AXLE = 114.48

STRAIGHT_MAX_TURN = 10  # 直進とみなすのは、向きの変わりがこの角度 (度) 以内のときだけ
LIFT_WARN_DEG = (
    5  # タイヤが止まっている間に向きがこれだけ変わったら「持ち上げて回した？」と知らせる
)

HEADER = re.compile(r"# teach: wheel=(\d+(?:\.\d+)?) axle=(\d+(?:\.\d+)?)")
ROW = re.compile(r"P,(\d+),(-?\d+),(-?\d+),(-?\d+),(-?\d+),(-?\d+)\s*$")


@dataclass
class Sample:
    t: int  # ハブの時計 (ms)
    left: int  # 左タイヤの角度 (度)
    right: int  # 右タイヤの角度 (度)
    heading: float  # ジャイロの向き (度・時計回りが＋)
    arm_l: int  # 左アームの角度 (度)
    arm_r: int  # 右アームの角度 (度)
    s: float = 0.0  # スタートから進んだ距離 (mm・左右の平均)
    x: float = 0.0  # スタートの向きを x、右を y とした位置 (mm)
    y: float = 0.0


@dataclass
class Move:
    kind: str  # "straight" / "turn" / "curve" / "arm"
    i0: int  # samples の番号（始まり・終わり）
    i1: int
    arm: str = ""  # "left" / "right"（アームのとき）
    deg: int = 0  # アームを回した角度（アームのとき）
    overlap: bool = False  # 走りながらアームを動かしていた


# ===== ログを読む =====
def parse_log(text):
    wheel, axle = DEFAULT_WHEEL, DEFAULT_AXLE
    header = HEADER.search(text)
    if header:
        wheel, axle = float(header.group(1)), float(header.group(2))
    samples = []
    for line in text.splitlines():
        m = ROW.search(line)
        if m:
            t, left, right, h10, arm_l, arm_r = (int(v) for v in m.groups())
            samples.append(Sample(t, left, right, h10 / 10, arm_l, arm_r))
    dead_reckon(samples, wheel)
    return wheel, axle, samples, header is not None


def dead_reckon(samples, wheel):
    """タイヤの角度とジャイロの向きから、進んだ距離と位置を足しあげる"""
    mm_per_deg = wheel * math.pi / 360
    for i, p in enumerate(samples):
        p.s = (p.left + p.right) / 2 * mm_per_deg
        if i == 0:
            continue
        q = samples[i - 1]
        ds = p.s - q.s
        th = math.radians((p.heading + q.heading) / 2)
        p.x = q.x + ds * math.cos(th)
        p.y = q.y + ds * math.sin(th)
    if samples:
        s0 = samples[0].s
        for p in samples:
            p.s -= s0


# ===== 区切る =====
def segments(samples, key, pause_ms):
    """key の値が変わり続けている区間 (始まり, 終わり) の一覧。pause_ms より長く変わらなければ区切る"""
    segs = []
    start = last = None
    for i in range(1, len(samples)):
        if key(samples[i]) == key(samples[i - 1]):
            continue
        if start is not None and samples[i].t - samples[last].t > pause_ms:
            segs.append((start, last))
            start = None
        if start is None:
            start = i - 1
        last = i
    if start is not None:
        segs.append((start, last))
    return segs


def _dist_to_segment(p, a, b):
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = bx - ax, by - ay
    length2 = dx * dx + dy * dy
    if length2 == 0:
        return math.hypot(px - ax, py - ay)
    u = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length2))
    return math.hypot(px - (ax + u * dx), py - (ay + u * dy))


def simplify(points, tol):
    """折れ線の近似（Douglas-Peucker）。残す点の番号を返す"""
    keep = {0, len(points) - 1}
    stack = [(0, len(points) - 1)]
    while stack:
        a, b = stack.pop()
        worst, idx = 0.0, None
        for i in range(a + 1, b):
            d = _dist_to_segment(points[i], points[a], points[b])
            if d > worst:
                worst, idx = d, i
        if idx is not None and worst > tol:
            keep.add(idx)
            stack += [(a, idx), (idx, b)]
    return sorted(keep)


def classify(samples, i0, i1, opt):
    """1 本の線を turn / straight / curve に分ける。小さすぎて無視するときは None"""
    ds = samples[i1].s - samples[i0].s
    dh = samples[i1].heading - samples[i0].heading
    dist, rot = abs(ds), abs(dh)
    if dist < opt.min_dist and rot < opt.min_turn:
        return None
    radius = dist / math.radians(rot) if rot > 0 else math.inf
    if dist < opt.min_dist or radius < opt.min_radius:
        return "turn"
    sagitta = radius * (1 - math.cos(math.radians(rot) / 2)) if rot > 0 else 0.0
    if rot <= STRAIGHT_MAX_TURN and sagitta <= opt.tol:
        return "straight"
    return "curve"


def drive_moves(samples, opt, axle):
    mm_per_turn_deg = axle / 2 * math.pi / 180  # その場で 1° 回るとき、タイヤが進む距離 (mm)
    moves = []
    for i0, i1 in segments(samples, lambda p: (p.left, p.right), opt.pause):
        pts = [(samples[i].s, samples[i].heading * mm_per_turn_deg) for i in range(i0, i1 + 1)]
        keep = simplify(pts, opt.tol)
        for a, b in zip(keep, keep[1:], strict=False):
            kind = classify(samples, i0 + a, i0 + b, opt)
            if kind:
                moves.append(Move(kind, i0 + a, i0 + b))
    return moves


def arm_moves(samples, opt):
    moves = []
    for arm, key in (("left", lambda p: p.arm_l), ("right", lambda p: p.arm_r)):
        for i0, i1 in segments(samples, key, opt.pause):
            deg = key(samples[i1]) - key(samples[i0])
            if abs(deg) >= opt.min_arm:
                moves.append(Move("arm", i0, i1, arm=arm, deg=deg))
    return moves


def merge(moves, samples, opt):
    """続けて同じ向きに回った・進んだもの（持ちかえで止まったぶん）を 1 つにまとめる"""
    out = []
    for m in moves:
        prev = out[-1] if out else None
        if prev is not None and prev.kind == m.kind:
            if m.kind == "turn":
                same = _sign(_dh(samples, prev)) == _sign(_dh(samples, m))
            elif m.kind == "straight":
                # 止まっている間に向きが変わっていたら（持ち上げて回したなど）、まとめない
                turned = samples[m.i0].heading - samples[prev.i1].heading
                same = (
                    _sign(_ds(samples, prev)) == _sign(_ds(samples, m))
                    and abs(turned) < opt.min_turn
                )
            elif m.kind == "arm":
                same = prev.arm == m.arm and _sign(prev.deg) == _sign(m.deg)
            else:
                same = False
            if same:
                prev.i1 = m.i1
                prev.deg += m.deg
                prev.overlap = prev.overlap or m.overlap
                continue
        out.append(m)
    return out


def _ds(samples, m):
    return samples[m.i1].s - samples[m.i0].s


def _dh(samples, m):
    return samples[m.i1].heading - samples[m.i0].heading


def _sign(v):
    return (v > 0) - (v < 0)


# ===== コードにする =====
def _turn_line(angle, note=""):
    side = "右" if angle > 0 else "左"
    return f"await robot.turn({angle})", f"{note}{side} {abs(angle)}°"


def _straight_line(dist):
    return f"await robot.straight({dist})", f"{'前進' if dist > 0 else '後退'} {abs(dist)}mm"


def to_code(moves, samples, opt):
    """(コード, コメント) の一覧を返す。向きはスタートからの絶対値で追いかける"""
    lines = []
    cmd = 0  # ここまでに命令した角度の合計（Pybricks が目標の向きとして覚えている値）
    for m in moves:
        p, q = samples[m.i0], samples[m.i1]
        if m.kind == "arm":
            name = "左" if m.arm == "left" else "右"
            lift = "left_lift" if m.arm == "left" else "right_lift"
            note = f"{name}アーム {m.deg}°" if m.deg > 0 else f"{name}アームを逆に {-m.deg}°"
            if m.overlap:
                note += "（走りながら動かしていた。同時にするなら multitask）"
            lines.append((f"await {lift}.run_angle({opt.arm_speed}, {m.deg})", note))
            continue

        ds = q.s - p.s
        if m.kind == "turn":
            angle = round(q.heading - cmd)
            if abs(angle) >= opt.min_turn:
                lines.append(_turn_line(angle))
                cmd += angle
            continue

        if m.kind == "straight":
            # 押した始まりと終わりを結ぶ向き（後ろに押したときは反対向き）
            chord = math.hypot(q.x - p.x, q.y - p.y)
            face = math.degrees(math.atan2(q.y - p.y, q.x - p.x)) + (180 if ds < 0 else 0)
            # atan2 は ±180° で折り返すので、ジャイロの向きの値（何周しても続く）の近くに合わせる
            face += 360 * round(((p.heading + q.heading) / 2 - face) / 360)
            align = round(face - cmd)
            if abs(align) >= opt.min_turn:
                lines.append(_turn_line(align, "向きを合わせる "))
                cmd += align
            dist = round(chord) * _sign(ds)
            if dist:
                lines.append(_straight_line(dist))
            continue

        # curve: 始まりの向きを合わせてから、終わりの向きまで円の上を走る
        align = round(p.heading - cmd)
        if abs(align) >= opt.min_turn:
            lines.append(_turn_line(align, "向きを合わせる "))
            cmd += align
        h = round(q.heading - cmd)
        if abs(h) < opt.min_turn:
            lines.append(_straight_line(round(ds)))
            continue
        radius = max(1, round(abs(ds) / math.radians(abs(h))))  # Pybricks は半径 0 を受けつけない
        angle = abs(h) * _sign(ds)  # Pybricks: 角度が＋なら前進・－なら後退
        radius *= _sign(h) * _sign(ds)  # 半径が＋なら右回りの円・－なら左回りの円
        side = "右" if h > 0 else "左"
        way = "前進" if ds > 0 else "後退"
        lines.append(
            (
                f"await robot.curve({radius}, {angle})",
                f"カーブ 半径 {abs(radius)}mm・{side} {abs(h)}°（{way} {round(abs(ds))}mm）",
            )
        )
        cmd += h
    return lines


def simulate(lines):
    """起こしたコードを、すべりの無い理想の機体で走らせたときの終点 (x, y, 向き)"""
    x = y = 0.0
    h = 0.0
    for code, _ in lines:
        m = re.match(r"await robot\.(straight|turn|curve)\((-?\d+)(?:, (-?\d+))?\)", code)
        if not m:
            continue
        kind, a = m.group(1), int(m.group(2))
        if kind == "straight":
            x += a * math.cos(math.radians(h))
            y += a * math.sin(math.radians(h))
        elif kind == "turn":
            h += a
        else:
            radius, angle = a, int(m.group(3))
            dist = abs(radius) * math.radians(angle)
            dh = angle if radius >= 0 else -angle
            steps = 100
            for _ in range(steps):
                mid = math.radians(h + dh / steps / 2)
                x += dist / steps * math.cos(mid)
                y += dist / steps * math.sin(mid)
                h += dh / steps
    return x, y, h


def lift_warnings(samples, opt):
    """タイヤが止まっている間に向きが大きく変わったところ（持ち上げて回した？）"""
    notes = []
    segs = segments(samples, lambda p: (p.left, p.right), opt.pause)
    ends = [0] + [b for _, b in segs]
    starts = [a for a, _ in segs] + [len(samples) - 1]
    for e, s in zip(ends, starts, strict=True):
        dh = samples[s].heading - samples[e].heading
        if abs(dh) >= LIFT_WARN_DEG:
            notes.append(
                f"{samples[e].t / 1000:.1f}〜{samples[s].t / 1000:.1f} 秒のあいだに、"
                f"タイヤが止まったまま向きが {dh:+.1f}° 変わった（持ち上げて回した？）。"
                "向きは次の回転で取り戻すが、動いた距離は入っていない"
            )
    return notes


# ===== 全体 =====
def build(text, opt):
    wheel, axle, samples, has_header = parse_log(text)
    if len(samples) < 2:
        raise SystemExit(
            "P, で始まる行がありません（ハブにつながらなかった？ teach_record.py の記録ですか？）"
        )
    moves = drive_moves(samples, opt, axle) + arm_moves(samples, opt)
    moves.sort(key=lambda m: (samples[m.i0].t, m.kind == "arm"))
    for a in moves:
        if a.kind != "arm":
            continue
        a.overlap = any(
            d.kind != "arm"
            and samples[d.i0].t < samples[a.i1].t
            and samples[a.i0].t < samples[d.i1].t
            for d in moves
        )
    moves = merge(moves, samples, opt)
    lines = to_code(moves, samples, opt)
    return wheel, axle, samples, has_header, lines


def newest_log():
    logs = sorted(glob.glob(os.path.join(LOG_DIR, "*.log")))
    if not logs:
        raise SystemExit(f"記録がありません: {LOG_DIR}（先に --name を付けて記録してね）")
    return logs[-1]


def record(hub_name):
    """run_with_log.py で teach_record.py を走らせて、できたログのパスを返す"""
    before = set(glob.glob(os.path.join(LOG_DIR, "*.log")))
    cmd = [sys.executable, "run_with_log.py", RECORDER, "--name", hub_name, "--no-trial"]
    env = dict(os.environ, PYTHONUTF8="1")
    proc = subprocess.Popen(cmd, cwd=ROOT, env=env)
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.wait()  # Ctrl+C のときも、run_with_log.py がログを書きおえるのを待つ
    new = sorted(set(glob.glob(os.path.join(LOG_DIR, "*.log"))) - before)
    if not new:
        raise SystemExit("記録のログができませんでした")
    return new[-1]


def write_run_file(path, lines, log_rel):
    if os.path.exists(path):
        raise SystemExit(f"{path} はもうあります。別の名前にしてね（上書きはしない）")
    with open(TEMPLATE, encoding="utf-8", newline="") as f:
        text = f.read()
    nl = "\r\n" if "\r\n" in text else "\n"
    body = [f"    # ↓ 手押しの記録から起こした（{log_rel}）"] + [
        f"    {code}  # {note}" for code, note in lines
    ]
    rows = text.split(nl)
    at = next((i for i, r in enumerate(rows) if TEMPLATE_SAMPLE.match(r)), None)
    if at is not None:
        rows[at : at + 1] = body
    else:
        mark = next((i for i, r in enumerate(rows) if TEMPLATE_MARK in r), None)
        if mark is None:
            raise SystemExit(f"{TEMPLATE} に書きこむ場所（{TEMPLATE_MARK}）が見つかりません")
        rows[mark + 2 : mark + 2] = [""] + body
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(nl.join(rows))


def main():
    ap = argparse.ArgumentParser(
        description="手で押して動かした記録から run ファイルのコードを起こす"
    )
    ap.add_argument(
        "log", nargs="?", help="ログのパス（省略時は docs/logs/teach_record/ のいちばん新しいもの）"
    )
    ap.add_argument("--name", help="ハブの名前。付けると先に teach_record.py で記録する")
    ap.add_argument(
        "--out", help="run_template.py の形で書き出す run ファイル（例: run_M05_kanna.py）"
    )
    ap.add_argument(
        "--pause", type=int, default=500, help="これより長く止まったら区切る (ms・既定 500)"
    )
    ap.add_argument("--tol", type=float, default=8, help="線で近似するときに許すずれ (mm・既定 8)")
    ap.add_argument(
        "--min-dist", type=float, default=10, help="これより短い移動は回転とみなす (mm・既定 10)"
    )
    ap.add_argument(
        "--min-turn", type=float, default=3, help="これより小さい回転は書かない (度・既定 3)"
    )
    ap.add_argument(
        "--min-radius",
        type=float,
        default=25,
        help="回る中心がこれより近ければ回転とみなす (mm・既定 25)",
    )
    ap.add_argument(
        "--min-arm", type=int, default=5, help="これより小さいアームの動きは書かない (度・既定 5)"
    )
    ap.add_argument("--arm-speed", type=int, default=500, help="アームの速さ (deg/s・既定 500)")
    opt = ap.parse_args()

    if opt.name and opt.log:
        raise SystemExit("--name（いまから記録する）とログのパスは、どちらか 1 つにしてね")
    if opt.out and os.path.exists(
        os.path.join(ROOT, opt.out) if not os.path.isabs(opt.out) else opt.out
    ):
        raise SystemExit(f"{opt.out} はもうあります。別の名前にしてね（上書きはしない）")
    log = record(opt.name) if opt.name else (opt.log or newest_log())
    with open(log, encoding="utf-8", errors="replace") as f:
        text = f.read()
    wheel, axle, samples, has_header, lines = build(text, opt)
    log_rel = os.path.relpath(os.path.abspath(log), ROOT).replace(os.sep, "/")

    print()
    print(f"=== 手押しの記録 → コード（{log_rel}）===")
    if not has_header:
        print(
            f"! # teach: の行が無いので、タイヤ {DEFAULT_WHEEL}mm・間隔 {DEFAULT_AXLE}mm で計算しました"
        )
    end = samples[-1]
    print(
        f"記録: {end.t / 1000:.1f} 秒・{len(samples)} 行・タイヤ {wheel}mm・間隔 {axle}mm"
        f"・終点 前へ {round(end.x)}mm / 右へ {round(end.y)}mm / 向き {end.heading:+.1f}°"
    )
    for note in lift_warnings(samples, opt):
        print("! " + note)
    print()
    if not lines:
        print("（動きが見つかりませんでした。タイヤやアームを手で回しましたか？）")
        return
    width = max(len(code) for code, _ in lines)
    for code, note in lines:
        print(f"    {code.ljust(width)}  # {note}")
    print()

    x, y, h = simulate(lines)
    gap = math.hypot(end.x - x, end.y - y)
    print(
        f"確認: このコードの終点は、手で押した終点から {gap:.0f}mm・向き {end.heading - h:+.1f}° ずれ"
        "（すべりの無い計算上の値）"
    )

    if opt.out:
        path = opt.out if os.path.isabs(opt.out) else os.path.join(ROOT, opt.out)
        write_run_file(path, lines, log_rel)
        print(
            f"✓ 書き出しました: {os.path.relpath(path, ROOT)}（F5 で走らせる前に、置き方と動きを確かめてね）"
        )


if __name__ == "__main__":
    main()
