from pybricks.hubs import PrimeHub
from pybricks.parameters import Port, Axis, Direction
from pybricks.pupdevices import Motor
from pybricks.robotics import DriveBase
from pybricks.tools import wait, multitask, run_task
from setup import initialize_robot


hub, left, right, robot = initialize_robot()

# 走行設定

straight_rate = 40                              # 直進速度の最大値に対する割合
straight_spd = 500 * (straight_rate / 100)      # 割合に沿って速度を決定
turn_rate = 30                                  # 旋回速度の最大値に対する割合
turn_spd = 500 * (turn_rate / 100)              # 割合に沿って速度を決定

robot.settings(
    straight_speed=straight_spd,        # 直進速度      デフォルト:200mm/s      最大速度の40%    
    turn_rate=turn_spd,                # 旋回速度      デフォルト:200deg/s     最大速度の40%
)


# ───────────────────────────────────────────
# 3) ジャイロ PID を有効化し、計測を初期化
# ───────────────────────────────────────────
robot.use_gyro(True)
hub.imu.reset_heading(0)
robot.reset()



# ───────────────────────────────────────────
# 非同期タスクの定義
# ───────────────────────────────────────────

async def sensor_logger_task():
    """
    センサー値を定期的にターミナルに表示する非同期タスク。
    他のタスク（ロボットの移動）と並行して実行されます。
    """
    print("--- センサーログタスク開始 ---")
    while True: # プログラムが終了するまで継続的にログを出力
        heading = hub.imu.heading()
        left_deg = left.angle()
        right_deg = right.angle()
        dist = robot.distance()
        print(f"LOG: dist={dist:4.0f} mm  heading={heading:4.0f}°  L={left_deg:5.0f}°  R={right_deg:5.0f}°")
        await wait(200) # 100ミリ秒待機して、他のタスクに実行を譲る

async def straight_with_power(distance_mm, motor_power):
    """
    
    Args:
        robot: DriveBaseオブジェクト
        distance_mm: 進む距離（ミリメートル）
        motor_power: モーターの出力（-100から100の範囲）
    """
    robot.settings(straight_speed=abs(motor_power) * 5)  # 出力を速度に変換
    await robot.straight(distance_mm)


async def turn_with_power(angle_deg, motor_power):
    """
    モーターの出力と角度を引数に取る回転関数
    
    Args:
        angle_deg: 回転角度（度）
        motor_power: モーターの出力（-100から100の範囲）
    """
    robot.settings(turn_rate=abs(motor_power) * 5)  # 出力を回転速度に変換
    await robot.turn(angle_deg)
    robot.stop()
    hub.imu.reset_heading(0)

async def test():
    print("straight 100")
    await straight_with_power(100, 100)
    await wait(50)
    print("straight 10")
    await straight_with_power(100, 10)
    await wait(50)
    print("turn 100")
    await turn_with_power(100, 100)
    await wait(50)
    print("turn 10")
    await turn_with_power(360, 10)
    await wait(50)




# ───────────────────────────────────────────
# プログラムの実行
# ───────────────────────────────────────────

# run_task() を使うことで、main_robot_sequence_task が完了するまで
# プログラム全体が終了しないようにします。
# sensor_logger_task は main_robot_sequence_task と並行して動作します。
# run_task() が終わると、他のすべてのタスクも停止します。
run_task(multitask(
    sensor_logger_task(),         # センサー値を継続的にログに出力するタスク
    # main_robot_sequence_task()    # ロボットの移動シーケンスを実行するタスク
    test()
))

print("Finished! (すべてのタスクが完了しました)") # この行はタスク完了後に実行される