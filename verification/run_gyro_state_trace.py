"""
【5 周の間、20ms ごとに記録して「いつ」ずれるかを見る】（2026-09-19・計画 09 の実験 1）

ジャイロの「2 つの状態」（1 周を約 365° と数える A・約 360° と数える B）が、
 ・走行の最初から最後まで同じ比率なのか（目盛りの問題）
 ・途中で段になって変わるのか（ファームの向き推定が切りかわる）
 ・A と B で振動（加速度のばらつき）が違うのか
を見る。やり方は run_gyro_motor_check.py と同じ（左側面を定規に当てて置く → 5 周 → 緑で当て直し）。

 1. 機体の左側面を、マットに固定した定規にぴったり当てて置き、手を離して実行する
 2. モーターで右回りに 5 周まわって止まる
 3. ライトが緑になったら、手でそっと回して同じ面を定規に当て直し、手を離す
 4. 青くなったあと、記録（T, で始まる行が約 450 行）が出る。出おわるまで 10 秒ほど待つ

記録は走行中には出さない（出すと 20ms の間隔がくずれる）。ハブの中にためて、当て直しのあとにまとめて出す。
PC 側で `uv run python scripts/gyro_trace_summary.py` を実行すると、CSV と 90° ごとの比率の表になる。
ハブの設定は書きかえない。

【更新履歴】
- 2026-09-19: 旋回中のジャイロや加速度の推移を記録するスクリプトを追加した
"""

from pybricks.parameters import Axis, Color
from pybricks.tools import StopWatch, run_task, wait
from setup import initialize_robot

TURNS = 5
SAMPLE_MS = 20  # 記録の間隔 (ms)
MAX_SAMPLES = 700  # ハブのメモリを守る上限（5 周は約 450 個）


async def run(hub, robot, left_wheel, right_wheel, left_lift, right_lift):
    while not hub.imu.ready():
        await wait(100)
    hub.imu.reset_heading(0)
    robot.reset()
    await wait(500)
    print("# imu.settings:", hub.imu.settings())
    print("# 前: tilt", hub.imu.tilt(), "/ 角速度", hub.imu.angular_velocity())
    rz0 = hub.imu.rotation(Axis.Z)
    left0 = left_wheel.angle()
    right0 = right_wheel.angle()

    # 小数はメモリを食うので、100 倍や 10 倍した整数でためる
    rows = []
    # Robot.turn() は終わるまで戻らないので、中の DriveBase を直接使って回転中も測る
    drivebase = robot._robot
    clock = StopWatch()
    drivebase.turn(360 * TURNS, wait=False)
    next_ms = 0
    while not drivebase.done() and len(rows) < MAX_SAMPLES:
        rows.append(
            (
                clock.time(),
                int(hub.imu.heading() * 100),  # ジャイロの向き (0.01 度)
                int((hub.imu.rotation(Axis.Z) - rz0) * 100),  # Z 軸の生の積算 (0.01 度)
                int(hub.imu.angular_velocity(Axis.Z) * 10),  # Z 軸の角速度 (0.1 deg/s)
                int(hub.imu.acceleration(Axis.X)),  # 加速度 X/Y/Z (mm/s²)
                int(hub.imu.acceleration(Axis.Y)),
                int(hub.imu.acceleration(Axis.Z)),
                left_wheel.angle() - left0,  # 左右モーターの角度 (度)
                right_wheel.angle() - right0,
                1 if hub.imu.stationary() else 0,  # ファームが「静止」と判定したか
            )
        )
        next_ms += SAMPLE_MS
        await wait(max(0, next_ms - clock.time()))
    while not drivebase.done():  # 上限に達したときも、回転は最後まで待つ
        await wait(SAMPLE_MS)
    await wait(1000)
    h1 = hub.imu.heading()
    rz1 = hub.imu.rotation(Axis.Z) - rz0
    left1 = left_wheel.angle() - left0
    right1 = right_wheel.angle() - right0
    robot.stop()  # モーターの力を抜く（手で回せるように）
    hub.light.on(Color.GREEN)
    print(
        "# ★いま★ ライトが緑になったら（ピーと鳴ったら）、手で定規にぴったり当て直して、手を離してね"
    )
    hub.speaker.volume(100)
    await hub.speaker.beep(frequency=500, duration=600)

    total = StopWatch()
    still = StopWatch()
    await wait(1500)  # 手を伸ばす時間
    still.reset()
    while True:
        if not hub.imu.stationary():
            still.reset()
        if total.time() > 8000 and still.time() > 3000:  # 少なくとも 8 秒は待つ
            break
        await wait(20)
    h2 = hub.imu.heading()
    hub.light.on(Color.BLUE)
    await hub.speaker.beep(frequency=1000, duration=200)

    print("# 列: T,ms,heading*100,rotZ*100,wz*10,ax,ay,az,left,right,stationary")
    for row in rows:
        print("T," + ",".join([str(v) for v in row]))
    print("# 記録の数:", len(rows), "/ 間隔:", SAMPLE_MS, "ms")
    print("# 止まった時 rotation Z:", round(rz1, 2), "/ モーター 左/右:", left1, right1, "度")
    if abs(h2 - h1) < 0.3:
        print("# ！ 合わせ直しでほとんど動いていません。当て直しを忘れていたら、この回は無効です")
    print("# 命令:", 360 * TURNS, "度 / 止まった時のジャイロ h1:", round(h1, 2), "度")
    print("# 定規に合わせ直した時のジャイロ h2:", round(h2, 2), "度")
    print("# 本当のズレ（＋は回り足りない）:", round(h2 - h1, 2), "度（ジャイロの目盛りで）")
    print(
        "# モーターで回ったときのジャイロの 1 周の読み:",
        round(h2 / TURNS, 3),
        "度（360 なら目盛りは合っている）",
    )
    print("# 電池:", hub.battery.voltage(), "mV")


def main():
    hub, robot, left_wheel, right_wheel, left_lift, right_lift = initialize_robot()
    run_task(run(hub, robot, left_wheel, right_wheel, left_lift, right_lift))


if __name__ == "__main__":
    main()
