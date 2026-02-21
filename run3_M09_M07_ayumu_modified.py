from pybricks.hubs import PrimeHub
from pybricks.parameters import Port, Axis, Direction, Color, Stop
from pybricks.pupdevices import Motor
from pybricks.robotics import DriveBase
from pybricks.tools import wait, multitask, run_task, StopWatch
from setup import initialize_robot


async def run(hub, robot, left_wheel, right_wheel, left_lift, right_lift):
    # ラン2だけ、他のランとは異なり低速で動くようにする
    # 直進速度: 800mm/s * 40% = 320mm/s
    # 回転速度: 200deg/s * 30% = 60deg/s
    robot.settings(straight_speed=320, turn_rate=60)

    # M09
    await robot.curve(120, 110)  # 半径120mmで110度カーブして方向転換
    await robot.curve(120, -64)  # 半径120mmで-64度カーブして方向転換

    robot.settings(straight_speed=220)  # M09に向けて前進
    await robot.straight(200)

    await robot.straight(-192)  # M09の台を引っ張って後進

    await wait(200)  # 0.2秒待機

    await robot.curve(710, 10)  # M09に向けて前進

    await wait(150)  # 0.15秒待機

    # 右のタイヤだけを回して回転
    await right_wheel.run_angle(100, 170)  # M09の下の台を回転して上げる

    await wait(100)  # 0.1秒待機

    # M07
    await robot.straight(-210)  # 後進でM09から離れる

    await robot.turn(45)  # M07へ向けて方向転換
    await robot.straight(210)  # M07に向けて前進
    await robot.turn(65)  # M07に向けて方向転換
    await robot.straight(90)  # M07に向けて前進

    await right_lift.run_angle(1000, -850)  # 右リフトでM07の下の台を上げる

    await robot.straight(100)

    # 右のアームを上げる
    await right_lift.run_angle(800, 720)

    # 左側にいくバージョン
    robot.settings(straight_speed=400)
    await robot.straight(-550)
    await robot.turn(58)
    robot.settings(straight_speed=600)  # スピードを600mm/sに上げる

    await robot.straight(-800)
    await robot.turn(-22)
    await robot.straight(-650)

    # ロボットを明示的に停止
    robot.stop()
    print("# 走行完了！")


# グローバル終了フラグ
stop_logging = False


async def sensor_logger_task():
    """
    センサー値を定期的にターミナルに表示する非同期タスク。
    他のタスク（ロボットの移動）と並行して実行されます。
    """

    global stop_logging
    print("--- センサーログタスク開始 ---")

    while not stop_logging:  # stop_loggingフラグがTrueになるまで継続
        heading = hub.imu.heading()
        left_deg = left_wheel.angle()
        right_deg = right_wheel.angle()
        dist = robot.distance()
        print(
            f"LOG: dist={dist:4.0f} mm  heading={heading:4.0f}°  L={left_deg:5.0f}°  R={right_deg:5.0f}°"
        )
        await wait(200)  # 0.2秒待機して、他のタスクに実行を譲る

    print("--- センサーログタスク終了 ---")


async def main():
    global stop_logging
    await run(hub, robot, left_wheel, right_wheel, left_lift, right_lift)
    # main()が終了したらログタスクも終了させる
    stop_logging = True
    print("--- メインタスク完了、ログタスク終了中 ---")
    await wait(500)  # ログタスクが終了するまで少し待つ


if __name__ == "__main__":
    hub, robot, left_wheel, right_wheel, left_lift, right_lift = initialize_robot()
    run_task(multitask(sensor_logger_task(), main()))
