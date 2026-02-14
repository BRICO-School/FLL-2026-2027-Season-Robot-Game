from pybricks.hubs import PrimeHub
from pybricks.parameters import Port, Axis, Direction, Color, Stop
from pybricks.pupdevices import Motor
from pybricks.robotics import DriveBase
from pybricks.tools import wait, multitask, run_task, StopWatch
from setup import initialize_robot


# ===== テスト設定（ここだけ変えればOK）=====
# 実行したいテストを選ぶ:
# - "straight": 直進テスト
#   距離がズレるか、まっすぐ進めるか（向きがズレないか）を確認します。
#   例: 400mm進ませて、最後の dist_mm と heading_deg を見る。
# - "turn": 旋回テスト
#   角度がズレるか（指定した角度に回れるか）を確認します。
#   例: 90度回して、最後の heading_deg の誤差を見る。
# - "square": 四角形テスト（直進+90度回転を4回）
#   「直進のズレ」と「回転のズレ」が積み重なるとどうなるかを確認します。
#   4回繰り返した後に、dist_mm が0に近いか、heading_deg が0付近に戻るかを見る。
# - "repeat": 直進20cm→後進20cmをN回
#   1往復ごとの「距離のズレ（mm）」と「向きのズレ（deg）」をまとめて確認します。
# - "all": 全部
TEST_MODE = "repeat"  # 前進→後進を20回

# ログを出す間隔（ミリ秒）
LOG_INTERVAL_MS = 100

# 直進テスト（mm）
STRAIGHT_DISTANCE_MM = 400
STRAIGHT_SPEED = None  # 例: 300（mm/s）。Noneならデフォルト

# 回転テスト（deg）
TURN_ANGLE_DEG = 90
TURN_RATE = None  # 例: 200（deg/s）。Noneならデフォルト

# テスト実行回数（直進・旋回テストをこの回数繰り返し、誤差を表にまとめる）
TEST_RUN_COUNT = 20

# 往復テスト（mm / 回数）
REPEAT_DISTANCE_MM = 200
REPEAT_COUNT = 20  # 試行回数（多いほどズレ傾向が見えやすいが、時間は長くなる）
REPEAT_SPEED = None  # 例: 300（mm/s）。Noneならデフォルト
REPEAT_PAUSE_MS = 150  # 1動作ごとの停止後に少し待つ（慣性/振動の影響を減らす）
REPEAT_WITH_LOGGER = False  # Trueにすると往復中もLOG_INTERVAL_MS間隔でログを出す


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

    print("=== straight result (誤差の表) ===")
    _print_error_table(
        results,
        ("回", "目標(mm)", "実際(mm)", "誤差(mm)", "向き(deg)"),
        [4, 8, 10, 10, 10],
    )
    errs = [float(r[3]) for r in results]
    print(f"誤差(mm): 平均={_mean(errs):.1f} 最大絶対値={_max_abs(errs):.1f}")


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


def _pad_right(s, width):
    """文字列 s を幅 width で右詰め（左にスペース）。rjust が無い環境用。"""
    s = str(s)
    n = width - len(s)
    return (" " * n + s) if n > 0 else s


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


async def run(hub, robot, left_wheel, right_wheel, left_lift, right_lift):
    #######################################
    # ここにロボットの動作を記述してください
    if TEST_MODE == "straight":
        await straight_test(hub, robot, left_wheel, right_wheel)
    elif TEST_MODE == "turn":
        await turn_test(hub, robot, left_wheel, right_wheel)
    elif TEST_MODE == "square":
        await square_test(hub, robot, left_wheel, right_wheel)
    elif TEST_MODE == "repeat":
        await repeat_back_forth_test(hub, robot, left_wheel, right_wheel)
    elif TEST_MODE == "all":
        await straight_test(hub, robot, left_wheel, right_wheel)
        await wait(500)
        await turn_test(hub, robot, left_wheel, right_wheel)
        await wait(500)
        await square_test(hub, robot, left_wheel, right_wheel)
        await wait(500)
        await repeat_back_forth_test(hub, robot, left_wheel, right_wheel)
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
