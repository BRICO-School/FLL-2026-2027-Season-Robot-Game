from pybricks.hubs import PrimeHub
from pybricks.parameters import Port, Axis, Direction
from pybricks.pupdevices import Motor
from pybricks.robotics import DriveBase
from pybricks.tools import wait, multitask, run_task
from setup import initialize_robot



def straight_with_power(robot,distance_mm, motor_power):
    """
   
    Args:
       robot: DriveBaseオブジェクト
       distance_mm: 進む距離（ミリメートル）
       motor_power: モーターの出力（-100から100の範囲）
    """
    robot.settings(straight_speed=abs(motor_power) * 5)  # 出力を速度に変換
    robot.straight(distance_mm)

def turn_with_power(robot,hub,angle_deg, motor_power):
    """
    モーターの出力と角度を引数に取る回転関数
   
    Args:
       angle_deg: 回転角度（度）
       motor_power: モーターの出力（-100から100の範囲）
    """
    robot.settings(turn_rate=abs(motor_power) * 5)  # 出力を回転速度に変換
    robot.turn(angle_deg)
    robot.stop()
    hub.imu.reset_heading(0)

   