from pybricks.hubs import PrimeHub
from pybricks.parameters import Port, Axis, Direction ,Color
from pybricks.pupdevices import Motor
from pybricks.robotics import DriveBase
from pybricks.tools import wait, multitask, run_task
from setup import initialize_robot

async def turn_time(left_wheel, right_wheel, speed, time_ms, direction="right"):
    """
    時間指定でロボットを回転させる関数
    
    Args:
        left_wheel: 左モーター
        right_wheel: 右モーター  
        speed: 回転速度
        time_ms: 回転時間（ミリ秒）
        direction: 回転方向 ("right" または "left")
    """
    if direction == "right":
        left_wheel.run(speed)    # 左モーター正回転
        right_wheel.run(-speed)  # 右モーター逆回転
    else:  # left
        left_wheel.run(-speed)   # 左モーター逆回転
        right_wheel.run(speed)   # 右モーター正回転
    
    await wait(time_ms)
    left_wheel.stop()
    right_wheel.stop()

async def run(hub ,robot, left_wheel, right_wheel,left_lift,right_lift):
#######################################
    # ここにロボットの動作を記述してください
    # === サンプル動作コード（参考例）===
    # 以下は基本的なロボット動作の例です。必要に応じてコメントアウトを解除して使用してください
    
    # 【awaitについて】
    # await = 動作が完了するまで待機（順次実行）
    # awaitなし = 動作を開始してすぐ次の処理へ（並行実行）
    
    # 動作速度の設定: robot.settingsで直進・回転速度を調整
    robot.settings(straight_speed=400, turn_rate=240)  # 直進200mm/s, 回転100deg/s
    
    # 直進移動: 300mm前進（非同期実行）

    await robot.straight(450)
    
    # 【角度指定でのモーター制御】元々の機能
    await right_lift.run_angle(500, -360)  # -360度回転
    await wait(100)
    await right_lift.run_angle(500, -360)  # -360度回転
    await wait(100)
    await right_lift.run_angle(500, -360)  # -360度回転
    await wait(100)
    
    # 【時間指定でのモーター制御】新機能
    # right_liftを500の速度で1000ミリ秒（1秒）動かす
    await right_lift.run_time(500, 1000)
    await wait(100)
    
    # right_liftを500の速度で1500ミリ秒（1.5秒）動かす
    await right_lift.run_time(500, 1500)
    await wait(100)
    
    # right_liftを500の速度で800ミリ秒（0.8秒）動かす
    await right_lift.run_time(500, 800)
    await wait(100)

    await robot.straight(240)

    # 【角度指定での回転】元々の機能
    await robot.turn(-50)

    # 【時間指定での回転】新機能 - 簡略化版
    await turn_time(left_wheel, right_wheel, 200, 1000, "right")  # 右回転1秒

    await robot.straight(80)


    ## リフト操作: 左リフトを速度200で360度回転（非同期実行）
    #await left_lift.run_angle(200, 360)
    #
    ## 時間指定でモーターを動かす例（非同期実行）
    #await left_lift.run_time(300, 2000)  # 速度300で2000ミリ秒（2秒）動かす
    #await right_lift.run_time(-200, 1500) # 速度-200（逆方向）で1500ミリ秒（1.5秒）動かす
    #
    ## 回転動作: その場で90度右回転（非同期実行）
    #await robot.turn(90)
    #
    ## 時間指定での回転動作例（簡略化版）
    #await turn_time(left_wheel, right_wheel, 300, 1500, "right")  # 右回転1.5秒
    #await turn_time(left_wheel, right_wheel, 250, 2000, "left")   # 左回転2秒
    #
    ## 時間指定での回転動作例（従来版）
    #left_wheel.run(300); right_wheel.run(-300); await wait(1500); left_wheel.stop(); right_wheel.stop()  # 右回転1.5秒
    #left_wheel.run(-250); right_wheel.run(250); await wait(2000); left_wheel.stop(); right_wheel.stop() # 左回転2秒
    #
    ## 動作中の速度変更例: より高速な設定に変更
    #robot.settings(straight_speed=400, turn_rate=200)  # 高速設定
    #
    ## リフト操作: 左リフトを速度200で360度回転（同期実行・awaitなし）
    #left_lift.run_angle(200, 360)
    #
    ## 時間指定でモーターを動かす例（同期実行・awaitなし）
    #left_lift.run_time(250, 1000)  # 速度250で1000ミリ秒（1秒）動かす（並行実行）
    #
    ## カーブ移動: 半径150mmで90度カーブ（非同期実行）
    #await robot.curve(150, 90)
    #
    ## 精密動作用の低速設定例
    #robot.settings(straight_speed=100, turn_rate=50)   # 低速・高精度設定
    #await robot.straight(50)  # 精密な50mm移動
    pass  # 何も実行しない場合の構文エラー回避
    
##########################################


async def sensor_logger_task():
    """
    センサー値を定期的にターミナルに表示する非同期タスク。
    他のタスク（ロボットの移動）と並行して実行されます。
    """
    print("--- センサーログタスク開始 ---")
    while True: # プログラムが終了するまで継続的にログを出力
        heading = hub.imu.heading()
        left_deg = left_wheel.angle()
        right_deg = right_wheel.angle()
        dist = robot.distance()
        print(f"LOG: dist={dist:4.0f} mm  heading={heading:4.0f}°  L={left_deg:5.0f}°  R={right_deg:5.0f}°")
        await wait(200) # 100ミリ秒待機して、他のタスクに実行を譲る

async def main():
    await run(hub ,robot, left_wheel, right_wheel,left_lift,right_lift)

if __name__=="__main__":
    hub ,robot, left_wheel, right_wheel,left_lift,right_lift = initialize_robot()
    run_task(multitask(
        sensor_logger_task(), 
        main()
    ))