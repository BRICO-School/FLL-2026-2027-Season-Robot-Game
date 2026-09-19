"""
【ロボット初期化ファイル】
このファイルは、ロボットを使い始める前に必要な「準備作業」をまとめたものです。
料理を始める前に、材料を並べたり、調理器具を準備するのと同じように、
ロボットもプログラムを動かす前に、モーターやセンサーの設定が必要です。

【このファイルでやること】
1. ハブ（ロボットの脳みそ）の向きを設定
2. モーター（タイヤやアームを動かす装置）の設定
3. ロボットの速度やパワーの設定
4. PID制御（ロボットをまっすぐ動かすための調整機能）の設定
5. センサーの初期化

【使い方】
他のプログラムから「initialize_robot()」という関数を呼ぶだけで、
すべての準備が自動的に完了します。
"""

# ===== 2026-27 本番機（ローバー型）の確定値 =====
# 反映日: 2026-09-17 / 測定: replication-study R班 r1（code/data/R/r1/trials.csv・groups/R/Step8-持ち込み値.md）
# wheel 62.32 (straight() で 1000mm 実測 999.9〜1001.6mm) / axle 114.48 (360° 平均 360.38°)
# turn 250 deg/s・acc 313【暫定】(45/60/75/90° 各 n=8 で SD 0.70〜1.13°・合格ライン 1.6°)
# straight 550 mm/s (天井 547mm/s) / straight_acc 800 (n=10 実測平均 999.9mm 幅 4mm・2.93 秒)
# heading PID 既定 / distance PID 既定（Pybricks の既定 7558-0-1889-4-8。KI を足しても良くならなかった）
# short move: なし（200mm も 45° も同じ加速度） / 回転の打ち消し: 既定では使わない（表 TURN_OVERSHOOT_TABLE は compensate=True のときだけ）
# 昨年の値: old/setup_last_season_backup.py（上書き前の姿。編集しない）

# ===== ライブラリのインポート =====
# LEGOロボットを動かすために必要な道具を読み込みます
from pybricks.hubs import PrimeHub  # ロボットの「脳みそ」（ハブ）を使うための道具
from pybricks.parameters import Axis, Direction, Port  # ポート、軸、方向などの設定
from pybricks.pupdevices import Motor  # モーターを使うための道具
from pybricks.robotics import DriveBase  # ロボットの移動機能を使うための道具
from pybricks.tools import StopWatch, wait  # 待機とタイマーの道具


class NullMotor:
    """
    物理的にモーターが接続されていない場合に使うダミーモーター。

    - await motor.run_angle(...) / motor.run_angle(..., wait=False) の両方に対応
    - motor.control.done() を常に True にする（即完了扱い）
    - angle()/speed()/reset_angle()/dc()/stop() を最低限提供
    """

    def __init__(self, name="(null)"):
        self._name = name
        self._angle = 0
        self.control = self  # motor.control.done() 互換

    def done(self):
        return True

    def angle(self):
        return self._angle

    def speed(self):
        return 0

    def reset_angle(self, angle=0):
        self._angle = angle

    def stop(self):
        return None

    def dc(self, _duty):
        return None

    async def _run_angle_wait(self, _speed, angle):
        self._angle += angle
        return None

    def run_angle(self, speed, angle, wait=True, **_kwargs):
        # 本物のモーターと同じ呼び出し形に寄せる。
        # wait=False の場合は非同期処理を開始した扱いにして即 return。
        if wait is False:
            self._angle += angle
            return None
        return self._run_angle_wait(speed, angle)


def _safe_motor(port, positive_direction, name):
    """
    モーターが未接続でもプログラムを止めないための安全生成。
    接続されていなければ NullMotor を返す。
    """
    try:
        return Motor(port, positive_direction=positive_direction)
    except Exception as e:
        print(f"! {name} not found on {port}; using NullMotor. ({e})")
        return NullMotor(name)


# ===== デフォルトの速度・加速度設定 =====
# 各runファイルから共通で使用できる設定値

# 直進時の設定
DEFAULT_STRAIGHT_SETTINGS = {
    "straight_speed": 550,
    "straight_acceleration": 800,
}

# 回転時の設定
DEFAULT_TURN_SETTINGS = {
    "turn_rate": 250,
    "turn_acceleration": 313,
}

# ===== new / old の切りかえ（2026-09-18・オーナー方針） =====
# 本番機の開発中は、今年の値 (new) と昨年の値 (old) を使い分けて、ミッションの成功率で見きわめる。
#   new … 上の DEFAULT_*（直進 550・800 / 回転 250・313）＋ Pybricks 既定の PID
#   old … 昨年の速度・加速度（直進 400・500 / 回転 240・850）＋ 昨年の PID（方向 2000/50/100・距離 1000/50/10）
#   寸法（wheel/axle）と校正表はどちらも今年の値（機体は同じなので）。
# Step 9 の比較（2026-09-18・replication-study groups/R/progress.md）: 直進の精度・回転のばらつき・時間は new、
#   square の終点は old（10mm 対 22mm）→ 校正表を 365.8 にして new は 5〜6mm に縮んだ（状態 A のとき）。
#   2026-09-19: 365.8 は取り下げ。始めに 2 秒待つ＋校正表 360.1 で new の square（700mm）×4 本の終点は 10 / 2 / 10 / 16mm。
#   9/18 の turn / square / mission の向きと終点は、ジャイロの状態 A/B が混ざる条件での数字なので取り直しの候補（直進・時間はそのまま）。
# 切りかえ方: ここを書きかえるか、run ファイルで initialize_robot(drive_settings="old") と呼ぶ。起動時に画面に出る。
DRIVE_SETTINGS = "new"   # "new" / "old"
LAST_SEASON_STRAIGHT_SETTINGS = {"straight_speed": 400, "straight_acceleration": 500}
LAST_SEASON_TURN_SETTINGS = {"turn_rate": 240, "turn_acceleration": 850}

# ===== ジャイロに見えない「回り足りなさ」の補正【暫定・2026-09-17 マット上の実測】 =====
# 【2026-09-17 夜の結論】Hub3 の IMU を公式手順で 3 軸校正した（手で回すと 1 周 359.7° と正しく数える）。
#   それでもモーターで回ると 1 周を 363.6° と数える（＝機体は 1 周あたり約 3.6°・90° あたり約 0.9° 回り足りない）。
#   手回しとモーターの差（約 1%）は校正の前後で変わらず、原因は未特定。ハブは B班と共用なので、
#   ハブの heading_correction はいじらず、この機体の Robot.turn() の中で角度を 1.0099 倍して合わせる。
#   以下は午後の経過の記録（係数を 2 回作って外した）。
# 機体の左側面の前後 2 つの角（184mm 離れている）の動きから、本当の向きを測った。
#   その場で 5 周（1800°）  : 本当は 10.3° 足りない。ジャイロが見ていたのは 1.7° だけ
#   90° を 4 回（1 周）      : 本当は 5.9° 足りない（2 回測って 6.6° と 5.9°）。ジャイロが見ていたのは 0.5° だけ
#   90° を 4 回の 3 回目      : 本当は 1.9° 足りない（ジャイロは 0.5°）← ばらつきが大きく、下の係数はまだ決まっていない
#   90° ずつ止まりながら 5 周（止まる 20 回）: 本当は 23.4° 足りない。ジャイロが見ていたのは 0.3° だけ
#   止まらずに 5 周の 2 回目（15:45）: 本当は 24.7° 足りない（ジャイロは 1.3°）← 1 回目の 10.3° と合わない
# 【結論・2026-09-17】回り足りない向きは 7 回とも同じだが、大きさは 1 周あたり 1.4〜5.6° とばらつき、
#   下の係数は信頼できない。correct=True は使わないこと（仕組みだけ残してある）。
# （以前の見積もり）同じ 5 周どうしの差から: 止まるたびに約 0.76°（(23.1−8.6)÷19）＋ 1 周あたり約 1.57°（目盛りのズレ）
# Robot.turn(…, correct=True) のときだけ、このぶん大きい角度を命令する（既定は使わない）。
# 左回り・45° など他の角度・速度を変えたときにも同じ量かは未確認。
GYRO_TURN_SCALE = 1.0099  # 2026-09-17 夜: IMU 3 軸校正のあと、モーターで 5 周 ×3 の読み 363.38/363.63/363.69 ÷ 360  # 命令角度に掛ける（1 周 361.5° ぶん回すと本当の 360°）
TURN_STOP_OFFSET = 0.0  # 止まるたびのズレは確認できなかったので 0  # 1 回の回転ごとに足す角度（度）


# 回転の「回りすぎ」の打ち消し表（命令した角度, 回りすぎの平均）。単位は度。
# 【2026-09-17 マット上の確認で「既定では使わない」に変更】プログラムの最初の 1 回だけ回る、のような
# 単発の回転を測ると turn(45) は平均 47.65° 回る。ただし続けて動くときは Pybricks が命令の合計を目標に
# 向きを保つのでズレは積み上がらず、打ち消すと逆にズレる。使うときだけ turn(…, compensate=True)。
# 表の間の角度は直線でつないで求めます（例: 58° → +1.89°）。45° 未満は未測定なので 0° で 0 になる直線で代用。
# 測定: 既定 PID・回転加速度 313・各 n=8（2026-09-17）。【暫定】競技マットの上で測り直して入れ替える。
TURN_OVERSHOOT_TABLE = (
    (0, 0.0),
    (45, 2.65),
    (60, 1.77),
    (75, 1.26),
    (90, 0.80),
    (360, 0.14),
)


def turn_overshoot(angle):
    """命令したい角度（度）に対する「回りすぎ」の見込み（度・いつも 0 以上）を表から求める"""
    a = abs(angle)
    table = TURN_OVERSHOOT_TABLE
    if a >= table[-1][0]:
        return table[-1][1]
    for i in range(len(table) - 1):
        a0, e0 = table[i]
        a1, e1 = table[i + 1]
        if a <= a1:
            return e0 + (e1 - e0) * (a - a0) / (a1 - a0)
    return table[-1][1]


# カーブ時の設定
DEFAULT_CURVE_SETTINGS = {
    "straight_speed": 240,
    "straight_acceleration": 800,
}


# ===== 機体（ハブ）ごとの校正表 =====
# ジャイロの目盛りはハブごとに違い、車輪径も機体ごとに少し違う。ハブの名前で引いて、その機体の値を使う。
# 表に無いハブは、ハブの設定に触らず、下の DEFAULT_PROFILE で動く（起動時に「未校正」と表示される）。
#
# 1 台を足す手順（約 15 分・道具はこのリポジトリにある）:
#   1. ハブを機体から外して 3 軸校正: run_imu_calibrate_guided.py（結果はハブに保存される。ファームを入れ直すと消える）
#   2. 機体に戻して、モーターで 5 周 → 手で定規に合わせ直し ×3: run_gyro_motor_check.py
#      （この表にそのハブがまだ無い状態＝ heading_correction 360 で測る）
#      「モーターで回ったときのジャイロの 1 周の読み」の平均を heading_correction に書く
#   3. 1000mm 直進をものさしで測って wheel を補正する（任意）
#
# heading_correction は「モーターで回したとき、本当の 1 周でジャイロが何度と数えるか」。
# 測るときは、プログラムを始めてから 1 秒以上止まったあとの回転で測る（下の GYRO_SETTLE_MS と 2026-09-19 の注記）。
# 始めてすぐの回転は約 1.4% 多く数える（理由は未特定・速度を変えても同じ）ので、校正に使わない。
# Robot.turn() は小数の角度を受け取れない（Pybricks が整数に丸める）ので、命令角度を 1.01 倍する方法は使えない。
DEFAULT_PROFILE = {"wheel": 62.32, "axle": 114.48, "heading_correction": None}
ROBOT_PROFILES = {
    # 本番機（ローバー型）。2026-09-17: 3 軸校正ずみ。
    # 2026-09-18: ジャイロはモーターで回すと「1 周を約 365° と数える状態 A（多数・今日 22 本中 16）」と
    # 「約 360° と数える状態 B（少数・手回しと同じ）」を行き来する（原因未特定。間の値は出ない）。
    # 364.0（9/17・2 状態の間）では状態 A のとき 90° あたり 0.45° 回り足りず、square の終点が 22mm ずれた
    # （turn/square の当て直し測定で同じ大きさ）。状態 A に合わせて 365.8 に上げる（暫定・オーナー判断 9/18）。
    # 状態 B のときは 90° あたり 1.45° 回りすぎになる。状態を分ける条件が分かったら見直す。
    # 2026-09-19: 条件が分かった（暫定）。状態 A は「プログラムを始めてすぐ（約 1 秒以内）に回り始めたとき」だけ出る。
    # 待たずに回すと 1 回目の 5 周だけ A（4 本とも 364.7〜364.8）・1 / 3 / 10 秒止まってからなら 1 回目から B（5 本とも）・
    # 2 回目以降は全部 B。セレクターはボタン待ちで止まっているので、大会形式の走行は B になる見こみ。
    # → initialize_robot() の終わりで GYRO_SETTLE_MS だけ止まって待ち、校正表は B に合わせる:
    #   B の 1 周の読み 20 回の平均 360.11（SD 0.13・359.89〜360.38）→ 360.1（暫定・オーナー判断 9/19。365.8 は取り下げ）
    "Pybricks Hub3": {"wheel": 62.32, "axle": 114.48, "heading_correction": 360.1},
}

# プログラムを始めてすぐの回転は、ジャイロが約 1.4% 多く数える（上の 2026-09-19 の注記）。
# initialize_robot() の終わりで、ハブが「静止」と判定しつづける時間がこれだけたまるまで待ってから走り出す。
# 1 秒で足りた（1 本）が、余裕をみて 2 秒。機体を置いて手を離してから数え始まる。
GYRO_SETTLE_MS = 2000
GYRO_SETTLE_TIMEOUT_MS = 10000  # 手で持ったままなどで静止にならないとき、あきらめて進むまでの時間
_active_profile = DEFAULT_PROFILE


def apply_robot_profile(hub):
    """ハブの名前で校正表を引き、ジャイロの目盛りをその機体の値に合わせる"""
    global _active_profile
    name = hub.system.name()
    settings = hub.imu.settings()
    if tuple(settings[3]) == (360.0, 360.0, 360.0):
        print("! IMU の 3 軸校正がされていません（run_imu_calibrate_guided.py を実行してね）")
    profile = ROBOT_PROFILES.get(name)
    if profile is None:
        _active_profile = DEFAULT_PROFILE
        print("! ", name, "は校正表に無いハブです。回転が 90° あたり 1° くらいずれるかもしれません")
        return
    _active_profile = profile
    target = profile["heading_correction"]
    if target is not None and abs(settings[5] - target) > 0.05:
        hub.imu.settings(heading_correction=target)
        print("✓ ジャイロの目盛りを", name, "の値にしました:", target)
    else:
        print("✓ 機体の校正表:", name, profile)


# ===== ハブの設定をする関数 =====
def setup_hub():
    """
    ハブ（ロボットの脳みそ）の向きを設定する関数

    【説明】
    ハブには「どちらが上か」「どちらが前か」を教える必要があります。
    これを正しく設定しないと、ロボットが正しく動きません。

    【設定内容】
    - top_side=Axis.Z : Z軸が上向き
    - front_side=Axis.X : X軸が前向き
    """
    return PrimeHub(top_side=Axis.Z, front_side=Axis.X)


# ===== モーターの設定をする関数 =====
def setup_motors():
    """
    4つのモーター（左右のタイヤ、左右のリフト）を設定する関数

    【説明】
    ロボットには4つのモーターがあります：
    1. 左のタイヤ用モーター
    2. 右のタイヤ用モーター
    3. 左のリフト（アーム）用モーター
    4. 右のリフト（アーム）用モーター

    それぞれのモーターがどのポート（差し込み口）に接続されているか、
    どちらの方向を「正」とするかを設定します。

    【ポートの接続】
    - Port.F : 左タイヤ（反時計回りが正の方向）※必須
    - Port.B : 右タイヤ（時計回りが正の方向）※必須
    - Port.E : 左リフト（未接続なら NullMotor）
    - Port.A : 右リフト（未接続なら NullMotor）

    B と F のモーターが繋がっていれば走行可能です。
    """
    # リフトは未接続のことがあるので先に安全に生成（未接続なら NullMotor）
    left_lift = _safe_motor(Port.E, positive_direction=Direction.CLOCKWISE, name="left_lift")
    right_lift = _safe_motor(Port.A, positive_direction=Direction.CLOCKWISE, name="right_lift")
    # 左タイヤのモーター（ポートFに接続、反時計回りが正）※必須
    left_wheel = Motor(Port.F, positive_direction=Direction.COUNTERCLOCKWISE)
    # 右タイヤのモーター（ポートBに接続、時計回りが正）※必須
    right_wheel = Motor(Port.B, positive_direction=Direction.CLOCKWISE)

    # 4つのモーターをまとめて返す
    return left_wheel, right_wheel, left_lift, right_lift


# ===== Robotクラス（DriveBaseのラッパー） =====
class Robot:
    """
    DriveBaseをラップした便利なロボットクラス

    【このクラスの特徴】
    straight(), turn(), curve() でスピードを直接指定できます。

    【使用例】
    await robot.straight(200, speed=220)       # 220mm/sで200mm前進
    await robot.turn(90, rate=300)              # 300deg/sで90度回転
    await robot.curve(200, 45, speed=150)       # 150mm/sでカーブ

    スピードを指定しない場合は、デフォルト設定が使われます。
    """

    def __init__(self, drivebase):
        """DriveBaseを受け取って初期化"""
        self._robot = drivebase

    async def straight(self, distance, speed=None, acceleration=None, timeout=None):
        """
        直進する（スピード・タイムアウト指定可能）

        【パラメータ】
        - distance: 移動距離（mm）。正の値で前進、負の値で後退
        - speed: 速度（mm/s）。省略時はデフォルト設定
        - acceleration: 加速度（mm/s²）。省略時はデフォルト設定
        - timeout: タイムアウト時間（ミリ秒）。省略時はタイムアウトなし
        """
        # スピード設定
        if speed is not None or acceleration is not None:
            self._robot.settings(
                straight_speed=speed
                if speed is not None
                else DEFAULT_STRAIGHT_SETTINGS["straight_speed"],
                straight_acceleration=acceleration
                if acceleration is not None
                else DEFAULT_STRAIGHT_SETTINGS["straight_acceleration"],
            )

        if timeout is not None:
            # タイムアウト付きで実行
            self._robot.straight(distance, wait=False)
            timer = StopWatch()
            timer.reset()
            while timer.time() < timeout:
                if self._robot.done():
                    break
                await wait(10)
            self._robot.stop()  # タイムアウト時は停止
        else:
            # 通常の実行（完了まで待つ）
            await self._robot.straight(distance)

        # デフォルト設定に戻す
        if speed is not None or acceleration is not None:
            self._robot.settings(**DEFAULT_STRAIGHT_SETTINGS)

    async def turn(
        self, angle, rate=None, acceleration=None, timeout=None, compensate=False, correct=False
    ):
        """
        その場で回転する（スピード・タイムアウト指定可能）

        【パラメータ】
        - angle: 回転角度（度）。正の値で右回転、負の値で左回転
        - rate: 回転速度（deg/s）。省略時はデフォルト設定
        - acceleration: 回転加速度（deg/s²）。省略時はデフォルト設定
        - timeout: タイムアウト時間（ミリ秒）。省略時はタイムアウトなし
        - compensate: True にしたときだけ「回りすぎ」のぶんだけ小さい角度を命令する
          （TURN_OVERSHOOT_TABLE）。**既定は False（打ち消さない）**。
          Pybricks は 1 つのプログラムの中では「命令した角度の合計」を目標の向きとして
          覚えていて、回転のズレは次の動きで自動的に取り戻される（積み上がらない）。
          そこへ打ち消しを入れると、逆に 1 回あたり約 0.8° ずつ回り足りなくなる
          （2026-09-17 マット上で確認: 90°×4 で −4.7°）。
          表は既定の速度・加速度で測ったもの。rate / acceleration を指定したときは打ち消さない。
        - correct: 【使わないこと】Pybricks の turn() は角度を整数に丸めるので、90° のような小さい角度では効かない
          （2026-09-17 に確認。いまは機体ごとの校正表 ROBOT_PROFILES の heading_correction で合わせる）。
          True にしたときだけ、ジャイロに見えない「回り足りなさ」のぶんだけ大きい角度を命令する
          （GYRO_TURN_SCALE と TURN_STOP_OFFSET）。**既定は False**。係数は測定のばらつきが大きく
          まだ決まっていない（2026-09-17・90°×4 の 3 回で 5.6° / 5.0° / 1.4°）。
        """
        # ジャイロに見えない回り足りなさの補正
        if correct and angle != 0:
            extra = abs(angle) * (GYRO_TURN_SCALE - 1) + TURN_STOP_OFFSET
            angle = angle + extra if angle > 0 else angle - extra

        # 回りすぎの打ち消し（既定の速度・加速度のときだけ）
        if compensate and rate is None and acceleration is None:
            over = turn_overshoot(angle)
            angle = angle - over if angle >= 0 else angle + over

        # スピード設定
        if rate is not None or acceleration is not None:
            self._robot.settings(
                turn_rate=rate if rate is not None else DEFAULT_TURN_SETTINGS["turn_rate"],
                turn_acceleration=acceleration
                if acceleration is not None
                else DEFAULT_TURN_SETTINGS["turn_acceleration"],
            )

        if timeout is not None:
            # タイムアウト付きで実行
            self._robot.turn(angle, wait=False)
            timer = StopWatch()
            timer.reset()
            while timer.time() < timeout:
                if self._robot.done():
                    break
                await wait(10)
            self._robot.stop()
        else:
            # 通常の実行
            await self._robot.turn(angle)

        # デフォルト設定に戻す
        if rate is not None or acceleration is not None:
            self._robot.settings(**DEFAULT_TURN_SETTINGS)

    async def curve(self, radius, angle, speed=None, acceleration=None, timeout=None):
        """
        カーブする（スピード・タイムアウト指定可能）

        【パラメータ】
        - radius: カーブの半径（mm）
        - angle: 回転角度（度）
        - speed: 速度（mm/s）。省略時はデフォルト設定
        - acceleration: 加速度（mm/s²）。省略時はデフォルト設定
        - timeout: タイムアウト時間（ミリ秒）。省略時はタイムアウトなし
        """
        # スピード設定
        if speed is not None or acceleration is not None:
            self._robot.settings(
                straight_speed=speed
                if speed is not None
                else DEFAULT_CURVE_SETTINGS["straight_speed"],
                straight_acceleration=acceleration
                if acceleration is not None
                else DEFAULT_CURVE_SETTINGS["straight_acceleration"],
            )

        if timeout is not None:
            # タイムアウト付きで実行
            self._robot.curve(radius, angle, wait=False)
            timer = StopWatch()
            timer.reset()
            while timer.time() < timeout:
                if self._robot.done():
                    break
                await wait(10)
            self._robot.stop()
        else:
            # 通常の実行
            await self._robot.curve(radius, angle)

        # デフォルト設定に戻す
        if speed is not None or acceleration is not None:
            self._robot.settings(**DEFAULT_STRAIGHT_SETTINGS)

    async def run_motor(self, motor, speed, angle, timeout=None):
        """
        個別のモーターを回転させる（タイムアウト指定可能）

        【パラメータ】
        - motor: 対象のモーター（left_wheel, right_wheel, left_lift, right_liftなど）
        - speed: 回転速度（deg/s）
        - angle: 回転角度（度）
        - timeout: タイムアウト時間（ミリ秒）。省略時はタイムアウトなし

        【使用例】
        await robot.run_motor(right_wheel, 200, 140, timeout=1500)
        await robot.run_motor(left_lift, 300, 180)
        """
        if timeout is not None:
            # タイムアウト付きで実行
            motor.run_angle(speed, angle, wait=False)
            timer = StopWatch()
            timer.reset()
            while timer.time() < timeout:
                if motor.control.done():
                    break
                await wait(10)
            motor.stop()
        else:
            # 通常の実行（完了まで待つ）
            await motor.run_angle(speed, angle)

    # ----- 元のDriveBaseのメソッドをそのまま使えるようにする -----
    def stop(self):
        """ロボットを停止"""
        self._robot.stop()

    def reset(self):
        """走行距離などをリセット"""
        self._robot.reset()

    def distance(self):
        """走行距離を取得"""
        return self._robot.distance()

    def settings(self, **kwargs):
        """設定を変更（元のDriveBase.settingsと同じ）"""
        self._robot.settings(**kwargs)

    def use_gyro(self, use):
        """ジャイロセンサーの使用設定"""
        self._robot.use_gyro(use)

    def distance_control(self):
        """距離制御（PID設定用）"""
        return self._robot.distance_control

    def heading_control(self):
        """方向制御（PID設定用）"""
        return self._robot.heading_control


# ===== ロボットのパラメータ（動作の設定）をする関数 =====
def setup_robot_parameters(left_wheel, right_wheel):
    """
    ロボットの動く速度を設定する関数

    【説明】
    速度・加速度はDEFAULT_STRAIGHT_SETTINGS、DEFAULT_TURN_SETTINGSで定義された
    デフォルト値が自動的に適用されます。

    【返り値】
    Robotクラスのインスタンス（DriveBaseをラップしたもの）
    """

    # ----- ロボットの物理的な大きさを設定 -----
    drivebase = DriveBase(
        left_wheel,  # 左タイヤのモーター
        right_wheel,  # 右タイヤのモーター
        wheel_diameter=_active_profile["wheel"],  # タイヤの直径（mm）。機体ごとの校正表から
        axle_track=_active_profile["axle"],  # 左右のタイヤの間隔（mm）。機体ごとの校正表から
    )

    # ----- デフォルトの速度・加速度を自動適用 -----
    drivebase.settings(**DEFAULT_STRAIGHT_SETTINGS, **DEFAULT_TURN_SETTINGS)
    print(f"✓ デフォルト設定適用: 直進={DEFAULT_STRAIGHT_SETTINGS}, 回転={DEFAULT_TURN_SETTINGS}")

    # Robotクラスでラップして返す
    return Robot(drivebase)


# ===== PID制御の設定をする関数 =====
def setup_pid_control(robot):
    """
    PID制御を設定する関数

    【PID制御とは？】
    ロボットをまっすぐ正確に動かすための「自動調整機能」です。

    例えば、車を運転するときに、カーブでハンドルを少しずつ調整しますよね？
    PID制御は、ロボットが自動的にこの調整をしてくれる機能です。

    【PIDの意味】
    - P (Proportional: 比例) : 目標からどれくらいズレているかに応じて調整
    - I (Integral: 積分) : 過去のズレを積み重ねて調整
    - D (Derivative: 微分) : ズレの変化の速さに応じて調整

    【2種類のPID制御】
    1. 距離制御 (DISTANCE) : 「どれくらい進むか」を正確にコントロール
    2. 方向制御 (HEADING) : 「どの方向を向くか」を正確にコントロール

    【注意】
    下の数値（KP, KI, KD）は「ゲイン」と呼ばれ、調整の強さを決めます。
    この数値を変えると、ロボットの動きが変わります。
    うまく動かない場合は、これらの数値を調整する必要があります。
    """

    # ----- 距離制御用のPIDゲイン（「進む距離」をコントロール） -----
    DISTANCE_KP = 1000  # P（比例）ゲイン: 目標との距離差に対する反応の強さ
    DISTANCE_KI = 50  # I（積分）ゲイン: 過去のズレを修正する強さ
    DISTANCE_KD = 10  # D（微分）ゲイン: 急な変化を抑える強さ

    # ----- 方向制御用のPIDゲイン（「向き」をコントロール） -----
    HEADING_KP = 2000  # P（比例）ゲイン: 目標との角度差に対する反応の強さ
    HEADING_KI = 50  # I（積分）ゲイン: 過去のズレを修正する強さ
    HEADING_KD = 100  # D（微分）ゲイン: 急な変化を抑える強さ

    # ----- ロボットにPIDゲインを設定 -----
    # 【2026-09-17】今年の本番機は Pybricks の既定の PID（7558-0-1889）をそのまま使う。
    # 測った結果、KI を足したり値を変えたりしても良くならなかったため（replication-study R班 Step 7）。
    # 上の昨年の数値は、昨年設定との比較（Step 9）用に残してある。使うときだけ USE_LAST_SEASON_PID を True に。
    # 2026-09-18: DRIVE_SETTINGS が "old" のときは昨年の PID も入れる（new/old の使い分け）。
    USE_LAST_SEASON_PID = DRIVE_SETTINGS == "old"
    if USE_LAST_SEASON_PID:
        # 距離制御のPIDゲインを設定
        robot.distance_control().pid(kp=DISTANCE_KP, ki=DISTANCE_KI, kd=DISTANCE_KD)

        # 方向制御のPIDゲインを設定
        robot.heading_control().pid(kp=HEADING_KP, ki=HEADING_KI, kd=HEADING_KD)


# ===== センサーを初期化する関数 =====
def initialize_sensors(hub, robot):
    """
    センサーとジャイロ（方向センサー）を初期化する関数

    【説明】
    ロボットには「ジャイロセンサー」という、スマートフォンの画面回転機能と同じような
    センサーが付いています。これは「ロボットがどちらを向いているか」を測定します。

    【やること】
    1. ジャイロセンサーを使用する設定にする
    2. 方向を0度（まっすぐ）にリセット
    3. ロボットの走行距離などをリセット

    【なぜ必要？】
    プログラムを実行する前に、「今がスタート地点」だと教える必要があります。
    これをしないと、前のプログラムの影響が残ってしまいます。
    """
    robot.use_gyro(True)  # ジャイロセンサーを使う設定にする
    hub.imu.reset_heading(0)  # 方向を0度（正面）にリセット
    robot.reset()  # ロボットの走行距離や回転角度をリセット


def wait_gyro_settle(hub):
    """ジャイロの目盛りが落ち着くまで、機体が止まったまま GYRO_SETTLE_MS 待つ関数"""
    total = StopWatch()
    still = StopWatch()
    while still.time() < GYRO_SETTLE_MS:
        if not (hub.imu.ready() and hub.imu.stationary()):
            still.reset()  # 動いたら数え直し
        if total.time() > GYRO_SETTLE_TIMEOUT_MS:
            print("⚠ ジャイロの待ち: 機体が止まらないまま", GYRO_SETTLE_TIMEOUT_MS, "ms たちました。回転が約 1.4% ずれるかもしれません")
            return
        wait(20)
    print("✓ ジャイロの待ち完了:", total.time(), "ms（止まったまま", GYRO_SETTLE_MS, "ms）")


# ===== モーターの角度をリセットする関数 =====
def reset_motor_angles(left_wheel, right_wheel, left_lift, right_lift):
    """
    すべてのモーターの角度を0度にリセットする関数

    【説明】
    モーターは回転した角度を記録しています。
    例えば、タイヤが360度回転したら「1回転した」と記録されます。

    この関数は、すべてのモーターの角度を0度に戻します。
    時計の針を12時の位置に戻すようなイメージです。

    【対象モーター】
    - 左タイヤ
    - 右タイヤ
    - 左リフト（アーム）
    - 右リフト（アーム）

    【なぜ必要？】
    プログラムを実行する前に、モーターの角度をリセットしないと、
    「前回どこまで回転したか」の情報が残ってしまい、正確に動きません。
    """
    left_wheel.reset_angle(0)  # 左タイヤのモーターを0度にリセット
    right_wheel.reset_angle(0)  # 右タイヤのモーターを0度にリセット
    left_lift.reset_angle(0)  # 左リフトのモーターを0度にリセット
    right_lift.reset_angle(0)  # 右リフトのモーターを0度にリセット
    print("✓ モーター角度リセット完了: 全モーター=0°")


# ===== ロボット全体を初期化する関数（メイン関数） =====
def initialize_robot(drive_settings=None):
    """
    ロボットを使う準備を全部まとめて行う関数

    drive_settings: "new"（今年の値）/ "old"（昨年の速度・加速度・PID）。省略時は DRIVE_SETTINGS（2026-09-18）

    【説明】
    この関数は、上で定義した5つの関数をすべて実行して、
    ロボットを使えるようにします。
    速度・加速度はDEFAULT_STRAIGHT_SETTINGS、DEFAULT_TURN_SETTINGSで
    定義されたデフォルト値が自動的に適用されます。

    【実行する処理（順番通り）】
    1. ハブの設定
    2. モーターの設定
    3. ロボットパラメータの設定
    4. PID制御の設定
    5. センサーの初期化
    6. モーター角度のリセット

    【返り値（戻ってくる値）】
    この関数は、以下の6つの情報を返します：
    - hub : ハブ（ロボットの脳みそ）
    - robot : ロボット全体のオブジェクト
    - left_wheel : 左タイヤのモーター
    - right_wheel : 右タイヤのモーター
    - left_lift : 左リフトのモーター
    - right_lift : 右リフトのモーター

    【使い方の例】
    他のプログラムから以下のように使います：
    hub, robot, left_wheel, right_wheel, left_lift, right_lift = initialize_robot()
    """
    global DRIVE_SETTINGS
    if drive_settings is not None:
        DRIVE_SETTINGS = drive_settings
    if DRIVE_SETTINGS == "old":
        DEFAULT_STRAIGHT_SETTINGS.update(LAST_SEASON_STRAIGHT_SETTINGS)
        DEFAULT_TURN_SETTINGS.update(LAST_SEASON_TURN_SETTINGS)
    elif DRIVE_SETTINGS != "new":
        print("! DRIVE_SETTINGS が不正:", DRIVE_SETTINGS, "→ new で動きます")
        DRIVE_SETTINGS = "new"
    print("=== ロボット初期化開始 ===")
    print("★ 走行設定:", DRIVE_SETTINGS, "（new＝今年の値 / old＝昨年の速度・加速度・PID）")

    # ----- ステップ1: ハブの設定 -----
    hub = setup_hub()
    apply_robot_profile(hub)
    print("✓ ハブ設定完了")

    # ----- ステップ2: モーターの設定 -----
    left_wheel, right_wheel, left_lift, right_lift = setup_motors()
    print("✓ モーター設定完了")

    # ----- ステップ3: ロボットパラメータの設定 -----
    robot = setup_robot_parameters(left_wheel, right_wheel)
    print("✓ ロボットパラメータ設定完了")

    # ----- ステップ4: PID制御の設定 -----
    setup_pid_control(robot)
    if DRIVE_SETTINGS == "old":
        print("✓ PID制御設定完了（昨年の値 方向 2000/50/100・距離 1000/50/10）")
    else:
        print("✓ PID制御設定完了（Pybricks の既定値を使用）")

    # ----- ステップ5: センサーの初期化 -----
    wait_gyro_settle(hub)  # 始めてすぐの回転はジャイロが多く数えるので、止まったまま少し待つ（2026-09-19）
    initialize_sensors(hub, robot)
    print("✓ センサー初期化完了")

    # ----- ステップ6: モーター角度のリセット -----
    reset_motor_angles(left_wheel, right_wheel, left_lift, right_lift)

    print("=== ロボット初期化完了 ===")

    # ----- すべての設定情報を返す -----
    return hub, robot, left_wheel, right_wheel, left_lift, right_lift
