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
- 2026-10-02: 手押し記録をもとにM04の走行プログラムを新規作成した
- 2026-10-03: 手押し記録をもとにM04とM05の走行とアーム動作を実装した。
- 2026-10-05: 直進速度や旋回角度を調整し後退と右アームの動作を追加した
- 2026-10-05: 直進速度や旋回角度を調整し後退と右アームの動作を追加した
- 2026-10-08: M04とM05の動作を調整し帰還動作を追加した

- 2026-10-08: 帰還時の後退距離とカーブ角度を調整した
- 2026-10-11: 種子採取処理の追加とミッション動作や帰還経路の調整を行った
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

    # ↓ 手押しの記録から起こした（docs/logs/teach_record/20261002_205805.log）

    # M04
    await robot.curve(1365, 27)  # カーブ 半径 1365mm・右 26°（前進 619mm）
    await robot.curve(-49, 54)  # カーブ 半径 49mm・左 65°（前進 55mm）
    await robot.turn(-7)  # 向きを合わせる 左 3°
    await robot.straight(190, 150)  # 前進 151mm

    await left_lift.run_angle(500, -360 * 2)  # 左アームを300deg/sで180度回転

    # M05
    # await robot.straight(-50, 200)  # 前進 151mm
    await robot.straight(-23)
    await right_lift.run_angle(500, -750)  # 右アームを逆に 6°
    await robot.turn(31)  # 右 32°

    await robot.straight(-30, 100)
    await wait(500)

    await right_lift.run_angle(500, 360)  # 右アームを逆に 6°
    await wait(500)
    await robot.straight(120, 200)
    await wait(500)
    await multitask(
        robot.straight(-40, 200),
        right_lift.run_angle(500, -100),
    )
    await wait(500)
    await right_lift.run_angle(1000, 360)  # 右アームを逆に 6°
    await robot.straight(50)
    await wait(500)
    await robot.turn(-30)
    await wait(500)
    await robot.turn(30)
    await wait(500)

    # 種子を採る
    await robot.straight(-70)  # 後退 42mm
    await right_lift.run_angle(500, -600)  # 右アームを逆に 6°
    await wait(500)
    await robot.turn(17, 100)  # 右 13°
    await wait(500)
    await robot.straight(13, 200)
    await right_lift.run_angle(100, 190)  # 右アームを逆に 6°
    await wait(500)
    await robot.turn(-20, 80)  # 向きを合わせる 左 12°

    # 帰還
    await robot.straight(-300)  # 後退 178mm
    await robot.curve(-330, -90)  # カーブ 半径 229mm・右 42°（後退 168mm）
    # await robot.curve(-200, -19)  # カーブ 半径 68mm・右 19°（後退 23mm）

    # # 帰還
    # await robot.straight(-380)  # 後退 452mm
    # await robot.curve(-430, -63)  # カーブ 半径 430mm・右 58°（後退 435mm）

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
