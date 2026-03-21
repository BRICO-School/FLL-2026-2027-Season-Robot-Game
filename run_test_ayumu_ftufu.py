from pybricks.hubs import PrimeHub
from pybricks.parameters import Port, Axis, Direction, Color, Stop
from pybricks.pupdevices import Motor
from pybricks.robotics import DriveBase
from pybricks.tools import wait, multitask, run_task, StopWatch
from setup import initialize_robot


#######################################
# ここにロボットの動作を記述してください
# ---ハブ・モーターの設定---
hub = PrimeHub()
left_motor = Motor(Port.F, positive_direction=Direction.COUNTERCLOCKWISE)
right_motor = Motor(Port.B)


# ---ロボットのサイズ設定--
WHEEL_DIAMETER = 62.4  # タイヤの直径（mm）
AXLE_TRACK = 123.0  # 左右タイヤの中心間距離（mm）
# ---変えられるところ---
DRIVE_SPEED = 100  # 走行速度(mm/s)
LOG_INTERVAL_MS = 100  # 走行ログの間隔（ミリ秒）
COURSE_DISTANCE = 200  # 前進させる距離（mm）
# === ログ考察（205〜207mm・左に0.3〜1.1degずれ）===
# ・距離: 毎回5〜7mmオーバー → DISTANCE_CORRECTION で打ち消す
# ・角度: 常に左へずれる → 右モーターが強め／左が弱めの可能性。DRIFT_BIAS で常時わずかに右へ補正
# ・左右の差: 走行ごとにばらつきあり。直進バランスの指標として継続ログ推奨
# 今後の候補: (1)距離補正を有効化 (2)ドリフトバイアス追加 (3)WHEEL_DIAMETER/AXLE_TRACK実測 (4)ANGLE_CORRECTION_GAIN微調整
# 誤差を減らすための補正（実測が目標より大きいときは 目標/実測 に近づける）
DISTANCE_CORRECTION = 200 / 206  # 実測206mm前後→目標200mmに近づける（1.0でオフ）
# 直進時の角度ズレ補正の強さ（0=オフ。2〜5でゆるく補正。大きすぎると振動する）
ANGLE_CORRECTION_GAIN = 4  # 左ずれ傾向のためやや強めに
# 常時かける「右向き」補正（左にずれる傾向があるときプラスで打ち消す。deg/s）
DRIFT_BIAS = 2.0
# 距離補正をかけた目標（DISTANCE_CORRECTION を変えるとここが変わる）
effective_target = COURSE_DISTANCE * DISTANCE_CORRECTION
#  ---ドライブベースの作成---
robot = DriveBase(left_motor, right_motor, WHEEL_DIAMETER, AXLE_TRACK)

# ---タイマ---
watch = StopWatch()

# ===== 走行開始　=====
print("===テスト開始＝＝＝")
print("走行速度:", DRIVE_SPEED, "mm/s")
print("タイヤ間距離:", AXLE_TRACK, "mm")
print("距離補正係数:", DISTANCE_CORRECTION, "→ 目標", effective_target, "mmで停止")
print("角度補正ゲイン:", ANGLE_CORRECTION_GAIN)
print("ドリフトバイアス:", DRIFT_BIAS, "deg/s")

# まっすぐ走る（走行中にログ出力）
# くねつき防止: straight_acceleration を低めにすると直進が安定する
robot.settings(straight_speed=DRIVE_SPEED, straight_acceleration=80)
watch.reset()
start_dist = robot.distance()
start_angle = robot.angle()
# 角度ズレ補正: turn_rate でまっすぐに戻す
turn_rate = 0

print("--- 走行ログ（経過ms, 走行距離mm, 瞬間速度, 角度, 左ずれ, 右ずれ, 左右の差）---")
print("経過_ms,走行距離_mm,瞬間速度_mm_s,角度_deg,左へのずれ_deg,右へのずれ_deg,左右の差_deg")
last_d = 0.0
final_dist = 0.0
final_angle = start_angle
while True:
    wait(LOG_INTERVAL_MS)
    elapsed_ms = watch.time()
    d = robot.distance() - start_dist
    angle_deg = robot.angle()
    angle_error = angle_deg - start_angle
    # 左へのずれ（正=左に曲がった）、右へのずれ（正=右に曲がった）
    left_drift = angle_error if angle_error > 0 else 0
    right_drift = -angle_error if angle_error < 0 else 0
    # 左右モーターの回転角の差（直進なら近い値になる）
    lr_diff = left_motor.angle() - right_motor.angle()
    # 角度ズレを補正（開始角度からの差に比例＋左ずれ傾向をDRIFT_BIASで右に打ち消し）
    if ANGLE_CORRECTION_GAIN != 0:
        turn_rate = -ANGLE_CORRECTION_GAIN * angle_error + DRIFT_BIAS
    else:
        turn_rate = DRIFT_BIAS
    robot.drive(DRIVE_SPEED, turn_rate)
    interval_s = LOG_INTERVAL_MS / 1000.0
    speed_mm_s = (d - last_d) / interval_s if interval_s > 0 else 0.0
    last_d = d
    print(
        elapsed_ms,
        ",",
        d,
        ",",
        speed_mm_s,
        ",",
        angle_deg,
        ",",
        left_drift,
        ",",
        right_drift,
        ",",
        lr_diff,
    )
    if d >= effective_target:
        final_dist = d
        final_angle = angle_deg
        break

robot.stop()

# 結果を表示
elapsed = watch.time()
distance = robot.distance()
print("--- 走行ログ終了 ---")
print("===テスト終了 ===")
print("走行時間:", elapsed, "ミリ秒")
print("走行時間:", elapsed / 1000, "秒")
print("走行距離:", distance, "mm")
print("走行距離(目標):", COURSE_DISTANCE, "mm")
print("走行距離(実測):", final_dist, "mm")
print("開始角度:", start_angle, "deg")
print("終了角度:", final_angle, "deg")
print("角度変化(ズレ):", final_angle - start_angle, "deg")
angle_error_final = final_angle - start_angle
print("左へのずれ:", angle_error_final if angle_error_final > 0 else 0, "deg")
print("右へのずれ:", -angle_error_final if angle_error_final < 0 else 0, "deg")
print("左右の差(モーター角):", left_motor.angle() - right_motor.angle(), "deg")


#######################################

# ロボットを停止
robot.stop()
print("# 走行完了！")
