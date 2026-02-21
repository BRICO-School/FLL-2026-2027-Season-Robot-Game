from pybricks.hubs import PrimeHub
from pybricks.parameters import Port, Axis, Direction, Color, Stop
from pybricks.pupdevices import Motor
from pybricks.robotics import DriveBase
from pybricks.tools import wait, multitask, run_task, StopWatch
from setup import initialize_robot


# ===== テスト設定（ここだけ変えればOK）=====
# 実行したいテストを選ぶ（TEST_MODE を下のいずれかに変更）:
#
# 【直進テスト】前進のみ。距離・向きの誤差を表で表示
#   TEST_MODE = "straight"
#
# 【カーブテスト】半径・角度指定のカーブをN回。距離・向きの誤差を表で表示
#   TEST_MODE = "curve"
#
# 【その他】
# - "turn_accuracy": 旋回正確性（90°×10 + 180°×5）。KPI・合格判定・比較用スコア。
# - "turn": 旋回テスト（指定角度の誤差をN回）
# - "square": 四角形テスト（直進+90°×4）
# - "repeat": 直進20cm→後進20cmをN回
# - "speed": 直進の「巡航速度」と「加速度（走り出し）」を変えて比較。どの設定が誤差が小さいか表で表示。
# - "all": 狭い範囲で3種のみ（旋回正確性 → 直進 → カーブ）。本格版は各モードを個別に。
#
TEST_MODE = (
    "speed"  # 一度に全てのテストを実行。単体なら "straight"/"curve"/"turn_accuracy" 等に変更
)

# ログを出す間隔（ミリ秒）
LOG_INTERVAL_MS = 100

# テスト範囲: 縦80cm × 横40cm（直進=縦方向、往復=横方向で収まるよう距離を設定）
# 直進テスト（mm）
STRAIGHT_DISTANCE_MM = 800  # 縦80cm
STRAIGHT_SPEED = None  # 例: 300（mm/s）。Noneならデフォルト

# ----- 速度テスト（どの速度・加速度が適切か比較）-----
# 巡航速度の候補（mm/s）。ある程度走っている時の速度
SPEED_TEST_SPEEDS = [200, 300, 400]
# 加速度の候補（mm/s²）。走り出しのキツさ（大きい＝立ち上がりが速い）
SPEED_TEST_ACCELERATIONS = [300, 500, 800]
# 各条件での試行回数（比較用なので少なめでOK）
SPEED_TEST_RUNS = 5
# 加速度比較時に使う固定巡航速度（mm/s）
SPEED_TEST_ACCEL_REF_SPEED = 300

# 回転テスト（deg）
TURN_ANGLE_DEG = 90
TURN_RATE = None  # 例: 200（deg/s）。Noneならデフォルト

# カーブテスト（半径mm / 角度deg / 試行回数）※範囲: 縦80cm×横40cm
CURVE_RADIUS_MM = 200  # カーブの半径（mm）。正で左、負で右。横40cm内に収まる
CURVE_ANGLE_DEG = 90  # カーブで曲がる角度（deg）
CURVE_SPEED = None  # mm/s。Noneならデフォルト
CURVE_TEST_COUNT = 10  # カーブの試行回数

# テスト実行回数（直進・旋回・カーブテストをこの回数繰り返し、誤差を表にまとめる）
TEST_RUN_COUNT = 20

# 往復テスト（mm / 回数）※範囲: 縦80cm×横40cm
REPEAT_DISTANCE_MM = 400  # 横方向に40cm（1往復で収まる）
REPEAT_COUNT = 20
REPEAT_SPEED = None  # 例: 300（mm/s）。Noneならデフォルト
REPEAT_PAUSE_MS = 150  # 1動作ごとの停止後に少し待つ（慣性/振動の影響を減らす）
REPEAT_WITH_LOGGER = False  # Trueにすると往復中もLOG_INTERVAL_MS間隔でログを出す

# ----- 旋回正確性テスト（Turning Accuracy First）-----
# 測定プロトコル: 90°×N90回、180°×N180回。同一条件で実施。
TURN_ACCURACY_90_COUNT = 10  # 90°回転の試行回数
TURN_ACCURACY_180_COUNT = 5  # 180°回転の試行回数
TURN_ACCURACY_RATE = None  # 旋回角速度(deg/s)。Noneならデフォルト。遅めにするとSDが下がりやすい
# しっかり wait を挟む（計測の再現性・SD 改善）
TURN_ACCURACY_WAIT_AFTER_RESET_MS = (
    300  # リセット後、旋回を始めるまで待つ(ms)。IMU・車体を落ち着かせる
)
TURN_ACCURACY_SETTLE_MS = 300  # 旋回後に計測まで待つ(ms)。振動・滑りが収まってから読む
TURN_ACCURACY_WAIT_BETWEEN_RUNS_MS = (
    200  # 1本計測後、次のリセット前に待つ(ms)。連続実行の負荷を減らす
)
# 合格基準（KPI）
TURN_ACCURACY_MEAN_MAX_DEG = 2.0  # 平均角度誤差 ≤ 2.0°
TURN_ACCURACY_SD_MAX_DEG = 1.0  # 誤差の標準偏差 ≤ 1.0°
TURN_ACCURACY_DRIFT_MAX_MM = 10.0  # 旋回後の横ズレ（目安）≤ 10mm
TURN_ACCURACY_OVERSUHOOT_MAX_DEG = 3.0  # オーバーシュート ≤ 3°
# 目的関数の重み（最小化）: Score = w1*|平均誤差| + w2*SD + w3*横ズレ
TURN_ACCURACY_W1 = 0.5  # 平均誤差
TURN_ACCURACY_W2 = 0.4  # 再現性(SD)
TURN_ACCURACY_W3 = 0.1  # 横ズレ（mmをdegと同スケールにするため/10など要調整）


stop_logging = False


async def reset_pose(hub, robot):
    """距離と向きをリセットして、スタート地点を「いま」として扱う。"""
    robot.stop()
    robot.reset()
    hub.imu.reset_heading(0)
    await wait(50)


async def sensor_logger_task(hub, robot, left_wheel, right_wheel, label):
    """
    センサー値を定期的にターミナルに表示する非同期タスク。
    """
    global stop_logging

    timer = StopWatch()
    timer.reset()

    last_dist = robot.distance()

    print(f"--- logger start: {label} ---")
    print("ms,dist_mm,delta_mm,heading_deg,left_deg,right_deg,left_dps,right_dps")

    while not stop_logging:
        elapsed = timer.time()
        dist = robot.distance()
        heading = hub.imu.heading()
        left_deg = left_wheel.angle()
        right_deg = right_wheel.angle()
        left_dps = left_wheel.speed()
        right_dps = right_wheel.speed()

        delta = dist - last_dist
        last_dist = dist

        print(
            f"{elapsed:.0f},{dist:.1f},{delta:.1f},{heading:.1f},{left_deg:.1f},{right_deg:.1f},{left_dps:.1f},{right_dps:.1f}"
        )

        await wait(LOG_INTERVAL_MS)

    print(f"--- logger end: {label} ---")


async def _run_with_logger(hub, robot, left_wheel, right_wheel, label, motion_coro):
    global stop_logging
    stop_logging = False
    try:
        await multitask(
            sensor_logger_task(hub, robot, left_wheel, right_wheel, label),
            motion_coro,
        )
    finally:
        stop_logging = True
        await wait(50)


async def straight_test(hub, robot, left_wheel, right_wheel):
    results = []
    for run_num in range(1, TEST_RUN_COUNT + 1):
        await reset_pose(hub, robot)

        async def motion():
            global stop_logging
            try:
                if STRAIGHT_SPEED is None:
                    await robot.straight(STRAIGHT_DISTANCE_MM)
                else:
                    await robot.straight(STRAIGHT_DISTANCE_MM, speed=STRAIGHT_SPEED)
            finally:
                stop_logging = True

        await _run_with_logger(hub, robot, left_wheel, right_wheel, "straight", motion())

        dist = robot.distance()
        heading = hub.imu.heading()
        err_mm = dist - STRAIGHT_DISTANCE_MM
        results.append(
            (run_num, STRAIGHT_DISTANCE_MM, f"{dist:.1f}", f"{err_mm:+.1f}", f"{heading:.1f}")
        )
        print(
            f"  run {run_num}/{TEST_RUN_COUNT}: actual={dist:.1f}mm error={err_mm:+.1f}mm heading={heading:.1f}deg"
        )
        # 距離制限のため、計測後は同じ距離で戻る（スタート位置付近に戻す）
        if STRAIGHT_SPEED is None:
            await robot.straight(-STRAIGHT_DISTANCE_MM)
        else:
            await robot.straight(-STRAIGHT_DISTANCE_MM, speed=STRAIGHT_SPEED)

    print("=== straight result (誤差の表) ===")
    _print_error_table(
        results,
        ("回", "目標(mm)", "実際(mm)", "誤差(mm)", "向き(deg)"),
        [4, 8, 10, 10, 10],
    )
    errs = [float(r[3]) for r in results]
    print(f"誤差(mm): 平均={_mean(errs):.1f} 最大絶対値={_max_abs(errs):.1f}")

    md_lines = [
        "# 直進テスト結果 (straight)",
        "",
        f"- 目標距離: {STRAIGHT_DISTANCE_MM} mm, 試行回数: {TEST_RUN_COUNT}",
        "",
        "| 回 | 目標(mm) | 実際(mm) | 誤差(mm) | 向き(deg) |",
        "|----|----------|----------|----------|-----------|",
    ]
    for r in results:
        md_lines.append(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} |")
    md_lines.append("")
    md_lines.append(f"- 誤差 平均: {_mean(errs):.1f} mm, 最大絶対値: {_max_abs(errs):.1f} mm")
    _write_test_result_md("straight", "\n".join(md_lines))


async def straight_speed_test(hub, robot, left_wheel, right_wheel):
    """
    巡航速度・加速度（走り出し）を変えて直進し、どの設定が誤差が小さいか比較する。
    """
    dist = STRAIGHT_DISTANCE_MM
    target_heading = 0.0  # 直進なので向きは0のままが理想

    # --- 1. 巡航速度の比較（走っている時の速度）---
    print("=== 速度テスト: 巡航速度の比較（直進時の速度 mm/s）===")
    speed_rows = []
    for speed in SPEED_TEST_SPEEDS:
        errs_mm = []
        errs_deg = []
        for _ in range(SPEED_TEST_RUNS):
            await reset_pose(hub, robot)
            await robot.straight(dist, speed=speed)
            d = robot.distance()
            h = hub.imu.heading()
            errs_mm.append(d - dist)
            errs_deg.append(h - target_heading)
            await robot.straight(-dist, speed=speed)
        avg_mm = _mean(errs_mm)
        max_mm = _max_abs(errs_mm)
        avg_deg = _mean(errs_deg)
        max_deg = _max_abs(errs_deg)
        speed_rows.append((speed, avg_mm, max_mm, avg_deg, max_deg))
        print(
            f"  speed={speed} mm/s: 距離誤差 平均={avg_mm:.1f}mm 最大={max_mm:.1f}mm, 向き誤差 平均={avg_deg:.1f}deg 最大={max_deg:.1f}deg"
        )

    print("")
    print(
        "  (表) 巡航速度 | 距離誤差平均(mm) | 距離誤差最大(mm) | 向き誤差平均(deg) | 向き誤差最大(deg)"
    )
    print("  " + "-" * 75)
    for r in speed_rows:
        print(f"  {r[0]:>8} | {r[1]:>16.1f} | {r[2]:>16.1f} | {r[3]:>18.1f} | {r[4]:>18.1f}")

    # --- 2. 加速度の比較（走り出しのキツさ）---
    print("")
    print(
        f"=== 速度テスト: 加速度の比較（走り出し mm/s^2、巡航は {SPEED_TEST_ACCEL_REF_SPEED} mm/s 固定）==="
    )
    accel_rows = []
    for accel in SPEED_TEST_ACCELERATIONS:
        errs_mm = []
        errs_deg = []
        for _ in range(SPEED_TEST_RUNS):
            await reset_pose(hub, robot)
            await robot.straight(dist, speed=SPEED_TEST_ACCEL_REF_SPEED, acceleration=accel)
            d = robot.distance()
            h = hub.imu.heading()
            errs_mm.append(d - dist)
            errs_deg.append(h - target_heading)
            await robot.straight(-dist, speed=SPEED_TEST_ACCEL_REF_SPEED, acceleration=accel)
        avg_mm = _mean(errs_mm)
        max_mm = _max_abs(errs_mm)
        avg_deg = _mean(errs_deg)
        max_deg = _max_abs(errs_deg)
        accel_rows.append((accel, avg_mm, max_mm, avg_deg, max_deg))
        print(
            f"  accel={accel} mm/s^2: 距離誤差 平均={avg_mm:.1f}mm 最大={max_mm:.1f}mm, 向き誤差 平均={avg_deg:.1f}deg 最大={max_deg:.1f}deg"
        )

    print("")
    print(
        "  (表) 加速度   | 距離誤差平均(mm) | 距離誤差最大(mm) | 向き誤差平均(deg) | 向き誤差最大(deg)"
    )
    print("  " + "-" * 75)
    for r in accel_rows:
        print(f"  {r[0]:>8} | {r[1]:>16.1f} | {r[2]:>16.1f} | {r[3]:>18.1f} | {r[4]:>18.1f}")

    md_lines = [
        "# 速度テスト結果 (straight_speed)",
        "",
        "## 巡航速度の比較",
        "| 速度(mm/s) | 距離誤差平均(mm) | 距離誤差最大(mm) | 向き誤差平均(deg) | 向き誤差最大(deg) |",
        "|------------|------------------|------------------|-------------------|------------------|",
    ]
    for r in speed_rows:
        md_lines.append(f"| {r[0]} | {r[1]:.1f} | {r[2]:.1f} | {r[3]:.1f} | {r[4]:.1f} |")
    md_lines.append("")
    md_lines.append(f"## 加速度（走り出し）の比較 (巡航 {SPEED_TEST_ACCEL_REF_SPEED} mm/s 固定)")
    md_lines.append(
        "| 加速度(mm/s^2) | 距離誤差平均(mm) | 距離誤差最大(mm) | 向き誤差平均(deg) | 向き誤差最大(deg) |"
    )
    md_lines.append(
        "|---------------|------------------|------------------|-------------------|------------------|"
    )
    for r in accel_rows:
        md_lines.append(f"| {r[0]} | {r[1]:.1f} | {r[2]:.1f} | {r[3]:.1f} | {r[4]:.1f} |")
    _write_test_result_md("straight_speed", "\n".join(md_lines))


async def turn_test(hub, robot, left_wheel, right_wheel):
    results = []
    for run_num in range(1, TEST_RUN_COUNT + 1):
        await reset_pose(hub, robot)

        async def motion():
            global stop_logging
            try:
                if TURN_RATE is None:
                    await robot.turn(TURN_ANGLE_DEG)
                else:
                    await robot.turn(TURN_ANGLE_DEG, rate=TURN_RATE)
            finally:
                stop_logging = True

        await _run_with_logger(hub, robot, left_wheel, right_wheel, "turn", motion())

        heading = hub.imu.heading()
        err_deg = heading - TURN_ANGLE_DEG
        results.append((run_num, TURN_ANGLE_DEG, f"{heading:.1f}", f"{err_deg:+.1f}"))
        print(f"  run {run_num}/{TEST_RUN_COUNT}: heading={heading:.1f}deg error={err_deg:+.1f}deg")

    print("=== turn result (誤差の表) ===")
    _print_error_table(
        results,
        ("回", "目標(deg)", "実際(deg)", "誤差(deg)"),
        [4, 8, 10, 10],
    )
    errs = [float(r[3]) for r in results]
    print(f"誤差(deg): 平均={_mean(errs):.1f} 最大絶対値={_max_abs(errs):.1f}")

    md_lines = [
        "# 旋回テスト結果 (turn)",
        "",
        f"- 目標角度: {TURN_ANGLE_DEG}°, 試行回数: {TEST_RUN_COUNT}",
        "",
        "| 回 | 目標(deg) | 実際(deg) | 誤差(deg) |",
        "|----|-----------|-----------|-----------|",
    ]
    for r in results:
        md_lines.append(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} |")
    md_lines.append("")
    md_lines.append(f"- 誤差 平均: {_mean(errs):.1f}°, 最大絶対値: {_max_abs(errs):.1f}°")
    _write_test_result_md("turn", "\n".join(md_lines))


async def curve_test(hub, robot, left_wheel, right_wheel):
    """
    カーブテスト。半径・角度を指定してカーブをN回実行し、
    毎回の「走行距離の誤差」と「向きの誤差」を表で表示する。
    """
    # 理論上の弧の長さ（mm）= 半径の絶対値 × 角度(rad)
    pi = 3.14159265359
    expected_dist_mm = abs(CURVE_RADIUS_MM) * abs(CURVE_ANGLE_DEG) * pi / 180.0
    results = []
    for run_num in range(1, CURVE_TEST_COUNT + 1):
        await reset_pose(hub, robot)

        async def motion():
            global stop_logging
            try:
                if CURVE_SPEED is None:
                    await robot.curve(CURVE_RADIUS_MM, CURVE_ANGLE_DEG)
                else:
                    await robot.curve(CURVE_RADIUS_MM, CURVE_ANGLE_DEG, speed=CURVE_SPEED)
            finally:
                stop_logging = True

        await _run_with_logger(hub, robot, left_wheel, right_wheel, "curve", motion())
        await wait(200)

        dist = robot.distance()
        heading = hub.imu.heading()
        err_mm = dist - expected_dist_mm
        err_deg = heading - CURVE_ANGLE_DEG
        results.append(
            (
                run_num,
                f"{expected_dist_mm:.0f}",
                f"{dist:.1f}",
                f"{err_mm:+.1f}",
                f"{heading:.1f}",
                f"{err_deg:+.1f}",
            )
        )
        print(
            f"  run {run_num}/{CURVE_TEST_COUNT}: dist={dist:.1f}mm err_mm={err_mm:+.1f} heading={heading:.1f}deg err_deg={err_deg:+.1f}"
        )

    print("=== curve result (カーブ誤差の表) ===")
    print(f"  条件: 半径={CURVE_RADIUS_MM}mm 角度={CURVE_ANGLE_DEG}deg 試行{CURVE_TEST_COUNT}回")
    _print_error_table(
        results,
        ("回", "目標距離(mm)", "実際(mm)", "距離誤差(mm)", "向き(deg)", "向き誤差(deg)"),
        [4, 12, 10, 12, 10, 12],
    )
    dist_errs = [float(r[3]) for r in results]
    deg_errs = [float(r[5]) for r in results]
    print(f"距離誤差(mm): 平均={_mean(dist_errs):.1f} 最大絶対値={_max_abs(dist_errs):.1f}")
    print(f"向き誤差(deg): 平均={_mean(deg_errs):.1f} 最大絶対値={_max_abs(deg_errs):.1f}")

    md_lines = [
        "# カーブテスト結果 (curve)",
        "",
        f"条件: 半径={CURVE_RADIUS_MM}mm 角度={CURVE_ANGLE_DEG}deg 試行{CURVE_TEST_COUNT}回",
        "",
        "| 回 | 目標距離(mm) | 実際(mm) | 距離誤差(mm) | 向き(deg) | 向き誤差(deg) |",
        "|----|--------------|----------|--------------|-----------|---------------|",
    ]
    for r in results:
        md_lines.append(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} |")
    md_lines.append("")
    md_lines.append(
        f"距離誤差 平均={_mean(dist_errs):.1f}mm 最大絶対値={_max_abs(dist_errs):.1f}mm"
    )
    md_lines.append(
        f"向き誤差 平均={_mean(deg_errs):.1f}deg 最大絶対値={_max_abs(deg_errs):.1f}deg"
    )
    _write_test_result_md("curve", "\n".join(md_lines))


async def turn_accuracy_test(hub, robot, left_wheel, right_wheel):
    """
    旋回正確性を最優先にした測定（トレッド比最適化用）。
    目標: 平均角度誤差≤2.0°, SD≤1.0°, 横ズレ≤10mm（目安）。
    90°×N90回 + 180°×N180回を実施し、KPI・合格判定・スコアを出力する。
    """

    def run_one_turn(target_deg, run_label):
        async def motion():
            global stop_logging
            try:
                if TURN_ACCURACY_RATE is None:
                    await robot.turn(target_deg)
                else:
                    await robot.turn(target_deg, rate=TURN_ACCURACY_RATE)
            finally:
                stop_logging = True

        return motion

    results_90 = []
    results_180 = []

    # ----- 90°旋回 × N -----
    for i in range(TURN_ACCURACY_90_COUNT):
        await reset_pose(hub, robot)
        await wait(TURN_ACCURACY_WAIT_AFTER_RESET_MS)
        await _run_with_logger(
            hub, robot, left_wheel, right_wheel, "turn_90", run_one_turn(90, i + 1)()
        )
        await wait(TURN_ACCURACY_SETTLE_MS)
        heading = hub.imu.heading()
        drift_mm = robot.distance()
        err = heading - 90
        results_90.append(
            {"run": i + 1, "target": 90, "actual": heading, "error_deg": err, "drift_mm": drift_mm}
        )
        if i < TURN_ACCURACY_90_COUNT - 1:
            await wait(TURN_ACCURACY_WAIT_BETWEEN_RUNS_MS)

    # ----- 180°旋回 × N -----
    for i in range(TURN_ACCURACY_180_COUNT):
        await reset_pose(hub, robot)
        await wait(TURN_ACCURACY_WAIT_AFTER_RESET_MS)
        await _run_with_logger(
            hub, robot, left_wheel, right_wheel, "turn_180", run_one_turn(180, i + 1)()
        )
        await wait(TURN_ACCURACY_SETTLE_MS)
        heading = hub.imu.heading()
        drift_mm = robot.distance()
        err = heading - 180
        results_180.append(
            {"run": i + 1, "target": 180, "actual": heading, "error_deg": err, "drift_mm": drift_mm}
        )
        if i < TURN_ACCURACY_180_COUNT - 1:
            await wait(TURN_ACCURACY_WAIT_BETWEEN_RUNS_MS)

    # ----- 90°結果表 -----
    print("=== 旋回正確性テスト (Turning Accuracy First) ===")
    print(f"条件: 90°×{TURN_ACCURACY_90_COUNT}回, 180°×{TURN_ACCURACY_180_COUNT}回")
    print("")
    print("--- 90°旋回の誤差 ---")
    rows90 = [
        (
            r["run"],
            r["target"],
            f"{r['actual']:.1f}",
            f"{r['error_deg']:+.1f}",
            f"{r['drift_mm']:.1f}",
        )
        for r in results_90
    ]
    _print_error_table(
        rows90, ("回", "目標(deg)", "実際(deg)", "誤差(deg)", "旋回後ずれ(mm)"), [4, 8, 10, 10, 12]
    )

    errs_90 = [r["error_deg"] for r in results_90]
    abs_errs_90 = [abs(e) for e in errs_90]
    drift_90 = [abs(r["drift_mm"]) for r in results_90]
    mean_abs_90 = _mean(abs_errs_90)
    sd_90 = _std(errs_90)
    overshoot_90 = max(0, max(errs_90)) if errs_90 else 0
    mean_drift_90 = _mean(drift_90) if drift_90 else 0

    print("")
    print("--- 180°旋回の誤差 ---")
    rows180 = [
        (
            r["run"],
            r["target"],
            f"{r['actual']:.1f}",
            f"{r['error_deg']:+.1f}",
            f"{r['drift_mm']:.1f}",
        )
        for r in results_180
    ]
    _print_error_table(
        rows180, ("回", "目標(deg)", "実際(deg)", "誤差(deg)", "旋回後ずれ(mm)"), [4, 8, 10, 10, 12]
    )

    errs_180 = [r["error_deg"] for r in results_180]
    abs_errs_180 = [abs(e) for e in errs_180]
    drift_180 = [abs(r["drift_mm"]) for r in results_180]
    mean_abs_180 = _mean(abs_errs_180)
    sd_180 = _std(errs_180)
    overshoot_180 = max(0, max(errs_180)) if errs_180 else 0
    mean_drift_180 = _mean(drift_180) if drift_180 else 0

    # ----- 全体KPI（90°を主、180°を参考）-----
    print("")
    print("=== 旋回正確性 KPI（主目標: 90°） ===")
    print(f"  平均角度誤差 |目標−実測|: {mean_abs_90:.2f}°  (合格: ≤{TURN_ACCURACY_MEAN_MAX_DEG}°)")
    print(f"  誤差の標準偏差 SD:         {sd_90:.2f}°  (合格: ≤{TURN_ACCURACY_SD_MAX_DEG}°)")
    print(
        f"  旋回後ずれ(目安):          {mean_drift_90:.1f} mm (合格: ≤{TURN_ACCURACY_DRIFT_MAX_MM}mm)"
    )
    print(
        f"  オーバーシュート(最大):    {overshoot_90:.2f}°  (合格: ≤{TURN_ACCURACY_OVERSUHOOT_MAX_DEG}°)"
    )
    # 注: 複数行f-stringはmpy-crossでSyntaxErrorになるため .format() を使用
    print("")
    _msg = (
        "  180deg参考: 平均|誤差|={:.2f}deg SD={:.2f}deg "
        "旋回後ずれ={:.1f}mm オーバーシュート={:.2f}deg"
    )
    print(_msg.format(mean_abs_180, sd_180, mean_drift_180, overshoot_180))

    ok_mean = mean_abs_90 <= TURN_ACCURACY_MEAN_MAX_DEG
    ok_sd = sd_90 <= TURN_ACCURACY_SD_MAX_DEG
    ok_drift = mean_drift_90 <= TURN_ACCURACY_DRIFT_MAX_MM
    ok_overshoot = overshoot_90 <= TURN_ACCURACY_OVERSUHOOT_MAX_DEG
    print("")
    print("--- 合格判定 ---")
    print(f"  平均角度誤差: {'✓ 合格' if ok_mean else '✗ 不合格'}")
    print(f"  SD:           {'✓ 合格' if ok_sd else '✗ 不合格'}")
    print(f"  旋回後ずれ:   {'✓ 合格' if ok_drift else '✗ 不合格'}")
    print(f"  オーバーシュート: {'✓ 合格' if ok_overshoot else '✗ 不合格'}")
    all_ok = ok_mean and ok_sd and ok_drift and ok_overshoot
    print(f"  総合: {'✓ 全項目合格' if all_ok else '✗ 要調整'}")

    # 目的関数スコア（最小化）。横ズレは 10mm=1 でdegに近いスケールに
    score = (
        TURN_ACCURACY_W1 * mean_abs_90
        + TURN_ACCURACY_W2 * sd_90
        + TURN_ACCURACY_W3 * (mean_drift_90 / 10.0)
    )
    print("")
    print("--- 最適化用スコア（小さいほど良い）---")
    print(
        f"  Score = {TURN_ACCURACY_W1}*平均誤差 + {TURN_ACCURACY_W2}*SD + {TURN_ACCURACY_W3}*ずれ/10 = {score:.3f}"
    )
    print("")
    print(f"  >> 比較用スコア: {score:.3f}  （タイヤ位置ごとにこの値を記録し、最小の位置を採用）")

    # docs に結果を Markdown で出力
    md_lines = [
        "# 旋回正確性テスト結果 (turn_accuracy)",
        "",
        f"- 条件: 90°×{TURN_ACCURACY_90_COUNT}回, 180°×{TURN_ACCURACY_180_COUNT}回",
        "",
        "## 90°旋回",
        "| 回 | 目標(deg) | 実際(deg) | 誤差(deg) | 旋回後ずれ(mm) |",
        "|----|-----------|-----------|-----------|----------------|",
    ]
    for r in results_90:
        md_lines.append(
            f"| {r['run']} | {r['target']} | {r['actual']:.1f} | {r['error_deg']:+.1f} | {r['drift_mm']:.1f} |"
        )
    md_lines.extend(
        [
            "",
            "## 180°旋回",
            "| 回 | 目標(deg) | 実際(deg) | 誤差(deg) | 旋回後ずれ(mm) |",
            "|----|-----------|-----------|-----------|----------------|",
        ]
    )
    for r in results_180:
        md_lines.append(
            f"| {r['run']} | {r['target']} | {r['actual']:.1f} | {r['error_deg']:+.1f} | {r['drift_mm']:.1f} |"
        )
    md_lines.extend(
        [
            "",
            "## KPI（90°）",
            f"- 平均角度誤差: {mean_abs_90:.2f}° (合格: ≤{TURN_ACCURACY_MEAN_MAX_DEG}°)",
            f"- SD: {sd_90:.2f}° (合格: ≤{TURN_ACCURACY_SD_MAX_DEG}°)",
            f"- 旋回後ずれ: {mean_drift_90:.1f} mm (合格: ≤{TURN_ACCURACY_DRIFT_MAX_MM}mm)",
            f"- オーバーシュート: {overshoot_90:.2f}° (合格: ≤{TURN_ACCURACY_OVERSUHOOT_MAX_DEG}°)",
            "",
            "## 合格判定",
            f"- 平均角度誤差: {'✓ 合格' if ok_mean else '✗ 不合格'}",
            f"- SD: {'✓ 合格' if ok_sd else '✗ 不合格'}",
            f"- 旋回後ずれ: {'✓ 合格' if ok_drift else '✗ 不合格'}",
            f"- オーバーシュート: {'✓ 合格' if ok_overshoot else '✗ 不合格'}",
            f"- **総合: {'✓ 全項目合格' if all_ok else '✗ 要調整'}**",
            "",
            f"## 比較用スコア: {score:.3f} （小さいほど良い）",
        ]
    )
    _write_test_result_md("turn_accuracy", "\n".join(md_lines))


async def square_test(hub, robot, left_wheel, right_wheel):
    await reset_pose(hub, robot)

    async def motion():
        global stop_logging
        try:
            for i in range(4):
                print(f"--- square leg {i + 1}/4 ---")
                await robot.straight(STRAIGHT_DISTANCE_MM)
                await robot.turn(90)
        finally:
            stop_logging = True

    await _run_with_logger(hub, robot, left_wheel, right_wheel, "square", motion())

    dist = robot.distance()
    heading = hub.imu.heading()
    print("=== square result ===")
    print(f"final_dist_mm={dist:.1f} (should be near 0 if it returned to start)")
    print(f"final_heading_deg={heading:.1f} (should be near 0 or 360)")

    md_lines = [
        "# 四角形テスト結果 (square)",
        "",
        f"- 1辺: {STRAIGHT_DISTANCE_MM} mm, 90°×4",
        "",
        f"- 最終距離: {dist:.1f} mm (スタートに戻っていれば 0 に近い)",
        f"- 最終向き: {heading:.1f}° (0 または 360 に近い)",
    ]
    _write_test_result_md("square", "\n".join(md_lines))


def _mean(vals):
    if not vals:
        return 0.0
    return sum(vals) / float(len(vals))


def _max_abs(vals):
    if not vals:
        return 0.0
    m = 0.0
    for v in vals:
        a = abs(v)
        if a > m:
            m = a
    return m


def _std(vals):
    """標本標準偏差（不偏分散の平方根）。再現性の指標。"""
    if not vals or len(vals) < 2:
        return 0.0
    n = len(vals)
    mean = sum(vals) / float(n)
    var = sum((x - mean) ** 2 for x in vals) / float(n - 1)
    return var**0.5


def _pad_right(s, width):
    """文字列 s を幅 width で右詰め（左にスペース）。rjust が無い環境用。"""
    s = str(s)
    n = width - len(s)
    return (" " * n + s) if n > 0 else s


def _write_test_result_md(test_mode, md_content):
    """テスト結果を docs/test_result_{mode}_latest.md に保存する。Pybricks環境ではスキップ。"""
    try:
        import os

        docs_dir = "docs"
        try:
            os.makedirs(docs_dir)
        except OSError:
            pass
        path = os.path.join(docs_dir, "test_result_" + test_mode + "_latest.md")
        with open(path, "w") as f:
            f.write(md_content)
        print("\n# テスト結果を保存しました: " + path)
    except Exception as e:
        print("\n# テスト結果の保存に失敗しました: " + str(e))


def _print_error_table(rows, headers, col_widths=None):
    """ヘッダーと行のリストから表を描画する。"""
    if not rows:
        return
    num_cols = len(headers)
    if col_widths is None:
        col_widths = [max(8, len(str(h))) for h in headers]
    else:
        col_widths = list(col_widths)
    for j in range(num_cols):
        col_widths[j] = max(col_widths[j] if j < len(col_widths) else 8, len(str(headers[j])))
    for row in rows:
        for i, cell in enumerate(row):
            if i < num_cols:
                w = len(str(cell))
                if i < len(col_widths) and w > col_widths[i]:
                    col_widths[i] = w
    # ヘッダー
    header_line = " | ".join(_pad_right(h, col_widths[i]) for i, h in enumerate(headers))
    sep = "-+-".join("-" * col_widths[i] for i in range(len(headers)))
    print(header_line)
    print(sep)
    for row in rows:
        line = " | ".join(
            _pad_right(row[i] if i < len(row) else "", col_widths[i]) for i in range(num_cols)
        )
        print(line)


async def repeat_back_forth_test(hub, robot, left_wheel, right_wheel):
    """
    直進 +D mm / 後退 -D mm を N 回繰り返す。

    注意: ここでの距離は DriveBase/エンコーダ由来なので、床での空転があると
    「実際の位置ズレ」と一致しない場合があります。向き(gyro)のズレは確認しやすいです。
    """
    await reset_pose(hub, robot)

    results = []

    async def motion():
        global stop_logging
        try:
            for i in range(REPEAT_COUNT):
                # forward
                dist0 = robot.distance()
                head0 = hub.imu.heading()

                if REPEAT_SPEED is None:
                    await robot.straight(REPEAT_DISTANCE_MM)
                else:
                    await robot.straight(REPEAT_DISTANCE_MM, speed=REPEAT_SPEED)
                robot.stop()
                await wait(REPEAT_PAUSE_MS)

                dist1 = robot.distance()
                head1 = hub.imu.heading()
                fwd_delta = dist1 - dist0
                fwd_err = fwd_delta - REPEAT_DISTANCE_MM
                fwd_head_delta = head1 - head0

                # backward
                dist2_0 = robot.distance()
                head2_0 = hub.imu.heading()

                if REPEAT_SPEED is None:
                    await robot.straight(-REPEAT_DISTANCE_MM)
                else:
                    await robot.straight(-REPEAT_DISTANCE_MM, speed=REPEAT_SPEED)
                robot.stop()
                await wait(REPEAT_PAUSE_MS)

                dist2 = robot.distance()
                head2 = hub.imu.heading()
                back_delta = dist2 - dist2_0  # should be -D
                back_err = back_delta + REPEAT_DISTANCE_MM
                back_head_delta = head2 - head2_0

                results.append(
                    {
                        "cycle": i + 1,
                        "fwd_delta_mm": float(fwd_delta),
                        "fwd_err_mm": float(fwd_err),
                        "fwd_head_delta_deg": float(fwd_head_delta),
                        "back_delta_mm": float(back_delta),
                        "back_err_mm": float(back_err),
                        "back_head_delta_deg": float(back_head_delta),
                        "end_dist_mm": float(dist2),
                        "end_heading_deg": float(head2),
                        "end_left_deg": float(left_wheel.angle()),
                        "end_right_deg": float(right_wheel.angle()),
                    }
                )
        finally:
            stop_logging = True

    if REPEAT_WITH_LOGGER:
        await _run_with_logger(hub, robot, left_wheel, right_wheel, "repeat_back_forth", motion())
    else:
        await motion()

    # summary
    print("=== repeat back/forth result (誤差の表) ===")
    print(f"target: +{REPEAT_DISTANCE_MM}mm then -{REPEAT_DISTANCE_MM}mm, cycles={REPEAT_COUNT}")
    table_rows = []
    for r in results:
        table_rows.append(
            (
                r["cycle"],
                f"{r['fwd_err_mm']:+.1f}",
                f"{r['fwd_head_delta_deg']:+.1f}",
                f"{r['back_err_mm']:+.1f}",
                f"{r['back_head_delta_deg']:+.1f}",
                f"{r['end_dist_mm']:.1f}",
                f"{r['end_heading_deg']:.1f}",
            )
        )
    _print_error_table(
        table_rows,
        (
            "回",
            "直進誤差(mm)",
            "直進向き(deg)",
            "後退誤差(mm)",
            "後退向き(deg)",
            "終了dist(mm)",
            "終了向き(deg)",
        ),
        [4, 12, 12, 12, 12, 12, 12],
    )
    print("(CSV)")
    print(
        "cycle,fwd_delta_mm,fwd_err_mm,fwd_dhead_deg,back_delta_mm,back_err_mm,back_dhead_deg,end_dist_mm,end_head_deg"
    )
    for r in results:
        print(
            f"{r['cycle']},{r['fwd_delta_mm']:.1f},{r['fwd_err_mm']:.1f},{r['fwd_head_delta_deg']:.1f},{r['back_delta_mm']:.1f},{r['back_err_mm']:.1f},{r['back_head_delta_deg']:.1f},{r['end_dist_mm']:.1f},{r['end_heading_deg']:.1f}"
        )

    fwd_errs = [r["fwd_err_mm"] for r in results]
    back_errs = [r["back_err_mm"] for r in results]
    end_dists = [r["end_dist_mm"] for r in results]
    end_heads = [r["end_heading_deg"] for r in results]

    print("--- aggregates ---")
    print(f"fwd_err_mm: mean={_mean(fwd_errs):.1f} max_abs={_max_abs(fwd_errs):.1f}")
    print(f"back_err_mm: mean={_mean(back_errs):.1f} max_abs={_max_abs(back_errs):.1f}")
    print(f"end_dist_mm (encoder): mean={_mean(end_dists):.1f} max_abs={_max_abs(end_dists):.1f}")
    if end_heads:
        print(f"end_heading_deg (gyro): last={end_heads[-1]:.1f} max_abs={_max_abs(end_heads):.1f}")
    else:
        print("end_heading_deg (gyro): (no data)")

    md_lines = [
        "# 往復テスト結果 (repeat)",
        "",
        f"- 目標: +{REPEAT_DISTANCE_MM}mm → -{REPEAT_DISTANCE_MM}mm, サイクル数: {REPEAT_COUNT}",
        "",
        "| 回 | 直進誤差(mm) | 直進向き(deg) | 後退誤差(mm) | 後退向き(deg) | 終了dist(mm) | 終了向き(deg) |",
        "|----|--------------|---------------|--------------|---------------|--------------|---------------|",
    ]
    for r in results:
        md_lines.append(
            "| "
            + str(r["cycle"])
            + " | "
            + "{:+.1f}".format(r["fwd_err_mm"])
            + " | "
            + "{:+.1f}".format(r["fwd_head_delta_deg"])
            + " | "
            + "{:+.1f}".format(r["back_err_mm"])
            + " | "
            + "{:+.1f}".format(r["back_head_delta_deg"])
            + " | "
            + "{:.1f}".format(r["end_dist_mm"])
            + " | "
            + "{:.1f}".format(r["end_heading_deg"])
            + " |"
        )
    mean_fwd = _mean(fwd_errs)
    max_fwd = _max_abs(fwd_errs)
    mean_back = _mean(back_errs)
    max_back = _max_abs(back_errs)
    mean_dist = _mean(end_dists)
    max_dist = _max_abs(end_dists)
    md_lines.extend(
        [
            "",
            "## 集計",
            f"- 直進誤差: 平均={mean_fwd:.1f} mm, 最大絶対値={max_fwd:.1f} mm",
            f"- 後退誤差: 平均={mean_back:.1f} mm, 最大絶対値={max_back:.1f} mm",
            f"- 終了距離(encoder): 平均={mean_dist:.1f} mm, 最大絶対値={max_dist:.1f} mm",
        ]
    )
    if end_heads:
        last_head = end_heads[-1]
        max_head = _max_abs(end_heads)
        md_lines.append(
            f"- 終了向き(gyro): 最終={last_head:.1f} deg, 最大絶対値={max_head:.1f} deg"
        )
    _write_test_result_md("repeat", "\n".join(md_lines))


async def run(hub, robot, left_wheel, right_wheel, left_lift, right_lift):
    #######################################
    # ここにロボットの動作を記述してください
    if TEST_MODE == "turn_accuracy":
        await turn_accuracy_test(hub, robot, left_wheel, right_wheel)
    elif TEST_MODE == "straight":
        await straight_test(hub, robot, left_wheel, right_wheel)
    elif TEST_MODE == "curve":
        await curve_test(hub, robot, left_wheel, right_wheel)
    elif TEST_MODE == "speed":
        await straight_speed_test(hub, robot, left_wheel, right_wheel)
    elif TEST_MODE == "turn":
        await turn_test(hub, robot, left_wheel, right_wheel)
    elif TEST_MODE == "square":
        await square_test(hub, robot, left_wheel, right_wheel)
    elif TEST_MODE == "repeat":
        await repeat_back_forth_test(hub, robot, left_wheel, right_wheel)
    elif TEST_MODE == "all":
        # 狭い範囲：旋回正確性 → 直進 → カーブ の3種のみ
        await turn_accuracy_test(hub, robot, left_wheel, right_wheel)
        await wait(500)
        await straight_test(hub, robot, left_wheel, right_wheel)
        await wait(500)
        await curve_test(hub, robot, left_wheel, right_wheel)
    else:
        print(f"ERROR: TEST_MODE が不正です: {TEST_MODE}")
    #######################################

    # ロボットを停止
    robot.stop()
    print("# 走行完了！")


# ===== 単体テスト用（このファイルを直接実行した場合） =====
if __name__ == "__main__":
    hub, robot, left_wheel, right_wheel, left_lift, right_lift = initialize_robot()
    run_task(run(hub, robot, left_wheel, right_wheel, left_lift, right_lift))
