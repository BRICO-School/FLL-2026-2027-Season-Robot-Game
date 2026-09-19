"""
【runファイルテンプレート】
このファイルは新しいrunを作成するためのテンプレートです。
コピーして使用してください。

【使い方】
1. このファイルをコピーして、新しい名前をつける（例: run2_M04_M05.py）
2. run() 関数内にロボットの動作を記述する
3. selector.py の programs リストに追加する
"""

from pybricks.hubs import PrimeHub
from pybricks.parameters import Port, Axis, Direction, Color, Stop
from pybricks.pupdevices import Motor
from pybricks.robotics import DriveBase
from pybricks.tools import wait, multitask, run_task, StopWatch
from setup import initialize_robot

# 走行ログの間隔（ミリ秒）
LOG_INTERVAL_MS = 100
# 円周率（Pybricks では math が使えないため定数で定義）
PI = 3.141592653589793
# 実験の繰り返し回数（1なら1回だけ）
EXPERIMENT_RUNS = 1
stop_logging = False


async def _sensor_logger_task(robot):
    """走行時間・走行距離・走行速度を一定間隔でログ出力する。"""
    global stop_logging
    timer = StopWatch()
    timer.reset()
    last_dist = robot.distance()
    print("--- 走行ログ開始 ---")
    print("走行時間_ms,走行距離_mm,走行速度_mm_s")
    while not stop_logging:
        elapsed = timer.time()
        dist = robot.distance()
        delta = dist - last_dist
        last_dist = dist
        interval_s = LOG_INTERVAL_MS / 1000.0
        speed_mm_s = delta / interval_s if interval_s > 0 else 0.0
        print(f"{elapsed:.0f},{dist:.1f},{speed_mm_s:.1f}")
        await wait(LOG_INTERVAL_MS)
    print("--- 走行ログ終了 ---")


def _norm_angle_diff(actual_deg):
    """角度差を -180～180 に正規化する。"""
    while actual_deg > 180:
        actual_deg -= 360
    while actual_deg < -180:
        actual_deg += 360
    return actual_deg


def _print_section_table(section_results):
    """セクション別の想定・結果・誤差を表で出力する。"""
    print("| セクション     | 想定      | 結果      | 誤差      |")
    print("|----------------|-----------|-----------|-----------|")
    for s in section_results:
        name, expected, actual, unit = s["name"], s["expected"], s["actual"], s["unit"]
        if unit == "deg":
            actual = _norm_angle_diff(actual)
        err = actual - expected
        print(
            f"| {name:<14} | {expected:>7.1f} {unit} | {actual:>7.1f} {unit} | {err:>+7.1f} {unit} |"
        )
    print("")


async def run(hub, robot, left_wheel, right_wheel, left_lift, right_lift):
    """
    ロボットの動作を記述する関数

    【使用可能なメソッド】

    === 移動系（speedとtimeoutを指定可能） ===
    await robot.straight(400)                            # 400mm直進
    await robot.straight(200, speed=500)                 # 500mm/sで200mm直進
    await robot.straight(-300)                           # 300mm後退
    await robot.straight(500, timeout=3000)              # 3秒以内に500mm直進（タイムアウト）
    await robot.straight(200, speed=300, timeout=2000)   # 300mm/sで2秒以内に200mm直進

    await robot.turn(90)                                 # 90度右回転
    await robot.turn(-45)                                # 45度左回転
    await robot.turn(180, rate=300)                      # 300deg/sで180度回転
    await robot.turn(90, timeout=1500)                   # 1.5秒以内に90度回転

    await robot.curve(200, 90)                           # 半径200mmで90度カーブ
    await robot.curve(300, 45, speed=150)                # 150mm/sで半径300mm、45度カーブ
    await robot.curve(150, 60, timeout=2000)             # 2秒以内にカーブ

    === モーター操作（timeoutを指定可能） ===
    await left_lift.run_angle(300, 180)                  # 左アームを300deg/sで180度回転
    await right_lift.run_angle(500, -360)                # 右アームを逆方向に1回転
    await robot.run_motor(right_wheel, 200, 140, timeout=1500)  # 1.5秒以内に右車輪を回転

    === 待機 ===
    await wait(500)                                      # 0.5秒待機
    await wait(1000)                                     # 1秒待機

    === デフォルト速度設定（setup.pyで定義） ===
    - straight: 400mm/s, 加速度500mm/s²
    - turn: 240deg/s, 加速度850deg/s²
    - curve: 240mm/s, 加速度800mm/s²
    """

    #######################################
    # ここにロボットの動作を記述してください
    #######################################

    global stop_logging
    run_timer = StopWatch()
    results = []
    run_section_results = []

    async def motion():
        global stop_logging
        dist_before = robot.distance()
        heading_before = hub.imu.heading()
        try:
            # 1. straight 500mm
            await robot.straight(500)
            dist_after = robot.distance()
            run_section_results.append(
                {
                    "name": "直進500",
                    "expected": 500.0,
                    "actual": dist_after - dist_before,
                    "unit": "mm",
                }
            )
            dist_before, heading_before = dist_after, hub.imu.heading()

            # 2. curve 250mm, -90deg（弧長 = 250*90*π/180）
            await robot.curve(250, -90)
            dist_after = robot.distance()
            expected_curve_mm = 250.0 * 90.0 * PI / 180.0
            run_section_results.append(
                {
                    "name": "カーブ250,-90",
                    "expected": expected_curve_mm,
                    "actual": dist_after - dist_before,
                    "unit": "mm",
                }
            )
            dist_before, heading_before = dist_after, hub.imu.heading()

            # 3. straight 350mm
            await robot.straight(350)
            dist_after = robot.distance()
            run_section_results.append(
                {
                    "name": "直進350",
                    "expected": 350.0,
                    "actual": dist_after - dist_before,
                    "unit": "mm",
                }
            )
            dist_before, heading_before = dist_after, hub.imu.heading()

            # 4. turn 90deg
            await robot.turn(90)
            heading_after = hub.imu.heading()
            run_section_results.append(
                {
                    "name": "旋回90",
                    "expected": 90.0,
                    "actual": _norm_angle_diff(heading_after - heading_before),
                    "unit": "deg",
                }
            )
            dist_before, heading_before = robot.distance(), heading_after

            # 5. straight -550mm
            await robot.straight(-550)
            dist_after = robot.distance()
            run_section_results.append(
                {
                    "name": "後退550",
                    "expected": -550.0,
                    "actual": dist_after - dist_before,
                    "unit": "mm",
                }
            )
            dist_before, heading_before = dist_after, hub.imu.heading()

            # 6. turn 90deg
            await robot.turn(90)
            heading_after = hub.imu.heading()
            run_section_results.append(
                {
                    "name": "旋回90(2)",
                    "expected": 90.0,
                    "actual": _norm_angle_diff(heading_after - heading_before),
                    "unit": "deg",
                }
            )
            dist_before, heading_before = robot.distance(), heading_after

            # 7. straight 800mm
            await robot.straight(800)
            dist_after = robot.distance()
            run_section_results.append(
                {
                    "name": "直進800",
                    "expected": 800.0,
                    "actual": dist_after - dist_before,
                    "unit": "mm",
                }
            )
        finally:
            stop_logging = True

    for run_num in range(1, EXPERIMENT_RUNS + 1):
        run_section_results.clear()
        robot.reset()
        stop_logging = False
        run_timer.reset()
        await multitask(_sensor_logger_task(robot), motion())
        robot.stop()
        elapsed_ms = run_timer.time()
        total_dist_mm = robot.distance()
        results.append((run_num, elapsed_ms, total_dist_mm))
        speed_mm_s = total_dist_mm / (elapsed_ms / 1000.0) if elapsed_ms > 0 else 0.0
        print("# 走行完了！")
        print(f"走行時間: {elapsed_ms} ms ({elapsed_ms / 1000:.1f} 秒)")
        print(f"走行距離: {total_dist_mm:.1f} mm")
        print(f"走行速度: {speed_mm_s:.1f} mm/s")
        print("")
        print(f"--- セクション別 想定 vs 結果（{run_num}回目） ---")
        _print_section_table(run_section_results)

    print("")
    print("========== 実験結果まとめ（1回目を基準） ==========")
    ref_ms, ref_mm = results[0][1], results[0][2]
    print("| 回 | 走行時間(秒) | 走行距離(mm) | 走行速度(mm/s) | 時間誤差(秒) | 距離誤差(mm) |")
    print("|----|-------------|-------------|----------------|-------------|-------------|")
    for run_num, elapsed_ms, total_dist_mm in results:
        t_sec = elapsed_ms / 1000.0
        speed_mm_s = total_dist_mm / t_sec if t_sec > 0 else 0.0
        err_sec = (elapsed_ms - ref_ms) / 1000.0
        err_mm = total_dist_mm - ref_mm
        print(
            f"| {run_num}  | {t_sec:>11.1f} | {total_dist_mm:>11.1f} | {speed_mm_s:>14.1f} | {err_sec:>+11.1f} | {err_mm:>+11.1f} |"
        )
    print("==============================================================")


# ===== 単体テスト用（このファイルを直接実行した場合） =====
if __name__ == "__main__":
    hub, robot, left_wheel, right_wheel, left_lift, right_lift = initialize_robot()
    run_task(run(hub, robot, left_wheel, right_wheel, left_lift, right_lift))
