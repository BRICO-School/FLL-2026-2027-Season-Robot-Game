"""
【セレクターから走らせて、ミッションごとのジャイロの状態を確かめる】（2026-09-19・検証用。確かめが済んだら selector.py から外す）

selector.py の 9 番に登録してある。競技と同じ流れ（initialize_robot() は始めの 1 回だけ・
ミッションごとは reset_robot() だけ・フォースセンサーで走り出す）のまま、すぐ 5 周まわって、
ジャイロが状態 B（正確な目盛り）か、状態 A（1 周を約 365° と数える）かを見る。

やり方:
 1. uv run python run_with_log.py selector.py --name "Pybricks Hub3" --no-trial
 2. ハブの右ボタン（▶）で 9 を選ぶ
 3. 試したい扱い方をする（例: そのまま置いておく／持ち上げて振ってから置く／ホームへ運ぶまねをする）
 4. 機体の左側面を定規に当てて置き、フォースセンサーを押す → すぐ 5 周まわる
 5. 緑（ピー）になったら定規に当て直して手を離す → 青 → 1 周の読みが出る → セレクターに戻る（3 へ）
 6. 5 回そろうと高い音が 3 回鳴る → ハブの中央ボタンで止める（条件ごとに 1 回のプログラム＝ログ 1 本）

出る行:  G, 回, 前の回が終わってから（1 回目はプログラムを始めてから）の時間 ms, 走り出すとき静止と判定されていたか,
        当て直しで動いた角度, 1 周の読み, 校正前の目盛りで
 校正前の目盛りで 約 360 なら状態 B・約 365 なら状態 A。

ハブの設定は書きかえない。

【更新履歴】
- 2026-09-19: セレクターから走らせる形のジャイロの状態の確かめを追加した
- 2026-09-19: 旋回動作でジャイロの状態を確認する検証プログラムを新規追加した
- 2026-09-19: ジャイロ確認が5回完了するごとに高い音を3回鳴らす処理を追加した。
"""

from pybricks.parameters import Color
from pybricks.tools import StopWatch, wait

TURNS = 5

count = 0
since_last = StopWatch()  # 前の回が終わってから（1 回目は selector.py を始めてから）の時間


async def realign(hub):
    """緑にして、手で定規に当て直されるのを待ち、当て直したあとのジャイロの向きを返す"""
    hub.light.on(Color.GREEN)
    hub.speaker.volume(100)
    await hub.speaker.beep(frequency=500, duration=600)
    total = StopWatch()
    still = StopWatch()
    await wait(1500)  # 手を伸ばす時間
    still.reset()
    while True:
        if not hub.imu.stationary():
            still.reset()
        if total.time() > 6000 and still.time() > 2500:  # 少なくとも 6 秒は待つ
            break
        await wait(20)
    h2 = hub.imu.heading()
    hub.light.on(Color.BLUE)
    await hub.speaker.beep(frequency=1000, duration=200)
    return h2


async def run(hub, robot, left_wheel, right_wheel, left_lift, right_lift):
    global count
    waited_ms = since_last.time()
    was_still = hub.imu.stationary()

    # selector.py が reset_robot()（向きを 0 に戻す）を済ませているので、そのまますぐ走り出す
    h0 = hub.imu.heading()
    await robot.turn(360 * TURNS)
    await wait(1000)
    h1 = hub.imu.heading()
    robot.stop()  # モーターの力を抜く（手で回せるように）
    h2 = await realign(hub)

    count += 1
    per_turn = abs(h2 - h0) / TURNS
    print(
        "G,",
        count,
        ", 前の回から",
        waited_ms,
        "ms , 走り出すとき静止",
        was_still,
        ", 当て直しで動いた角度 h2-h1",
        round(h2 - h1, 2),
        ", 1 周の読み",
        round(per_turn, 3),
        ", 校正前の目盛りで",
        round(per_turn * hub.imu.settings()[-1] / 360, 2),
        ", 電池",
        hub.battery.voltage(),
    )
    if count % 5 == 0:  # 5 回そろった合図（高い音 3 回）。中央ボタンで止めて、次の条件へ
        for _ in range(3):
            await hub.speaker.beep(frequency=1500, duration=150)
            await wait(100)
    since_last.reset()
