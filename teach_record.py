"""
【手押しティーチング: 手で押して動かしたルートを記録する】（2026-10-02）

ロボットを手で押して動かすと、左右のタイヤ・左右のアームの角度とジャイロの向きを記録して画面に出す。
記録（docs/logs/teach_record/ のログ）から、scripts/teach.py が run ファイルのコード
（robot.straight / robot.turn / robot.curve / アームの run_angle）を起こす。

【使い方】いちばん楽なのは scripts/teach.py から呼ぶ方法（記録 → コードまで 1 回で済む）
  uv run python scripts/teach.py --name "Pybricks Hub3"

 1. ロボットをスタート位置に置いて、手を離してから実行する
    （initialize_robot() が止まったまま 2 秒待つ。そのあいだはさわらない）
 2. ピーと鳴ってライトが緑になったら、手で押して動かす
    - 1 つの動き（まっすぐ・その場で回る・アームを回す）が終わるたびに手を止める。
      約 0.5 秒止まるとピッと鳴って、画面に「動き 1: …」が出る（区切れた合図）
    - 持ち上げない。タイヤが床の上で回らないと、進んだ距離が分からない
    - アームは手で回せば記録される
 3. 終わったら、ハブの真ん中のボタンで止める
 4. scripts/teach.py がログを読んでコードにする（このファイルだけで走らせたときは
    uv run python scripts/teach.py でいちばん新しいログを読む）

このファイルだけで走らせるとき:
  uv run python run_with_log.py teach_record.py --name "Pybricks Hub3" --no-trial

記録の形（1 行 = 1 回の読み取り。値が変わったときと、止まっていても 1 秒ごとに出す）:
  P,ms,左タイヤ(度),右タイヤ(度),向き(0.1 度・時計回りが＋),左アーム(度),右アーム(度)
走行中のように間隔をそろえる必要はないので、ためずにその場で出す（途中で止めても記録が残る）。
ハブの設定は書きかえない。

【更新履歴】
- 2026-10-02: 手で押して動かしたルートを記録するプログラムを新規作成した
"""

from pybricks.parameters import Color
from pybricks.tools import StopWatch, run_task, wait

import setup
from setup import initialize_robot

SAMPLE_MS = 40  # 読み取りの間隔 (ms)
HEARTBEAT_MS = 1000  # 止まっていても、この間隔で 1 行出す（止まっていた時間を PC 側で分かるように）
PAUSE_MS = 500  # これだけ止まったら「1 つの動きのおわり」としてピッと鳴らす（scripts/teach.py の --pause と同じ値）
HEADING_STEP = 5  # 向き (0.1 度) がこれだけ変わったら、タイヤが止まっていても 1 行出す


async def run(hub, robot, left_wheel, right_wheel, left_lift, right_lift):
    robot.stop()  # タイヤの力を抜く（手で押せるように）
    left_lift.stop()
    right_lift.stop()

    wheel = setup._active_profile["wheel"]  # この機体の校正表の値（PC 側で mm に直すのに使う）
    axle = setup._active_profile["axle"]
    print("# teach: wheel=" + str(wheel) + " axle=" + str(axle) + " hub=" + hub.system.name())
    print("# 列: P,ms,左タイヤ(度),右タイヤ(度),向き(0.1度),左アーム(度),右アーム(度)")
    hub.light.on(Color.GREEN)
    await hub.speaker.beep(frequency=1000, duration=300)
    print("● 記録スタート: 手で押して動かしてね。1 つの動きごとに手を止める（ピッと鳴る）")
    print("● 終わったら、ハブの真ん中のボタンで止める")

    mm_per_deg = wheel * 3.14159 / 360  # タイヤ 1 度で進む距離 (mm)
    clock = StopWatch()
    shown = None  # 最後に出した行の値
    shown_ms = 0
    prev = None  # 1 回前の読み取り
    moving_since = None  # 動きはじめの値（画面の「動き N」用）
    still_ms = 0  # 最後に動いた時刻
    count = 0
    while True:
        now = clock.time()
        row = (
            left_wheel.angle(),
            right_wheel.angle(),
            int(hub.imu.heading() * 10),
            left_lift.angle(),
            right_lift.angle(),
        )

        if (
            shown is None
            or row[0] != shown[0]
            or row[1] != shown[1]
            or row[3] != shown[3]
            or row[4] != shown[4]
            or abs(row[2] - shown[2]) >= HEADING_STEP
            or now - shown_ms >= HEARTBEAT_MS
        ):
            print("P," + str(now) + "," + ",".join([str(v) for v in row]))
            shown = row
            shown_ms = now

        # 1 つの動きのおわりを知らせる（区切りの目安。本当の区切りは scripts/teach.py が決め直す）
        if prev is not None:
            moved = row[0] != prev[0] or row[1] != prev[1] or row[3] != prev[3] or row[4] != prev[4]
            if moved:
                if moving_since is None:
                    moving_since = prev
                still_ms = now
            elif moving_since is not None and now - still_ms >= PAUSE_MS:
                count += 1
                start = moving_since
                moving_since = None
                distance = ((row[0] - start[0]) + (row[1] - start[1])) / 2 * mm_per_deg
                print(
                    "● 動き",
                    count,
                    ": 進んだ",
                    round(distance),
                    "mm / 向き",
                    (row[2] - start[2]) / 10,
                    "° / 左アーム",
                    row[3] - start[3],
                    "° / 右アーム",
                    row[4] - start[4],
                    "°",
                )
                hub.light.on(Color.CYAN)
                await hub.speaker.beep(frequency=1500, duration=60)
                hub.light.on(Color.GREEN)
        prev = row
        await wait(SAMPLE_MS)


def main():
    hub, robot, left_wheel, right_wheel, left_lift, right_lift = initialize_robot()
    run_task(run(hub, robot, left_wheel, right_wheel, left_lift, right_lift))


if __name__ == "__main__":
    main()
