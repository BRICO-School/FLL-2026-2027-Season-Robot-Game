"""
【M04 kidachi】
少し前進 → 左アームを少し挙げる → 後退 → 左アームをもう少し挙げる
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

    arm_speed = 500
    arm_angle_step = 100  # 1回あたりの挙げ量
    drive_mm = 100

    await robot.straight(drive_mm, timeout=STRAIGHT_TIMEOUT_MS)

    await left_lift.run_angle(arm_speed, -arm_angle_step)  # 左アームを少し挙げる

    await robot.straight(-drive_mm, timeout=STRAIGHT_TIMEOUT_MS)

    await left_lift.run_angle(arm_speed, -arm_angle_step)  # 左アームをもう少し挙げる

    robot.stop()
    print("# 走行完了！")


# ===== 単体テスト用（このファイルを直接実行した場合） =====
if __name__ == "__main__":
    hub, robot, left_wheel, right_wheel, left_lift, right_lift = initialize_robot()
    run_task(run(hub, robot, left_wheel, right_wheel, left_lift, right_lift))
