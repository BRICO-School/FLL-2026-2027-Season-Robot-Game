from pybricks.hubs import PrimeHub
from pybricks.parameters import Port, Axis, Direction ,Color
from pybricks.pupdevices import Motor
from pybricks.robotics import DriveBase
from pybricks.tools import wait, multitask, run_task, StopWatch
from setup import initialize_robot

async def run(hub ,robot, left_wheel, right_wheel,left_lift,right_lift):
#######################################
    #度/秒
    rate=250
    #回転角度
    deg=180
    print(f"-------------{str(rate)}/s {str(deg)}deg-----------------")
    await wait(3000)
    robot.settings(straight_speed=500, turn_rate=rate)  # 直進200mm/s, 回転100deg/s
    
    # 直進移動: 300mm前進（非同期実行）
    #await robot.straight(-500)
    await wait(500)
    
    # 時間測定開始
    timer = StopWatch()
    timer.reset()
    print(f"回転開始: {deg}度回転（速度: {rate}deg/s）")
    
    await robot.turn(deg)
    
    # 時間測定終了
    elapsed_time = timer.time()
    print(f"回転完了: {elapsed_time}ms かかりました")
    print(f"理論時間: {abs(deg) / rate * 1000:.1f}ms（{abs(deg)}度 ÷ {rate}deg/s）")
    print(f"実測時間: {elapsed_time}ms")
    
    await wait(3000)
    raise SystemExit
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
    left_wheel.reset_angle(0)
    right_wheel.reset_angle(0)
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