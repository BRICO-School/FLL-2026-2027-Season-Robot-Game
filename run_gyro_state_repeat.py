"""
【置き直さずに 5 周を何回もくり返し、状態 A/B が「いつ」決まるかを見る】（2026-09-19・計画 09 の実験 3）

実験 1（9/19・11 本）で分かったこと: 状態 A/B は 1 回の 5 周の中では変わらず、走行ごとに決まっている。
B の回は、同じジャイロの角度に対してモーターが約 1.5〜2% 多く回る
＝「ジャイロの向き ÷ エンコーダから計算した向き」の比率で、当て直しをしなくても A/B が見分けられる。

この道具は、1 回のプログラムの中で、機体にさわらずに 5 周を REPEATS 回くり返し、1 回ごとの比率を出す。
 ・1 回のプログラムの中で比率が A と B に分かれたら → プログラムの開始や置き方ではなく、回転のたびに決まる
 ・プログラムの中では全部同じで、プログラムごとに変わるなら → 開始時（ハブの準備・置き方）で決まる

やり方:
 1. 機体の左側面を定規に当てて置き、手を離して実行する
 2. 5 周 → 2 秒休み を REPEATS 回くり返す（約 1 分）。そのあいだ機体にさわらない
 3. 最後にライトが緑になったら、手で定規に当て直して手を離す（全部の合計のズレを読む）

ハブの設定は書きかえない。

【更新履歴】
- 2026-09-19: 連続旋回時のジャイロとエンコーダ比率を記録する検証スクリプトを追加した
"""

from pybricks.parameters import Axis, Color
from pybricks.tools import StopWatch, run_task, wait
from setup import initialize_robot

TURNS = 5
REPEATS = 6
DIRECTION = 1  # 1 = 右回り / -1 = 左回り
WHEEL_MM = 62.32  # setup.py の ROBOT_PROFILES と同じ（比率の計算だけに使う）
AXLE_MM = 114.48
# 加速・減速のところはタイヤのすべり方が違うので、比率は 1 周目の終わり〜4 周目の終わりで取る
MID_FROM_DEG = 360
MID_TO_DEG = 360 * (TURNS - 1)


async def run(hub, robot, left_wheel, right_wheel, left_lift, right_lift):
    while not hub.imu.ready():
        await wait(100)
    hub.imu.reset_heading(0)
    robot.reset()
    await wait(500)
    print("# imu.settings:", hub.imu.settings())
    print("# 前: tilt", hub.imu.tilt(), "/ 電池:", hub.battery.voltage(), "mV")
    drivebase = robot._robot  # 回転中も測るので、中の DriveBase を直接使う

    for i in range(REPEATS):
        h0 = hub.imu.heading()
        rz0 = hub.imu.rotation(Axis.Z)
        e0 = (left_wheel.angle() - right_wheel.angle()) / 2 * WHEEL_MM / AXLE_MM
        mid_from = None  # 1 周目の終わりの (ジャイロ, エンコーダ)
        mid_to = None  # 4 周目の終わりの (ジャイロ, エンコーダ)
        drivebase.turn(360 * TURNS * DIRECTION, wait=False)
        while not drivebase.done():
            h = abs(hub.imu.heading() - h0)
            e = abs((left_wheel.angle() - right_wheel.angle()) / 2 * WHEEL_MM / AXLE_MM - e0)
            if mid_from is None and h >= MID_FROM_DEG:
                mid_from = (h, e)
            if mid_to is None and h >= MID_TO_DEG:
                mid_to = (h, e)
            await wait(10)
        await wait(1000)
        h = abs(hub.imu.heading() - h0)
        e = abs((left_wheel.angle() - right_wheel.angle()) / 2 * WHEEL_MM / AXLE_MM - e0)
        rz = abs(hub.imu.rotation(Axis.Z) - rz0)
        mid = 0.0
        if mid_from is not None and mid_to is not None:
            mid = (mid_to[0] - mid_from[0]) / (mid_to[1] - mid_from[1])
        print(
            "R,",
            i + 1,
            ", ジャイロ",
            round(h, 2),
            ", rotZ",
            round(rz, 2),
            ", エンコーダ",
            round(e, 2),
            ", 比率(全体)",
            round(h / e, 4),
            ", 比率(2〜4 周目)",
            round(mid, 4),
            ", 電池",
            hub.battery.voltage(),
        )
        await wait(1000)

    h1 = hub.imu.heading()
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
    if abs(h2 - h1) < 0.3:
        print("# ！ 合わせ直しでほとんど動いていません。当て直しを忘れていたら、合計のズレは無効です")
    print("# 命令の合計:", 360 * TURNS * REPEATS * DIRECTION, "度 / 止まった時のジャイロ h1:", round(h1, 2), "度")
    print("# 定規に合わせ直した時のジャイロ h2:", round(h2, 2), "度")
    print("# 合計の本当のズレ（右回りで＋は回り足りない）:", round(h2 - h1, 2), "度（ジャイロの目盛りで）")
    print("# 1 周の読みの平均:", round(abs(h2) / (TURNS * REPEATS), 3), "度")
    print("# 電池:", hub.battery.voltage(), "mV")


def main(direction=None):
    global DIRECTION
    if direction is not None:
        DIRECTION = direction
    hub, robot, left_wheel, right_wheel, left_lift, right_lift = initialize_robot()
    run_task(run(hub, robot, left_wheel, right_wheel, left_lift, right_lift))


if __name__ == "__main__":
    main()
