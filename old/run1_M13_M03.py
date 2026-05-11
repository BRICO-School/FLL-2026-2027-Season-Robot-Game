from pybricks.hubs import PrimeHub
from pybricks.parameters import Port, Axis, Direction, Color, Stop
from pybricks.pupdevices import Motor
from pybricks.robotics import DriveBase
from pybricks.tools import wait, multitask, run_task, StopWatch
from setup import initialize_robot


async def run(hub ,robot, left_wheel, right_wheel,left_lift,right_lift):

#######################################
    # ここにロボットの動作を記述してください

    # 速度・加速度設定を定義
    # 直進時の設定
    straight_settings = {
        'straight_speed': 400,
        'straight_acceleration': 500
    }
    
    # 回転時の設定
    turn_settings = {
        'turn_rate': 240,
        'turn_acceleration': 850
    }
    
    # カーブ時の設定
    curve_settings = {
        'straight_speed': 240,
        'straight_acceleration': 800
    }


    '''
    '''

    # 直進設定を適用
    robot.settings(**straight_settings)
    await robot.straight(650)  #M13に向けて前進   

    # 回転設定を適用
    robot.settings(**turn_settings)
    await robot.turn(90)       # 90度右回転

    # 直進設定を適用
    robot.settings(**straight_settings)
    await robot.straight(262)  #M13に向けて前進   

    # 回転設定を適用
    robot.settings(**turn_settings)
    await robot.turn(39)       # 45度右回転

    # 直進設定を適用
    robot.settings(**straight_settings)
    await robot.straight(140)  #M13に向けて前進   
    await wait(100)                      # 0.2秒待機

    await right_lift.run_angle(150, 380) # 右アーム操作（スピード, 角度）
    await wait(300)                      # 0.2秒待機

    # 回転設定を適用
    robot.settings(**turn_settings)
    await robot.turn(-30)       # 20度左回転
    await wait(700)                      # 0.2秒待機

    # 回転設定を適用
    robot.settings(**turn_settings)
    await robot.turn(30)       # 20度右回転

    # 直進設定を適用
    robot.settings(**straight_settings)
    await robot.straight(-48)  #M13に向けて前進   

    # await right_lift.run_angle(800, 360*2)  # 右アームを上げる

    # 回転設定を適用
    robot.settings(**turn_settings)
    await robot.turn(245)       # 20度左回転

    await right_lift.run_angle(1000, -350)  # 右アームを下げる

    await robot.straight(48)  #M13に向けて前進   

    await right_lift.run_angle(1000, 360*3)  # 右アームを上げる
    await wait(500)                      # 0.2秒待機

    await right_lift.run_angle(800, -50)  # 右アームを下げる

    # 回転設定を適用
    robot.settings(**turn_settings)
    await robot.turn(-100)       # 20度右回転

    robot.settings(**straight_settings)
    await robot.straight(300)  #M13に向けて前進   

    robot.settings(**turn_settings)
    await robot.turn(-80)       # 20度右回転

    robot.settings(**straight_settings)
    await robot.straight(700)  #M13に向けて前進   

    '''
    await left_lift.run_angle(800, 360*3)        # 左アームを下げる（完了を待つ）
    # この時点で両方の動作が完了している
    '''


    # 【参考】方法2: multitaskを使った同時実行（よりわかりやすい）
    # await multitask(
    #     right_lift.run_angle(300, 360),   # 右アームを上げる
    #     left_lift.run_angle(300, -360)    # 左アームを下げる
    # )


    # 例: ブロイントまで移動
    # await robot.straight(400)  # 400mm前進
    # await robot.turn(45)       # 45度右回転
    
    # アームでブロックを掴む
    # await left_lift.run_angle(300, 180)  # 左アーム操作（スピード, 角度）
    # await right_lift.run_angle(300, 180) # 右アーム操作（スピード, 角度）
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