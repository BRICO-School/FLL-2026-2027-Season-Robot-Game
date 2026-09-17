"""
run_setup_compare.py — 昨年の setup.py と今年の setup.py の性能を同じ機体・同じコースで比べる

【置き場所】本番リポジトリ FLL-2026-2027-Season-Robot-Game/ にコピーして、Pybricks Code から F5 で走らせる
【使い方】下の SETTINGS と COURSE を書きかえて 1 回ずつ走らせ、出力とものさし実測を比較表に書く

  SETTINGS = "new"      … 今年の setup.py の値そのまま（Step 8 で書きこんだもの）
  SETTINGS = "old"      … 寸法（wheel/axle）は今年、速度・加速度・PID だけ昨年の値 ← 優劣判定はこれで行う（公平な比較）
  SETTINGS = "old_full" … 昨年の setup.py を丸ごと（wheel 62 / axle 85 も昨年）← 参考。機体が違うので回転は合わない
  SETTINGS = "new_short"… 今年の値に、短い動き用の加速度（Step 6-2 の SHORT_*）を mission コースの各動きで上書き
                          ← new と mission の時間を比べ、短い動き用の設定を持つ価値があるかを決める

  COURSE = "straight"   … 直進 1000 mm → 3 秒待つ。ものさしで距離と向きのズレを測る
  COURSE = "turn"       … 90° 右回転 ×4（合計 360°）→ 3 秒待つ。スタートの向きに戻るか（マットの線で測る）
  COURSE = "square"     … 直進 1000 → 右 90° を 4 回（1 m 四方）。終点がスタートから何 mm ずれるか測る
  COURSE = "mission"    … ミッション模擬: 直進 300 → 右 90° を 4 回で 300 mm 四方を 2 周（直進 8・回転 8）。
                          短い移動の連続なので加速度の差が時間にいちばん出る。終点のズレと所要時間を見る

【2026-09-17 追記】
- 今年の setup.py は Robot.turn() が「回りすぎ」を打ち消す（TURN_OVERSHOOT_TABLE）。表は今年の加速度で測ったものなので、
  old / old_full では打ち消しを切って（compensate=False）昨年どおりの turn() にする。new は打ち消しも含めて「今年の一式」。
- 今年の PID は Pybricks の既定（setup.py は pid() を呼ばない）。old は昨年値を上書きする。
- 短い動き用の設定は Step 6-2 で「持たない」に決着したので new_short は走らせない（仕組みは残す）。
- 1 回ごとに書きかえなくて済むよう、cmp_<設定>_<コース>.py（2 行のラッパー）から main() を呼べる。
  例: python run_with_log.py cmp_new_straight.py --name "Pybricks Hub3" --no-trial
- 回転の 1 回ごとにジャイロの向きを表示する（打ち消し表が合っているかの目安）。

出力: 所要時間（秒）・ジャイロの向き（°）・エンコーダの距離（mm）。ものさし実測は人が測って表に書く。
昨年の値は old/setup_last_season_backup.README.md の抜き書きと同じ。

【更新履歴】
- 2026-09-17: 新旧の走行設定による性能を比較検証するスクリプトを新規作成した。
- 2026-09-17: 設定値の取得元を内部のDriveBaseに変更した。
"""

from pybricks.hubs import PrimeHub
from pybricks.parameters import Port, Axis, Direction, Color, Stop
from pybricks.pupdevices import Motor
from pybricks.robotics import DriveBase
from pybricks.tools import wait, multitask, run_task, StopWatch
from setup import initialize_robot, Robot

# ===== ここを書きかえる =====
SETTINGS = "new"        # "new" / "old" / "old_full" / "new_short"
COURSE = "straight"     # "straight" / "turn" / "square" / "mission"
# ============================

# 短い動き用の加速度（Step 6-2 で決めた setup_R.py の値をここに写す。new_short のときだけ使う）
SHORT_STRAIGHT_ACC = None   # mm/s²  例: 1100
SHORT_TURN_ACC = None       # deg/s² 例: 1200

# 昨年の本番値（old/setup_last_season_backup.py の抜き書き。ここは変えない）
OLD_WHEEL = 62
OLD_AXLE = 85
OLD_STRAIGHT = {"straight_speed": 400, "straight_acceleration": 500}
OLD_TURN = {"turn_rate": 240, "turn_acceleration": 850}
OLD_HEADING_PID = {"kp": 2000, "ki": 50, "kd": 100}
OLD_DISTANCE_PID = {"kp": 1000, "ki": 50, "kd": 10}


def apply_old_values(robot):
    """速度・加速度・PID を昨年の値にする（寸法はそのまま）"""
    robot.settings(**OLD_STRAIGHT, **OLD_TURN)
    robot.heading_control().pid(**OLD_HEADING_PID)
    robot.distance_control().pid(**OLD_DISTANCE_PID)


def build_old_full(hub, left_wheel, right_wheel):
    """昨年の setup.py を丸ごと再現する（寸法も昨年）"""
    db = DriveBase(left_wheel, right_wheel, wheel_diameter=OLD_WHEEL, axle_track=OLD_AXLE)
    db.settings(**OLD_STRAIGHT, **OLD_TURN)
    db.distance_control.pid(**OLD_DISTANCE_PID)
    db.heading_control.pid(**OLD_HEADING_PID)
    db.use_gyro(True)
    hub.imu.reset_heading(0)
    db.reset()
    return Robot(db)


async def run(hub, robot, left_wheel, right_wheel, left_lift, right_lift):
    if SETTINGS == "old":
        apply_old_values(robot)
    elif SETTINGS == "old_full":
        robot = build_old_full(hub, left_wheel, right_wheel)

    comp = SETTINGS in ("new", "new_short")   # 回りすぎの打ち消しは今年の設定のときだけ
    print("# 比較走行: SETTINGS =", SETTINGS, "/ COURSE =", COURSE, "/ 回転の打ち消し =", comp)
    print("# settings:", robot._robot.settings())  # Robot.settings() は値を返さないので中の DriveBase から読む
    print("# heading pid:", robot.heading_control().pid())
    print("# distance pid:", robot.distance_control().pid())

    # ジャイロが落ち着くまで待ってから向きを 0 にする
    while not hub.imu.ready():
        await wait(100)
    hub.imu.reset_heading(0)
    robot.reset()
    await wait(500)

    watch = StopWatch()
    watch.reset()

    if COURSE == "straight":
        await robot.straight(1000)          # 速度の引数は書かない（既定値の効きを見る）
    elif COURSE == "turn":
        for i in range(4):
            await robot.turn(90, compensate=comp)
            await wait(300)
            print("#  回転", i + 1, "回目のあと ジャイロ:", round(hub.imu.heading(), 2), "度")
    elif COURSE == "square":
        for _ in range(4):
            await robot.straight(1000)
            await wait(300)
            await robot.turn(90, compensate=comp)
            await wait(300)
    elif COURSE == "mission":
        short = SETTINGS == "new_short"
        if short and (SHORT_STRAIGHT_ACC is None or SHORT_TURN_ACC is None):
            print("! new_short には SHORT_STRAIGHT_ACC / SHORT_TURN_ACC を入れる")
        for _ in range(8):
            if short:
                await robot.straight(300, acceleration=SHORT_STRAIGHT_ACC)
            else:
                await robot.straight(300)
            await wait(200)
            if short:
                await robot.turn(90, acceleration=SHORT_TURN_ACC)
            else:
                await robot.turn(90, compensate=comp)
            await wait(200)
    else:
        print("! COURSE が不正:", COURSE)

    t = watch.time() / 1000
    await wait(3000)                        # 止まってから測れるように待つ
    robot.stop()

    print("# 所要時間:", round(t, 2), "秒")
    print("# ジャイロの向き:", round(hub.imu.heading(), 2), "度 （turn/square は 360、mission は 720 か 0 に近いほど良い）")
    print("# エンコーダの距離:", robot.distance(), "mm / 電池:", hub.battery.voltage(), "mV")
    print("# → ものさしで実測した距離・向きのズレ・終点のズレを比較表に書く")
    print("# 走行完了！")


def main(settings=None, course=None):
    """cmp_*.py から呼ぶ入口。引数があれば SETTINGS / COURSE を上書きする"""
    global SETTINGS, COURSE
    if settings is not None:
        SETTINGS = settings
    if course is not None:
        COURSE = course
    hub, robot, left_wheel, right_wheel, left_lift, right_lift = initialize_robot()
    run_task(run(hub, robot, left_wheel, right_wheel, left_lift, right_lift))


if __name__ == "__main__":
    main()
