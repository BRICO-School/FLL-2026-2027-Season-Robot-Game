"""
【M10 kidachi】
前進 → アームを下げる → 待機 → アームを上げる → 後退
（右リフト未接続時は左リフトで代用。右モータを Port.A に接続すれば右のみ使用）
"""

from pybricks.hubs import PrimeHub
from pybricks.parameters import Port, Axis, Direction, Color, Stop
from pybricks.pupdevices import Motor
from pybricks.robotics import DriveBase
from pybricks.tools import wait, multitask, run_task, StopWatch
from setup import NullMotor, initialize_robot


# 直進で壁などに当たり目標距離に届かないとき、await が長く止まるのを防ぐ（setup.Robot.straight の timeout）
STRAIGHT_TIMEOUT_MS = 2000


async def run(hub, robot, left_wheel, right_wheel, left_lift, right_lift):

    # 100mm 前進する（到達不能時は最大 STRAIGHT_TIMEOUT_MS で打ち切り、次の処理へ進む）
    await robot.straight(100, timeout=STRAIGHT_TIMEOUT_MS)

    # Port.A 未接続のとき right_lift は NullMotor になり動かない（docs/logs/run_M01_kidachi 参照）。
    # kidachi 機体は M01 と同様 Port.E の左リフトでアーム操作する。
    arm_speed = 500
    arm_angle = 1000
    if isinstance(right_lift, NullMotor):
        await left_lift.run_angle(arm_speed, arm_angle)  # 左アームを下げる（M01 と同じ向き）
        await wait(500)
        await left_lift.run_angle(arm_speed, -arm_angle)  # 戻す
    else:
        await right_lift.run_angle(arm_speed, -arm_angle)  # 右アームを下げる
        await wait(500)
        await right_lift.run_angle(arm_speed, arm_angle)  # 戻す

    # 100mm 後退する
    await robot.straight(-100, timeout=STRAIGHT_TIMEOUT_MS)

    robot.stop()
    print("# 走行完了！")


# ===== 単体テスト用（このファイルを直接実行した場合） =====
if __name__ == "__main__":
    hub, robot, left_wheel, right_wheel, left_lift, right_lift = initialize_robot()
    run_task(run(hub, robot, left_wheel, right_wheel, left_lift, right_lift))
