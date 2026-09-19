from pybricks.hubs import PrimeHub
from pybricks.parameters import Port, Axis, Direction ,Color
from pybricks.pupdevices import Motor
from pybricks.robotics import DriveBase
from pybricks.tools import wait, multitask, run_task
from setup import initialize_robot


async def run1(hub ,robot, left_wheel, right_wheel,left_lift,right_lift):
    left_lift.run_angle(360,360)#左リフトを360°/sで360°回す
    await robot.turn(90)#90°曲がる
    await robot.straight(100)#100mm直進
    await right_wheel.run_angle(200,360)#右タイヤを200°/sで360°回す
