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
- 2026-10-03: 手押し記録を基にM12等の攻略を行う走行ファイルを新規作成した。
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

    # ↓ 手押しの記録から起こした（docs/logs/teach_record/20261003_110652.log）

    # M12
    await robot.straight(554)  # 前進 627mm
    await robot.turn(-10, 200)  # 右 38°
    await right_lift.run_angle(1000, -360 * 2.35)  # 右アーム 6°
    await robot.turn(35, 125)  # 右 38°
    await wait(500)
    await right_lift.run_angle(240, 360 * 1)  # 右アームを逆に 6°
    await wait(500)

    # #M11へ
    await robot.turn(-104)  # 左 16°
    await robot.straight(153)  # 前進 153mm
    await left_lift.run_angle(500, 360 * 1.5)  # 右アーム 5°

    # #M06へ
    await robot.turn(14)  # 右 14°
    await robot.straight(313)  # 前進 313mm
    await robot.turn(61)  # 右 61°
    await robot.curve(-44, -15)  # カーブ 半径 44mm・右 15°（後退 11mm）
    await robot.curve(56, 32)  # カーブ 半径 56mm・右 44°（前進 43mm）
    await robot.straight(290, 175)  # 前進 115mm
    await robot.straight(-137)  # 後退 137mm

    # # M07へ
    # await robot.curve(38, 51)  # カーブ 半径 38mm・右 51°（前進 34mm）
    # await robot.straight(260)  # 前進 321mm
    # await right_lift.run_angle(1000, -360 * 1.8)  # 右アーム 6°
    # await robot.turn(-64)  # 左 64°
    # await robot.curve(48, -38)  # カーブ 半径 48mm・左 34°（後退 29mm）
    # await robot.straight(32)  # 前進 32mm
    # await right_lift.run_angle(1000, 360 * 1)  # 右アーム 6°
    # await wait(500)
    # await robot.straight(-65, 150)  # 後退 65mm
    # await right_lift.run_angle(1000, -360 * 1)  # 右アーム 6°

    # # 帰還
    # await robot.curve(-26, -36)  # カーブ 半径 26mm・右 36°（後退 16mm）
    # await robot.turn(43)  # 右 43°
    # await robot.curve(38, 84)  # カーブ 半径 38mm・右 84°（前進 56mm）
    # await robot.straight(600)  # カーブ 半径 3994mm・左 9°（前進 627mm）

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
