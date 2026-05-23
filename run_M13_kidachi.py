"""
【M13 kidachi】
前進 → 左アームを勢いよく挙げる
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

    arm_speed = 1050  # Technic Angular Motor の最大角速度 (deg/s)
    arm_angle = 800  # M01 kidachi の下げ量と同程度（挙げる向きは符号反転）

    await robot.straight(100, timeout=STRAIGHT_TIMEOUT_MS)

    await left_lift.run_angle(arm_speed, -arm_angle)  # 左アームを挙げ

    await robot.straight(-100, timeout=STRAIGHT_TIMEOUT_MS)

    robot.stop()
    print("# 走行完了！")


# ===== 単体テスト用（このファイルを直接実行した場合） =====
if __name__ == "__main__":
    hub, robot, left_wheel, right_wheel, left_lift, right_lift = initialize_robot()
    run_task(run(hub, robot, left_wheel, right_wheel, left_lift, right_lift))
