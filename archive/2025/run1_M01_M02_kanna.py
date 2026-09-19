from pybricks.hubs import PrimeHub
from pybricks.parameters import Port, Axis, Direction, Color, Stop
from pybricks.pupdevices import Motor
from pybricks.robotics import DriveBase
from pybricks.tools import wait, multitask, run_task, StopWatch
from setup import initialize_robot


async def run(hub ,robot, left_wheel, right_wheel,left_lift,right_lift):

#######################################
    # ここにロボットの動作を記述してください

    '''
    '''

    await robot.straight(590)  #M01に向けて前進   

    await robot.straight(-120)  #M01で後進して奥側の羽を倒す   

    await robot.turn(40)      #M02に向けて方向転換

    await robot.straight(220)  #まっすぐすすむ

    await robot.turn(-85)      #M02に向けて方向転換

    await robot.straight(205, timeout=3000)  # 3秒でタイムアウト

    await robot.straight(-210)  #まっすぐすすむ

    await robot.turn(-45)      #曲がる
 
    await robot.straight(50)  #まっすぐすすむ

    await left_lift.run_angle(300, 180)  # 左アーム操作

    await robot.straight(-50)  #まっすぐすすむ

    await robot.turn(-70)      #曲がる

    await robot.straight(580)  #まっすぐすすむ
    

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

    # ヘッダーを一度だけ表示
    print("time,current_dist_mm,error_angle_deg,current_heading_deg,left_angle_deg,right_angle_deg,angle_diff_deg,left_speed_dps,right_speed_dps,speed_diff_dps,kp_dist,ki_dist,kd_dist,kp_head,ki_head,kd_head")

    while not stop_logging: # stop_loggingフラグがTrueになるまで継続
        elapsed_time = logger_timer.time()

        # 基本センサー値
        current_dist_mm = robot.distance()
        current_heading_deg = hub.imu.heading()
        left_angle_deg = left_wheel.angle()
        right_angle_deg = right_wheel.angle()

        # 角度差分
        angle_diff_deg = right_angle_deg - left_angle_deg

        # 速度（dps: degrees per second）
        left_speed_dps = left_wheel.speed()
        right_speed_dps = right_wheel.speed()
        speed_diff_dps = right_speed_dps - left_speed_dps

        # PIDゲイン値（setup.pyで設定された値を使用）
        kp_dist = 1000
        ki_dist = 50
        kd_dist = 10
        kp_head = 2000
        ki_head = 50
        kd_head = 100

        # エラー角度（目標角度との差 - 概算）
        error_angle_deg = 0  # PyBricksでは目標値を直接取得できないため0とする

        print(f"{elapsed_time:.0f},{current_dist_mm:.1f},{error_angle_deg:.1f},{current_heading_deg:.1f},{left_angle_deg:.1f},{right_angle_deg:.1f},{angle_diff_deg:.1f},{left_speed_dps:.1f},{right_speed_dps:.1f},{speed_diff_dps:.1f},{kp_dist:.1f},{ki_dist:.1f},{kd_dist:.1f},{kp_head:.1f},{ki_head:.1f},{kd_head:.1f}")

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