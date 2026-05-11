from pybricks.hubs import PrimeHub
from pybricks.parameters import Port, Axis, Direction, Color, Stop
from pybricks.pupdevices import Motor
from pybricks.robotics import DriveBase
from pybricks.tools import wait, multitask, run_task, StopWatch
from setup import initialize_robot


async def run(hub ,robot, left_wheel, right_wheel,left_lift,right_lift):
#######################################
    # ここにロボットの動作を記述してください
    
    # ステップ1: 目標地点に向かって前進
    await robot.straight(350)  # 350mm直進して移動
    
    # ステップ2: 位置調整のため少し後退
    await robot.straight(-130)  # 130mm後退して最適な位置に調整
    
    # ステップ3: カーブしながら前進（タイムアウト処理付き）
    await robot.curve(850, 25, speed=200, timeout=2000)  # 200mm/sでカーブ、2秒でタイムアウト
    
    # ステップ4: スタート地点に向けて後退
    await robot.straight(-550, speed=350)  # 350mm/sで後退してベースに戻る 
    
    # 例: ブロイントまで移動
    # await robot.straight(400)  # 400mm前進
    # await robot.turn(45)       # 45度右回転
    
    # アームでブロックを掴む
    # await left_lift.run_angle(300, 180)  # 左アーム操作
    # await right_lift.run_angle(300, 180) # 右アーム操作
    # await wait(500)                      # 0.5秒待機
    
    # ブロックを運搬
    # await robot.straight(-100)   # 100mm後退
    # await robot.turn(-90)        # 90度左回転
    # await robot.straight(600)    # 600mm前進
    
    # ブロックを配置
    # await left_lift.run_angle(300, -180)  # アームを戻す
    # await right_lift.run_angle(300, -180)
    # await wait(300)
    
    # 初期位置に戻る
    # await robot.straight(-300)
    # await robot.turn(45)



    # ロボットを明示的に停止
    robot.stop()
    print("# 走行完了！")

    pass  # 何も実行しない場合の構文エラー回避
    
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
    # 経過時間測定用のタイマーを開始
    logger_timer = StopWatch()
    logger_timer.reset()
    
    while not stop_logging: # stop_loggingフラグがTrueになるまで継続
        elapsed_time = logger_timer.time()
        heading = hub.imu.heading()
        left_deg = left_wheel.angle()
        right_deg = right_wheel.angle()
        dist = robot.distance()
        print(f"LOG[{elapsed_time:5.0f}ms]: dist={dist:4.0f} mm  heading={heading:4.0f}°  L={left_deg:5.0f}°  R={right_deg:5.0f}°")
        await wait(200) # 200ミリ秒待機して、他のタスクに実行を譲る
    
    print("--- センサーログタスク終了 ---")

async def main():
    global stop_logging
    await run(hub ,robot, left_wheel, right_wheel,left_lift,right_lift)
    # main()が終了したらログタスクも終了させる
    stop_logging = True
    print("--- メインタスク完了、ログタスク終了中 ---")
    await wait(500)  # ログタスクが終了するまで少し待つ

if __name__=="__main__":
    hub ,robot, left_wheel, right_wheel,left_lift,right_lift = initialize_robot()
    run_task(multitask(
        sensor_logger_task(), 
        main()
    ))