from pybricks.hubs import PrimeHub
from pybricks.parameters import Port, Axis, Direction, Color, Stop
from pybricks.pupdevices import Motor
from pybricks.robotics import DriveBase
from pybricks.tools import wait, multitask, run_task, StopWatch
from setup import initialize_robot


async def run(hub ,robot, left_wheel, right_wheel,left_lift,right_lift):

#######################################
    # ここにロボットの動作を記述してください

    # M08

    # 最初の目標地点まで前進（450mm）
    print(">>> 実行: await robot.straight(450)")
    await robot.straight(450)
    
    # 右アームを下げる（速度500、角度-360度）
    print(">>> 実行: await right_lift.run_angle(500,-1100)")
    await right_lift.run_angle(500,-360)

    await wait(100)  # 0.1秒待機
    
    # 右アームを下げる（速度500、角度-360度）
    print(">>> 実行: await right_lift.run_angle(500,-1100)")
    await right_lift.run_angle(500,-360)

    await wait(100)  # 0.1秒待機

    # 右アームを下げる（速度500、角度-360度）
    print(">>> 実行: await right_lift.run_angle(500,-1100)")
    await right_lift.run_angle(500,-360)

    await wait(50)  # 0.1秒待機    # M06


    #M06

    # 微調整のため左に5度回転
    print(">>> 実行: await robot.turn(-5)")
    await robot.turn(-5)
    
    # さらに前進（250mm）- 目標位置に近づく
    print(">>> 実行: await robot.straight(250)")
    await robot.straight(250)
    

    # M05

    await robot.turn(-42)
    await robot.straight(34)

    # 右の車輪だけを少し動かす（180度回転、タイムアウト1.5秒）
    print(">>> 実行: right_wheel.run_angle(200, 140) [タイムアウト1.5秒]")
    await robot.run_motor(right_wheel, 200, 140, timeout=1500)
        

    # ホームエリアに戻る

    # 時計回りに60度回転
    print(">>> 実行: await robot.turn(45)")
    await robot.turn(50)

    # 後退して初期位置方向に戻る（720mm）- 500mm/sスピード
    print(">>> 実行: await robot.straight(-720) [500mm/sスピード]")
    await robot.straight(-720, speed=500)


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



    pass  # 何も実行しない場合の構文エラー回避
    
##########################################



async def sensor_logger_task():
    """
    センサー値を定期的にターミナルに表示する非同期タスク。
    他のタスク（ロボットの移動）と並行して実行されます。
    """
    print("--- センサーログタスク開始 ---")
    # 経過時間測定用のタイマーを開始
    logger_timer = StopWatch()
    logger_timer.reset()
    
    while True: # プログラムが終了するまで継続的にログを出力
        elapsed_time = logger_timer.time()
        heading = hub.imu.heading()
        left_deg = left_wheel.angle()
        right_deg = right_wheel.angle()
        dist = robot.distance()
        print(f"LOG[{elapsed_time:5.0f}ms]: dist={dist:4.0f} mm  heading={heading:4.0f}°  L={left_deg:5.0f}°  R={right_deg:5.0f}°")
        await wait(200) # 200ミリ秒待機して、他のタスクに実行を譲る

async def main():
    await run(hub ,robot, left_wheel, right_wheel,left_lift,right_lift)

if __name__=="__main__":
    hub ,robot, left_wheel, right_wheel,left_lift,right_lift = initialize_robot()
    run_task(multitask(
        sensor_logger_task(), 
        main()
    ))