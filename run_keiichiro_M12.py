"""
【runファイルテンプレート】
このファイルは新しいrunを作成するためのテンプレートです。
コピーして使用してください。

【使い方】
1. このファイルをコピーして、新しい名前をつける（例: run2_M04_M05.py）
2. run() 関数内にロボットの動作を記述する
3. selector.py の programs リストに追加する

【更新履歴】
- 2026-05-20: robot.straight(500, speed=500) を追加

"""

from pybricks.hubs import PrimeHub
from pybricks.parameters import Port, Axis, Direction, Color, Stop
from pybricks.pupdevices import Motor
from pybricks.robotics import DriveBase
from pybricks.tools import wait, multitask, run_task, StopWatch
from setup import initialize_robot


async def run(hub, robot, left_wheel, right_wheel, left_lift, right_lift):

    await robot.straight(510, speed=500)
    await robot.straight(-100, speed=541)
    await robot.straight(100)
    await robot.straight(-150)

    """
    ロボットの動作を記述する関数

    【使用可能なメソッド】

    === 移動系（speedとtimeoutを指定可能） ===
    await robot.straight(400)                            # 400mm直進
    await robot.straight(200, speed=500)                 # 500mm/sで200mm直進
    await robot.straight(-300)                           # 300mm後退
    await robot.straight(500, timeout=3000)              # 3秒以内に500mm直進（タイムアウト）
    await robot.straight(200, speed=300, timeout=2000)   # 300mm/sで2秒以内に200mm直進

    await robot.turn(90)                                 # 90度右回転
    await robot.turn(-45)                                # 45度左回転
    await robot.turn(180, rate=300)                      # 300deg/sで180度回転
    await robot.turn(90, timeout=1500)                   # 1.5秒以内に90度回転

    await robot.curve(200, 90)                           # 半径200mmで90度カーブ
    await robot.curve(300, 45, speed=150)                # 150mm/sで半径300mm、45度カーブ
    await robot.curve(150, 60, timeout=2000)             # 2秒以内にカーブ

    === モーター操作（timeoutを指定可能） ===
    await left_lift.run_angle(300, 180)                  # 左アームを300deg/sで180度回転
    await right_lift.run_angle(500, -360)                # 右アームを逆方向に1回転
    await robot.run_motor(right_wheel, 200, 140, timeout=1500)  # 1.5秒以内に右車輪を回転

    === 待機 ===
    await wait(500)                                      # 0.5秒待機
    await wait(1000)                                     # 1秒待機

    === デフォルト速度設定（setup.pyで定義） ===
    - straight: 400mm/s, 加速度500mm/s²
    - turn: 240deg/s, 加速度850deg/s²
    - curve: 240mm/s, 加速度800mm/s²
    """

    #######################################
    # ここにロボットの動作を記述してください
    #######################################

    # ロボットを停止
    robot.stop()
    print("# 走行完了！")


# ===== 単体テスト用（このファイルを直接実行した場合） =====
if __name__ == "__main__":
    hub, robot, left_wheel, right_wheel, left_lift, right_lift = initialize_robot()
    run_task(run(hub, robot, left_wheel, right_wheel, left_lift, right_lift))
