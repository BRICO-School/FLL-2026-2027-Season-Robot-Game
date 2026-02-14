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

# ===== ライブラリのインポート =====
# LEGOロボットを動かすために必要な道具を読み込みます
from pybricks.hubs import PrimeHub  # ロボットの「脳みそ」（ハブ）を使うための道具
from pybricks.parameters import Axis, Direction, Port  # ポート、軸、方向などの設定
from pybricks.pupdevices import Motor  # モーターを使うための道具
from pybricks.robotics import DriveBase  # ロボットの移動機能を使うための道具
from pybricks.tools import StopWatch, wait  # 待機とタイマーの道具

# ===== デフォルトの速度・加速度設定 =====
# 各runファイルから共通で使用できる設定値

# 直進時の設定
DEFAULT_STRAIGHT_SETTINGS = {
    "straight_speed": 400,
    "straight_acceleration": 500,
}

# 回転時の設定
DEFAULT_TURN_SETTINGS = {
    "turn_rate": 240,
    "turn_acceleration": 850,
}

# カーブ時の設定
DEFAULT_CURVE_SETTINGS = {
    "straight_speed": 240,
    "straight_acceleration": 800,
}


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
    - Port.F : 左タイヤ（反時計回りが正の方向）
    - Port.B : 右タイヤ（時計回りが正の方向）
    - Port.E : 左リフト（時計回りが正の方向）
    - Port.A : 右リフト（時計回りが正の方向）
    """
    # 左タイヤのモーター（ポートFに接続、反時計回りが正）
    left_wheel = Motor(Port.F, positive_direction=Direction.COUNTERCLOCKWISE)
    # 右タイヤのモーター（ポートBに接続、時計回りが正）
    right_wheel = Motor(Port.B, positive_direction=Direction.CLOCKWISE)
    # 左リフトのモーター（ポートEに接続、時計回りが正）
    left_lift = Motor(Port.E, positive_direction=Direction.CLOCKWISE)
    # 右リフトのモーター（ポートAに接続、時計回りが正）
    right_lift = Motor(Port.A, positive_direction=Direction.CLOCKWISE)

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

    async def turn(self, angle, rate=None, acceleration=None, timeout=None):
        """
        その場で回転する（スピード・タイムアウト指定可能）

        【パラメータ】
        - angle: 回転角度（度）。正の値で右回転、負の値で左回転
        - rate: 回転速度（deg/s）。省略時はデフォルト設定
        - acceleration: 回転加速度（deg/s²）。省略時はデフォルト設定
        - timeout: タイムアウト時間（ミリ秒）。省略時はタイムアウトなし
        """
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
        wheel_diameter=62,  # タイヤの直径（mm）
        axle_track=115,  # 左右のタイヤの間隔（mm）
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
def initialize_robot():
    """
    ロボットを使う準備を全部まとめて行う関数

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
    print("=== ロボット初期化開始 ===")

    # ----- ステップ1: ハブの設定 -----
    hub = setup_hub()
    print("✓ ハブ設定完了")

    # ----- ステップ2: モーターの設定 -----
    left_wheel, right_wheel, left_lift, right_lift = setup_motors()
    print("✓ モーター設定完了")

    # ----- ステップ3: ロボットパラメータの設定 -----
    robot = setup_robot_parameters(left_wheel, right_wheel)
    print("✓ ロボットパラメータ設定完了")

    # ----- ステップ4: PID制御の設定 -----
    setup_pid_control(robot)
    print("✓ PID制御設定完了")

    # ----- ステップ5: センサーの初期化 -----
    initialize_sensors(hub, robot)
    print("✓ センサー初期化完了")

    # ----- ステップ6: モーター角度のリセット -----
    reset_motor_angles(left_wheel, right_wheel, left_lift, right_lift)

    print("=== ロボット初期化完了 ===")

    # ----- すべての設定情報を返す -----
    return hub, robot, left_wheel, right_wheel, left_lift, right_lift
