"""
【モーターで回ったあと、手で定規に合わせ直して「本当のズレ」をジャイロで読む】（2026-09-17）

角の位置をものさしで読むかわりに、ジャイロを分度器として使う。
 1. 機体の左側面を、マットに固定した定規にぴったり当てて置き、手を離して実行する
 2. モーターで右回りに TURNS 周まわって止まる（MODE="spin" は止まらずに / "steps" は 90° ずつ）
 3. ピッと鳴ったら、機体を手でそっと回して、始めと同じ面を定規にぴったり当て直し、手を離す
    （ズレていないように見えても、いちど定規に当て直す）
 4. 3 秒じっとしていると結果が出る

読めるもの:
  ・止まった時のジャイロ h1 と、定規に合わせ直した時のジャイロ h2
  ・h2 − h1 ＝ モーターで回った結果の「本当の回り足りなさ（＋）／回りすぎ（−）」
  ・h2 ÷ 周回数 ＝ モーターで回ったときの「ジャイロの 1 周の読み」。手で回したときの 361.8 と同じなら、
    ジャイロの目盛りは回し方に依らない（＝ズレのばらつきはジャイロのせいではない）

ハブの設定は書きかえない。

【更新履歴】
- 2026-09-17: 旋回時のズレとジャイロ精度を定規で測定するスクリプトを追加した
- 2026-09-17: ビープ音の呼び出しを周波数と長さを指定した非同期処理に変更した。
- 2026-09-17: 旋回チェックで回転速度を指定できるようにした
- 2026-09-17: 定規当て直し案内のライト点灯と待機時間の延長および当て直し忘れ警告を追加した
- 2026-09-17: 旋回テストで角度補正の有無を指定できるようにした。
- 2026-09-17: 動作前後のジャイロ情報や各軸の回転量を出力するログを追加した
"""

from pybricks.parameters import Axis, Color
from pybricks.tools import StopWatch, run_task, wait
from setup import initialize_robot

TURNS = 5
MODE = "spin"  # "spin" / "steps"
CORRECT = False  # True なら Robot.turn() の回り足りなさの補正（角度×GYRO_TURN_SCALE）を入れて回る
RATE = None  # 回転速度 (deg/s)。None なら setup.py の既定（250）


async def run(hub, robot, left_wheel, right_wheel, left_lift, right_lift):
    while not hub.imu.ready():
        await wait(100)
    hub.imu.reset_heading(0)
    robot.reset()
    await wait(500)
    # 手がかり集め: 走る前の傾き・静止時の角速度・軸ごとの回転
    print("# imu.settings:", hub.imu.settings())
    print(
        "# 前: tilt",
        hub.imu.tilt(),
        "/ 角速度",
        hub.imu.angular_velocity(),
        "/ 加速度",
        hub.imu.acceleration(),
    )
    rx0 = hub.imu.rotation(Axis.X)
    ry0 = hub.imu.rotation(Axis.Y)
    rz0 = hub.imu.rotation(Axis.Z)
    if MODE == "spin":
        await robot.turn(360 * TURNS, rate=RATE, correct=CORRECT)
    else:
        for _ in range(TURNS * 4):
            await robot.turn(90, rate=RATE, correct=CORRECT)
            await wait(300)
    await wait(1000)
    h1 = hub.imu.heading()
    print("# 後: tilt", hub.imu.tilt(), "/ 角速度", hub.imu.angular_velocity())
    print(
        "# 軸ごとの回転 X/Y/Z:",
        round(hub.imu.rotation(Axis.X) - rx0, 2),
        round(hub.imu.rotation(Axis.Y) - ry0, 2),
        round(hub.imu.rotation(Axis.Z) - rz0, 2),
        "/ heading:",
        round(h1, 2),
    )
    robot.stop()  # モーターの力を抜く（手で回せるように）
    print(
        "# MODE:",
        MODE,
        "/ 回転速度:",
        RATE,
        "/ 補正:",
        CORRECT,
        "/ 命令:",
        360 * TURNS,
        "度 / 止まった時のジャイロ h1:",
        round(h1, 2),
        "度",
    )
    hub.light.on(Color.GREEN)  # 音が聞こえなくても分かるように、ハブのライトを緑にする
    print(
        "# ★いま★ ライトが緑になったら（ピーと鳴ったら）、手で定規にぴったり当て直して、手を離してね"
    )
    hub.speaker.volume(100)
    await hub.speaker.beep(frequency=500, duration=600)

    total = StopWatch()
    still = StopWatch()
    await wait(1500)  # 手を伸ばす時間
    still.reset()
    while True:
        if not hub.imu.stationary():
            still.reset()
        if total.time() > 8000 and still.time() > 3000:  # 少なくとも 8 秒は待つ
            break
        await wait(20)
    h2 = hub.imu.heading()
    hub.light.on(Color.BLUE)
    await hub.speaker.beep(frequency=1000, duration=200)
    if abs(h2 - h1) < 0.3:
        print("# ！ 合わせ直しでほとんど動いていません。当て直しを忘れていたら、この回は無効です")
    print("# 定規に合わせ直した時のジャイロ h2:", round(h2, 2), "度")
    print("# 本当のズレ（＋は回り足りない）:", round(h2 - h1, 2), "度（ジャイロの目盛りで）")
    print(
        "# モーターで回ったときのジャイロの 1 周の読み:",
        round(h2 / TURNS, 3),
        "度（360 なら目盛りは合っている）",
    )
    print("# 電池:", hub.battery.voltage(), "mV")


def main(mode=None, rate=None, correct=None):
    global MODE, RATE, CORRECT
    if correct is not None:
        CORRECT = correct
    if rate is not None:
        RATE = rate
    if mode is not None:
        MODE = mode
    hub, robot, left_wheel, right_wheel, left_lift, right_lift = initialize_robot()
    run_task(run(hub, robot, left_wheel, right_wheel, left_lift, right_lift))


if __name__ == "__main__":
    main()
