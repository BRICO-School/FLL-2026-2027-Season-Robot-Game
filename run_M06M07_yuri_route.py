"""
【runファイルテンプレート】
このファイルは新しいrunを作成するためのテンプレートです。
コピーして使用してください。

【使い方】
1. このファイルをコピーして、新しい名前をつける（例: run_M04_kanna.py。run_ で始めると変更の記録が自動で付く）
2. run() 関数内にロボットの動作を記述する
3. selector.py の programs リストに追加する

【更新履歴】
- 2026-05-20: robot.straight(500, speed=500) を追加
- 2026-09-17: 直進と旋回のデフォルト速度および加速度の記載を更新した
- 2026-09-17: 旋回設定のコメントから回りすぎに関する補足を削除した。
- 2026-09-18: 単体テスト用に昨年の走行設定で検証する方法のコメントを追加した
- 2026-09-19: ロボット初期化時の静止待機と実行時の注意コメントを追加した
- 2026-09-19: 命名ルールの説明追加とサンプル直進処理の配置位置を修正した
"""

from pybricks.hubs import PrimeHub
from pybricks.parameters import Port, Axis, Direction, Color, Stop
from pybricks.pupdevices import Motor
from pybricks.robotics import DriveBase
from pybricks.tools import wait, multitask, run_task, StopWatch
from setup import initialize_robot


async def run(hub, robot, left_wheel, right_wheel, left_lift, right_lift):
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
    - straight: 550mm/s, 加速度800mm/s²
    - turn: 250deg/s, 加速度313deg/s²
    - curve: 240mm/s, 加速度800mm/s²
    """

    #######################################
    # ここにロボットの動作を記述してください
    #######################################

    # ↓ 手押しの記録から起こした（docs/logs/teach_record/20261020_145310.log）
    await robot.turn(-3)  # 向きを合わせる 左 3°
    await robot.straight(207)  # 前進 207mm
    await robot.turn(3)  # 向きを合わせる 右 3°
    await robot.curve(-42, 55)  # カーブ 半径 42mm・左 55°（前進 40mm）
    await robot.turn(-43)  # 左 43°
    await robot.turn(3)  # 向きを合わせる 右 3°
    await robot.straight(433)  # 前進 433mm
    await robot.curve(42, 92)  # カーブ 半径 42mm・右 92°（前進 67mm）
    await robot.turn(5)  # 向きを合わせる 右 5°
    await robot.straight(240)  # 前進 240mm
    await robot.curve(39, 38)  # カーブ 半径 39mm・右 38°（前進 26mm）
    await robot.curve(-297, 21)  # カーブ 半径 297mm・左 21°（前進 109mm）
    await robot.turn(4)  # 向きを合わせる 右 4°
    await robot.straight(114)  # 前進 114mm
    await robot.turn(23)  # 右 23°
    await robot.straight(142)  # 前進 142mm
    await robot.straight(-65)  # 後退 65mm
    await robot.curve(47, 33)  # カーブ 半径 47mm・右 33°（前進 27mm）
    await robot.curve(-48, -13)  # カーブ 半径 48mm・右 13°（後退 11mm）
    await robot.turn(6)  # 向きを合わせる 右 6°
    await robot.straight(234)  # 前進 234mm
    await robot.turn(-89)  # 左 89°
    await robot.curve(50, -15)  # カーブ 半径 50mm・左 15°（後退 13mm）
    await robot.turn(4)  # 向きを合わせる 右 4°
    await robot.straight(-75)  # 後退 75mm
    await robot.turn(5)  # 向きを合わせる 右 5°
    await robot.straight(51)  # 前進 51mm
    await robot.turn(-10)  # 左 10°
    await robot.straight(-61)  # 後退 61mm
    await robot.straight(73)  # 前進 73mm
    await robot.turn(3)  # 向きを合わせる 右 3°
    await robot.curve(-46, -16)  # カーブ 半径 46mm・右 16°（後退 13mm）
    await robot.curve(409, -22)  # カーブ 半径 409mm・左 22°（後退 157mm）
    await robot.turn(-3)  # 向きを合わせる 左 3°
    await robot.straight(-241)  # 後退 241mm
    await robot.turn(-4)  # 向きを合わせる 左 4°
    await robot.curve(-983, -17)  # カーブ 半径 983mm・右 17°（後退 292mm）

    # ロボットを停止
    robot.stop()
    print("# 走行完了！")


# ===== 単体テスト用（このファイルを直接実行した場合） =====
if __name__ == "__main__":
    # 昨年の速度・加速度・PID で走らせて成功率を比べるときは initialize_robot(drive_settings="old")（2026-09-18・setup.py の DRIVE_SETTINGS）
    # initialize_robot() は、機体が止まったまま 2 秒待ってから進む（2026-09-19・ジャイロは始めてすぐの回転だけ約 1.4% 多く数えるため）。
    # 機体を置いて手を離してから実行する。
    hub, robot, left_wheel, right_wheel, left_lift, right_lift = initialize_robot()
    run_task(run(hub, robot, left_wheel, right_wheel, left_lift, right_lift))
