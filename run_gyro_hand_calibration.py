"""
【ジャイロの目盛り（heading_correction）を手で測る】（2026-09-17）

モーターは動かさない。機体を手で TURNS 周まわして、ジャイロが何度と数えたかを読む。
始めと終わりに、機体の横を「動かない定規（か壁）」にぴったり当てるので、本当の回転はちょうど 360°×周回数になる。
（Pybricks 公式の測り方: 1 周まわしたときにジャイロが報告する角度が heading_correction）

【手順】
 1. 定規をマットに固定し、機体の左側面をぴったり当てて置く。手を離して、このプログラムを実行する
 2. 「# まわしてね」と出たら、機体を持ち上げずに、その場で右回り（時計回り）にゆっくり TURNS 周まわす
    （1 周 3〜5 秒くらい。何周したかを声に出して数える）
 3. TURNS 周したら、始めと同じ面を定規にぴったり当てて、手を離す
 4. 3 秒じっとしていると「# 結果」が出て終わる

このプログラムはハブの設定を書きかえない（読むだけ）。

【更新履歴】
- 2026-09-17: 機体を手動で回してジャイロの補正値を測定するスクリプトを追加した
"""

from pybricks.hubs import PrimeHub
from pybricks.parameters import Axis
from pybricks.tools import StopWatch, wait

TURNS = 10  # 手でまわす周回数

hub = PrimeHub(top_side=Axis.Z, front_side=Axis.X)
print("# imu.settings:", hub.imu.settings())
print("# じっとしていてね（ジャイロの準備中）")
while not hub.imu.ready():
    wait(100)
hub.imu.reset_heading(0)
wait(500)
print("# まわしてね: 右回りに", TURNS, "周 → 定規にぴったり当てて手を離す")
hub.speaker.beep()

watch = StopWatch()
still = StopWatch()
moved = False
last_print = 0
while True:
    h = hub.imu.heading()
    if abs(h) > 180:
        moved = True
    if not hub.imu.stationary():
        still.reset()
    if watch.time() - last_print >= 1000:
        last_print = watch.time()
        print("#  いま:", round(h, 1), "度 （", round(h / 360, 2), "周）")
    if moved and still.time() > 3000:
        break
    wait(20)

h = hub.imu.heading()
hub.speaker.beep()
print("# 結果: ジャイロの読み", round(h, 2), "度 /", TURNS, "周")
print(
    "# → 1 周あたり",
    round(h / TURNS, 3),
    "度（これが heading_correction の候補。360 なら目盛りは正確）",
)
print("# 電池:", hub.battery.voltage(), "mV")
