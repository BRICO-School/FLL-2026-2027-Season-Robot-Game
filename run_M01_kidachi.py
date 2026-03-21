"""
【M01 kidachi】
前進 → 後進 → 左アームを下げる動作を行うプログラム
"""

from pybricks.hubs import PrimeHub
from pybricks.parameters import Port, Axis, Direction, Color, Stop
from pybricks.pupdevices import Motor
from pybricks.robotics import DriveBase
from pybricks.tools import wait, multitask, run_task, StopWatch
from setup import initialize_robot


async def run(hub, robot, left_wheel, right_wheel, left_lift, right_lift):

    # 200mm 前進する
    await robot.straight(200)

    # 0.5秒待機して動作を安定させる
    await wait(500)

    # 300mm 後進する
    await robot.straight(-300)

    # 0.5秒待機して動作を安定させる
    await wait(500)

    # 左アームを下げる（300deg/sで450度回転）
    await left_lift.run_angle(300, 450)

    # ロボットを停止
    robot.stop()
    print("# 走行完了！")


# ===== 単体テスト用（このファイルを直接実行した場合） =====
if __name__ == "__main__":
    hub, robot, left_wheel, right_wheel, left_lift, right_lift = initialize_robot()
    run_task(run(hub, robot, left_wheel, right_wheel, left_lift, right_lift))
