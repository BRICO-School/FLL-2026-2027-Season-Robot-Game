from pybricks.hubs import PrimeHub
from pybricks.parameters import Port, Axis, Direction, Color, Stop
from pybricks.robotics import DriveBase
from pybricks.tools import wait, multitask, run_task, StopWatch
from setup import initialize_robot


async def run(hub, robot, left_wheel, right_wheel, left_lift, right_lift):
    #######################################
    # ここにロボットの動作を記述してください

    async def guarded_straight(total_mm):
        """
        指定距離(total_mm)を50mm単位で分割直進し、詰まり時は次動作へ進む。
        """
        step_unit_mm = 50
        timeout_ms = 700
        min_progress_mm = 12

        direction = 1 if total_mm >= 0 else -1
        remaining_mm = abs(total_mm)
        step_index = 0

        while remaining_mm > 0:
            this_step_mm = direction * min(step_unit_mm, remaining_mm)
            before = robot.distance()
            timer = StopWatch()
            timer.reset()
            await robot.straight(this_step_mm, timeout=timeout_ms)
            elapsed = timer.time()
            moved = abs(robot.distance() - before)
            step_index += 1

            if moved < min_progress_mm:
                print(
                    "STRAIGHT timeout/stall -> continue "
                    f"(step={step_index}, moved={moved}mm, elapsed={elapsed}ms)"
                )
                return False

            if elapsed >= timeout_ms and moved < abs(this_step_mm):
                print(
                    "STRAIGHT timeout/stall -> continue "
                    f"(step={step_index}, moved={moved}mm, elapsed={elapsed}ms)"
                )

            remaining_mm -= abs(this_step_mm)

        return True

    # await robot.straight(40)
    # 少し、左アームを下げる
    await left_lift.run_angle(500, -200)
    wait(1000)
    await guarded_straight(100)
    wait(1000)
    # 左アームを下げる
    await left_lift.run_angle(500, -140)
    wait(1000)
    # 左アームを上げる
    await left_lift.run_angle(300, 300)
    wait(3000)
    # 少しバック
    await robot.straight(-300)

    #######################################

    # ロボットを停止
    robot.stop()
    print("# 走行完了！")


# ===== 単体テスト用（このファイルを直接実行した場合） =====
if __name__ == "__main__":
    hub, robot, left_wheel, right_wheel, left_lift, right_lift = initialize_robot()
    run_task(run(hub, robot, left_wheel, right_wheel, left_lift, right_lift))
