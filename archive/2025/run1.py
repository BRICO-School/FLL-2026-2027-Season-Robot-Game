from pybricks.hubs import PrimeHub
from pybricks.parameters import Port, Axis, Direction
from pybricks.pupdevices import Motor
from pybricks.robotics import DriveBase
from pybricks.tools import wait, multitask, run_task
from setup import initialize_robot



def run1(robot,hub,left,right,lift):
    right.run_angle(360,360)