from pybricks.hubs import PrimeHub
from pybricks.parameters import Port, Axis, Direction ,Color
from pybricks.pupdevices import Motor
from pybricks.robotics import DriveBase
from pybricks.tools import wait, multitask, run_task
from setup import initialize_robot

async def run(hub ,robot, left_wheel, right_wheel,left_lift,right_lift):
#######################################

   '''
   '''

   # ラン2だけ、他のランとは異なり低速で動くようにする
   # 直進速度: 800mm/s * 40% = 320mm/s
   # 回転速度: 200deg/s * 30% = 60deg/s
   robot.settings(straight_speed=320, turn_rate=60)

   # ここにロボットの動作を記述してください

   #M09
   await robot.curve(120, 110)   #半径120mmで90度カーブ M09に向けて方向転換

   await robot.curve(120, -64)   #半径120mmで-90度カーブ M09に向けて方向転換

   robot.settings(straight_speed=220)   #M009に向けて前進
   await robot.straight(200)

   await robot.straight(-192)   #M09の台を引っ張って後進

   await wait(200)  # 1秒待機

   await robot.curve(710, 10)  #M09に向けて前進

   await wait(150)  # 1秒待機

   # 右のタイヤだけを回して回転
   await right_wheel.run_angle(100, 170)   # 速度100で50度回転 M09の下の台を回転して上げる

   await wait(100)  # 1秒待機


   #M07
   await robot.straight(-210)  #後進でM09から離れる

   await robot.turn(45) #M07へ向けて方向転換

   await robot.straight(210) #M07に向けて前進

   await robot.turn(65) #M07に向けて方向転換

   await robot.straight(90) #M07に向けて前進

   await right_lift.run_angle(1000, -850)  # 速度200で360度回転 右リフトでM07の下の台を上げる

   await robot.straight(100)

   # await robot.straight(100)

   # 右のアームを上げる
   await right_lift.run_angle(800, 720)  # 速度200で360度回転

   # スタート位置に戻るバージョン
   #await robot.straight(-210)
   #await robot.turn(-55)
   #await robot.curve(-1000, 40)


   # 左側にいくバージョン
   robot.settings(straight_speed=400)
   await robot.straight(-550)
   await robot.turn(58)
   robot.settings(straight_speed=600)  # スピードを600mm/sに上げる

   await robot.straight(-800)
   await robot.turn(-22)
   await robot.straight(-650)
   '''
   await robot.curve(-230, -80)



   # await robot.straight(-300)


   '''
   

   # ロボットを明示的に停止
   robot.stop()
   print("# 走行完了！")


    # === サンプル動作コード（参考例）===
    # 以下は基本的なロボット動作の例です。必要に応じてコメントアウトを解除して使用してください
    
    # 【awaitについて】
    # await = 動作が完了するまで待機（順次実行）
    # awaitなし = 動作を開始してすぐ次の処理へ（並行実行）
    # 【実装時の注意点】
    # リフト操作：連続して同じリフトを使用する場合はwaitを使用し待ち時間を挟む。waitがないと同時に動いてしまい想定した挙動にならない。
    
    # 動作速度の設定: robot.settingsで直進・回転速度を調整
    #robot.settings(straight_speed=800, turn_rate=100)  # 直進200mm/s, 回転100deg/s
    
    # 直進移動: 300mm前進（非同期実行）
    #robot.straight(500)
    #await wait(500)
    #left_lift.run_angle(200, 360)
    
    ## リフト操作: 左リフトを速度200で360度回転（非同期実行）
    #await left_lift.run_angle(200, 360)
    #
    ## 回転動作: その場で90度右回転（非同期実行）
    #await robot.turn(90)
    #
    ## 動作中の速度変更例: より高速な設定に変更
    #robot.settings(straight_speed=400, turn_rate=200)  # 高速設定
    #
    ## リフト操作: 左リフトを速度200で360度回転（同期実行・awaitなし）
    #left_lift.run_angle(200, 360)
    #
    ## カーブ移動: 半径150mmで90度カーブ（非同期実行）
    #await robot.curve(150, 90)
    #
    ## 精密動作用の低速設定例
    #robot.settings(straight_speed=100, turn_rate=50)   # 低速・高精度設定
    #await robot.straight(50)  # 精密な50mm移動
    #pass  # 何も実行しない場合の構文エラー回避
    
##########################################


# グローバル終了フラグ
stop_logging = False

async def sensor_logger_task():
    """
    センサー値を定期的にターミナルに表示する非同期タスク。
    他のタスク（ロボットの移動）と並行して実行されます。
    """
    global stop_logging
    print("--- センサーログタスク開始 ---")
    while not stop_logging: # stop_loggingフラグがTrueになるまで継続
        heading = hub.imu.heading()
        left_deg = left_wheel.angle()
        right_deg = right_wheel.angle()
        dist = robot.distance()
        print(f"LOG: dist={dist:4.0f} mm  heading={heading:4.0f}°  L={left_deg:5.0f}°  R={right_deg:5.0f}°")
        await wait(200) # 100ミリ秒待機して、他のタスクに実行を譲る
    
    print("--- センサーログタスク終了 ---")

async def main():
    global stop_logging
    await run(hub ,robot, left_wheel, right_wheel,left_lift,right_lift)
    # main()が終了したらログタスクも終了させる
    stop_logging = True
    print("--- メインタスク完了、ログタスク終了中 ---")
    await wait(500)  # ログタスクが終了するまで少し待つ

if __name__=="__main__":
    # ラン2だけ、他のランとは異なり低速で動くようにする
    hub ,robot, left_wheel, right_wheel,left_lift,right_lift = initialize_robot(straight_speed_percent=40, turn_speed_percent=30, motor_power_percent=100)
    run_task(multitask(
        sensor_logger_task(), 
        main()
    ))