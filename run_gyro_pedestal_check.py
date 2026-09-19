"""
【台の上で空転: 機体が回らないのに、ジャイロが動くか】（2026-09-19・計画 09 の実験 2）

ジャイロの「2 つの状態」（1 周を約 365° と数える A・約 360° と数える B）の原因を切り分ける。
機体を台（本やブロック）に載せて **タイヤを浮かせ**、5 周ぶんの回転と同じ命令でモーターだけ回す。
機体は回らないので、ジャイロの向きは 0 のままのはず。
 ・動いたら → モーターの振動か電流がジャイロに乗っている（床は関係ない）
 ・動く回と動かない回に分かれたら → A/B の切りかわりを床なしで再現できた
 ・動かなければ → A/B は機体が本当に回っているときだけ起きる

やり方:
 1. 機体を台に載せ、左右のタイヤがどこにも触れていないことを確かめる。台ごと動かないようにする
 2. 手を離して実行する。モーターが約 9 秒回って止まる。そのあいだ機体にさわらない
 3. 青くなったら終わり（当て直しは無い）

ジャイロを使う設定のままだと「向きが目標に届かない」のでモーターが止まらない。
この道具の中だけ use_gyro(False)（エンコーダで 5 周ぶん）にして回す。速度・加速度は setup.py のまま。
ハブの設定は書きかえない。

【更新履歴】
- 2026-09-19: 台上で車輪を空転させ振動によるジャイロへの影響を検証する処理を追加した
- 2026-09-19: タイヤ接地時の回転検知による中止処理を追加し変数の初期化を修正した
"""

from pybricks.parameters import Axis, Color
from pybricks.tools import StopWatch, run_task, wait
from setup import initialize_robot

TURNS = 5
SAMPLE_MS = 20  # 静止判定と角速度を見る間隔 (ms)
FLOOR_LIMIT_DEG = 45  # ジャイロの向きがこれより動いたら「タイヤが浮いていない」とみなして止める (度)。振動だけなら 5 周ぶんでも約 25 度まで


async def run(hub, robot, left_wheel, right_wheel, left_lift, right_lift):
    while not hub.imu.ready():
        await wait(100)
    robot.use_gyro(False)  # 台の上では向きが変わらないので、エンコーダで回す
    hub.imu.reset_heading(0)
    robot.reset()
    await wait(500)
    print("# imu.settings:", hub.imu.settings())
    print("# 前: tilt", hub.imu.tilt(), "/ 角速度", hub.imu.angular_velocity())
    rx0 = hub.imu.rotation(Axis.X)
    ry0 = hub.imu.rotation(Axis.Y)
    rz0 = hub.imu.rotation(Axis.Z)
    left0 = left_wheel.angle()
    right0 = right_wheel.angle()

    # Robot.turn() は終わるまで戻らないので、中の DriveBase を直接使って回転中も測る
    drivebase = robot._robot
    drivebase.turn(360 * TURNS, wait=False)
    clock = StopWatch()
    samples = 0
    stationary_samples = 0  # 回転中に「静止」と判定された回数（ファームの向き推定の手がかり）
    # 0 ではなく 0.0 で始める（MicroPython は整数の round(x, 1) ができず NotImplementedError になる）
    wz_min = 0.0  # Z 軸の角速度の最小・最大 (deg/s)。機体は回らないので、振れ幅＝振動の大きさ
    wz_max = 0.0
    h_min = 0.0  # 回転中のジャイロの向きの最小・最大 (度)
    h_max = 0.0
    while not drivebase.done():
        samples += 1
        if hub.imu.stationary():
            stationary_samples += 1
        wz = hub.imu.angular_velocity(Axis.Z)
        wz_min = min(wz_min, wz)
        wz_max = max(wz_max, wz)
        h = hub.imu.heading()
        h_min = min(h_min, h)
        h_max = max(h_max, h)
        if abs(h) > FLOOR_LIMIT_DEG:
            # 機体が本当に回っている＝タイヤが床か台に触れている。この実験にならないので止める
            drivebase.stop()
            robot.use_gyro(True)
            hub.light.on(Color.RED)
            print("# ！中止！ 機体が", round(h, 1), "度回りました。タイヤが床や台に触れています。")
            print("# タイヤを完全に浮かせてから、もう一度実行してください（この回は無効）")
            return
        await wait(SAMPLE_MS)
    run_ms = clock.time()
    h_stop = hub.imu.heading()  # モーターが止まった瞬間
    await wait(1000)
    h_end = hub.imu.heading()  # 1 秒たって落ち着いたあと
    robot.stop()
    robot.use_gyro(True)

    print("# 後: tilt", hub.imu.tilt(), "/ 角速度", hub.imu.angular_velocity())
    print(
        "# 軸ごとの回転 X/Y/Z:",
        round(hub.imu.rotation(Axis.X) - rx0, 2),
        round(hub.imu.rotation(Axis.Y) - ry0, 2),
        round(hub.imu.rotation(Axis.Z) - rz0, 2),
    )
    print(
        "# モーターの回転 左/右:",
        left_wheel.angle() - left0,
        right_wheel.angle() - right0,
        "度 / 回した時間:",
        run_ms,
        "ms",
    )
    print(
        "# 回転中: 静止と判定",
        stationary_samples,
        "/",
        samples,
        "回 / Z 角速度の範囲:",
        round(wz_min, 1),
        "〜",
        round(wz_max, 1),
        "deg/s / 向きの範囲:",
        round(h_min, 2),
        "〜",
        round(h_max, 2),
        "度",
    )
    print("# 台の上の空転: 命令", 360 * TURNS, "度ぶん / 止まった瞬間のジャイロ:", round(h_stop, 2), "度")
    print(
        "# ★結果★ 機体は回っていないのに動いたジャイロの向き:",
        round(h_end, 2),
        "度（0 なら振動・電流の影響なし。床の上の状態 A は 5 周で約 +25 度ぶん多く数える）",
    )
    print("# 電池:", hub.battery.voltage(), "mV")
    hub.light.on(Color.BLUE)
    hub.speaker.volume(100)
    await hub.speaker.beep(frequency=1000, duration=200)


def main():
    hub, robot, left_wheel, right_wheel, left_lift, right_lift = initialize_robot()
    run_task(run(hub, robot, left_wheel, right_wheel, left_lift, right_lift))


if __name__ == "__main__":
    main()
