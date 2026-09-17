"""
【ジャイロの「1 周」が本当に 360° かを確かめる】（Step 8 の追加確認・2026-09-17）

その場で 5 周（1800°）回って止まる。ジャイロは「1800° 回った」と思っている。
止まった機体が、スタートの向き（マットの線）から実際に何度ずれているかを見る。

  ぴったり戻る      … ジャイロの 1 周 ＝ 本当の 1 周。問題なし
  手前で止まる（回り足りない）/ 行き過ぎる … ジャイロの目盛りがずれている。
      ずれ ÷ 5 が 1 周あたりのずれ。hub.imu.settings(heading_correction=…) で直せる

測り方: スタートで機体の横をマットの線（か定規）に沿わせる。止まったあと、
        機体の前の端と後ろの端が線から何 mm 離れたかを測る（前後の長さも測っておく）。

【更新履歴】
- 2026-09-17: ジャイロの旋回角度のずれを確認するため５周旋回するスクリプトを追加した。
- 2026-09-17: 連続旋回に加えて90度ずつ停止しながら旋回するモードを追加した
- 2026-09-17: 旋回時の角度補正の有無を設定や引数で変更可能にした。
"""

from pybricks.tools import run_task, wait
from setup import initialize_robot

TURNS = 5  # 何周まわるか
CORRECT = False  # True なら Robot.turn() の「回り足りなさの補正」を入れて回る
MODE = "spin"  # "spin" = 止まらずに TURNS 周 / "steps" = 90° ずつ止まりながら TURNS 周（止まる回数 = TURNS×4）


async def run(hub, robot, left_wheel, right_wheel, left_lift, right_lift):
    while not hub.imu.ready():
        await wait(100)
    hub.imu.reset_heading(0)
    robot.reset()
    await wait(500)
    if MODE == "spin":
        await robot.turn(360 * TURNS, correct=CORRECT)
    else:
        for _ in range(TURNS * 4):
            await robot.turn(90, correct=CORRECT)
            await wait(300)
    await wait(1000)
    print("# MODE:", MODE, "/ 補正:", CORRECT, "/ 命令:", 360 * TURNS, "度 / ジャイロの向き:", round(hub.imu.heading(), 2), "度")
    print("# imu.settings:", hub.imu.settings())
    print("# → 機体がスタートの向きから実際に何度（前と後ろで何 mm）ずれているかを測る")
    await wait(3000)
    robot.stop()


def main(mode=None, correct=None):
    global MODE, CORRECT
    if correct is not None:
        CORRECT = correct
    if mode is not None:
        MODE = mode
    hub, robot, left_wheel, right_wheel, left_lift, right_lift = initialize_robot()
    run_task(run(hub, robot, left_wheel, right_wheel, left_lift, right_lift))


if __name__ == "__main__":
    main()
