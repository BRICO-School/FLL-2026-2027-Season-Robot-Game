"""
【開発版プログラムセレクター】
このファイルは、selector.pyの「開発版（デベロップメント版）」です。
通常版よりも高機能で、デバッグ（バグ探し）に便利な機能があります。

【通常版（selector.py）との違い】
1. センサーログ機能：ロボットの動きをリアルタイムで記録できる
2. 非同期処理：複数の作業を同時に行える（ログを取りながらロボットを動かす）
3. devフラグ：開発モードと本番モードを簡単に切り替えられる

【devフラグとは？】
- dev=True : 開発モード（センサーログが有効、デバッグに便利）
- dev=False : 本番モード（センサーログなし、競技本番用）

【使い方】
通常版と同じように、左右ボタンでプログラムを選び、
フォースセンサーで実行します。
開発モードでは、ロボットの動きが数値で画面に表示されます。

【いつ使う？】
- プログラムのテスト中 → dev=True
- 競技本番 → dev=False
"""

# ===== ライブラリのインポート =====
# LEGOロボットを動かすために必要な道具を読み込みます
from pybricks.parameters import Button, Color, Port  # ポート番号、ボタン、色などの設定
from pybricks.pupdevices import ForceSensor  # センサーを使うための道具
from pybricks.tools import StopWatch, multitask, run_task, wait  # 待機、並行処理、タイマーの道具

# ----- 競技プログラムのインポート -----
# 各ミッションのプログラムを読み込みます
import run1_M01_M02_kanna  # ミッション1と2のプログラム
import run1_m08_M06_M05_new  # ミッション8、6、5のプログラム（新版）
import run1_M10_M11  # ミッション10と11のプログラム
import run1_M13_M03  # ミッション13と3のプログラム
import run3_M09_M07_ayumu_modified  # ミッション9と7のプログラム（修正版）
import run4_M12_ayumu  # ミッション12のプログラム
from setup import initialize_robot  # ロボットを初期化する関数をインポート

# ===== 開発モードの設定 =====
# ★★★ここを変更することで、開発モードと本番モードを切り替えます★★★
dev = False  # False=本番モード、True=開発モード（センサーログ有効）
# テスト中は dev=True にすると、ロボットの動きが詳しく分かります
# 競技本番では dev=False にすると、動作が軽くなります

# ===== ロボットの初期化 =====
# ロボットを使う準備をします（モーターやセンサーの設定を行う）
hub, robot, left_wheel, right_wheel, left_lift, right_lift = initialize_robot()

# ===== プログラムリスト =====
# ここに、実行したいプログラムを登録します
# 競技の「ラン（run）」の順番に並べると分かりやすいです
#
# 各プログラムは以下の情報を持っています：
#   - module: どのファイルに関数があるか（必須）
#   - display_number: ハブに表示する番号（必須）
# ※ 各モジュールには「run」という名前の関数が必要です
programs = [
    {"module": run1_m08_M06_M05_new, "display_number": 1},
    {"module": run3_M09_M07_ayumu_modified, "display_number": 2},
    {"module": run1_M10_M11, "display_number": 3},
    {"module": run4_M12_ayumu, "display_number": 4},
    {"module": run1_M01_M02_kanna, "display_number": 5},
    {"module": run1_M13_M03, "display_number": 6},
]

# ===== フォースセンサーの初期化 =====
# ポートCに接続されたフォースセンサー（押すボタン）を使えるようにします
button = ForceSensor(Port.C)

# ===== 使い方の説明を表示 =====
print("=== プログラムセレクター ===")
print("LEFT/RIGHT: プログラム選択")
print("フォースセンサー: プログラム実行")


# ===== ロボットをリセットする関数（非同期版） =====
async def reset_robot():
    """
    ロボットを初期状態に戻す関数（非同期版）

    【asyncとは？】
    「async」は「非同期（ひどうき）」という意味です。
    通常の関数（def）と違い、他の作業と同時に実行できます。

    【やること】
    - ロボットの動きを停止
    - 走行距離などをリセット
    - ジャイロセンサー（向き）を0度にリセット
    """
    try:
        robot.stop()  # ロボットの動きを停止
        robot.reset()  # ロボットの走行距離などをリセット
        hub.imu.reset_heading(0)  # ジャイロセンサー（向き）を0度にリセット
        print("ロボットリソースをリセットしました")
    except Exception as e:
        # エラーが発生した場合はメッセージを表示
        print(f"リセットエラー: {e}")


# ===== センサーログを記録するタスク =====
async def sensor_logger_task():
    """
    センサーの値を定期的にコンピューターの画面に表示する関数

    【この関数の役割】
    ロボットが動いている間、センサーの値を0.2秒ごとに記録します。
    ビデオカメラが動画を撮影するように、ロボットの動きを記録できます。

    【記録される情報】
    1. 経過時間（何ミリ秒経ったか）
    2. dist（ロボットが進んだ距離）
    3. heading（ロボットの向き、0度が正面）
    4. L（左タイヤが回転した角度）
    5. R（右タイヤが回転した角度）

    【出力例】
    LOG[ 1000ms]: dist= 150 mm  heading=   0°  L=  720°  R=  720°
    ↑ 1秒後、150mm進んだ、向きは0度、タイヤは2回転（720度）

    【いつ役立つ？】
    - ロボットがまっすぐ進まないとき → headingを見て曲がり具合を確認
    - 目標距離に届かないとき → distを見て実際の距離を確認
    - プログラムのバグを探すとき → 数値を見て原因を特定

    【非同期処理の仕組み】
    この関数は「タスク」として、ロボットの動作と「同時に」実行されます。
    料理で「お湯を沸かしながら野菜を切る」ように、2つのことを並行して行います。
    """
    print("--- センサーログタスク開始 ---")

    # ----- 経過時間を測るタイマーを準備 -----
    logger_timer = StopWatch()  # ストップウォッチを作成
    logger_timer.reset()  # タイマーを0にリセット

    # ----- 永遠にログを記録し続けるループ -----
    while True:  # プログラムが終了するまで継続的にログを出力
        # 各センサーの値を読み取る
        elapsed_time = logger_timer.time()  # 経過時間（ミリ秒）
        heading = hub.imu.heading()  # ロボットの向き（度）
        left_deg = left_wheel.angle()  # 左タイヤの回転角度（度）
        right_deg = right_wheel.angle()  # 右タイヤの回転角度（度）
        dist = robot.distance()  # 走行距離（mm）

        # 読み取った値を画面に表示（フォーマットを整えて見やすく）
        print(
            f"LOG[{elapsed_time:5.0f}ms]: dist={dist:4.0f} mm  heading={heading:4.0f}°  L={left_deg:5.0f}°  R={right_deg:5.0f}°"
        )

        # 0.2秒（200ミリ秒）待機して、次の記録まで待つ
        # awaitをつけることで、待っている間に他のタスク（ロボットの動作）が実行できる
        await wait(200)


# ===== セレクタータスク（プログラム選択と実行） =====
async def selector_task():
    """
    プログラムを選択して実行するタスク（非同期版）

    【この関数の役割】
    通常版のselector.pyと同じ機能を、非同期処理で実現します。
    左右ボタンでプログラムを選び、フォースセンサーで実行します。

    【通常版との違い】
    - すべての処理に「await」がついている（他のタスクと同時実行できる）
    - センサーログと並行して動く
    """
    program_id = 0  # 現在選択されているプログラムの番号
    max_programs = len(programs) - 1  # プログラムの総数-1

    # ----- メインループ（永遠に繰り返す） -----
    while True:
        # ----- 現在のプログラム情報を取得 -----
        current_program = programs[program_id]  # 選択中のプログラム

        # display_numberが設定されていれば、それをハブに表示
        # 設定されていなければ、program_idを表示
        display_num = current_program.get("display_number", program_id)
        hub.display.char(str(display_num))  # ハブに番号を表示

        # ----- ハブのボタン入力をチェック -----
        pressed_buttons = hub.buttons.pressed()  # 押されているボタンを確認

        # 【右ボタンが押された場合】次のプログラムに進む
        if Button.RIGHT in pressed_buttons:
            # プログラム番号を1つ増やす（最後まで行ったら0に戻る）
            program_id = (program_id + 1) % (max_programs + 1)
            hub.light.on(Color.GREEN)  # ハブのライトを緑色に点灯
            await wait(100)  # 0.1秒待つ（awaitで他のタスクに譲る）
            hub.light.off()  # ライトを消す
            print(f"→ プログラム {program_id} に変更")

        # 【左ボタンが押された場合】前のプログラムに戻る
        elif Button.LEFT in pressed_buttons:
            # プログラム番号を1つ減らす（0より前に行ったら最後に戻る）
            program_id = (program_id - 1) if program_id > 0 else max_programs
            hub.light.on(Color.BLUE)  # ハブのライトを青色に点灯
            await wait(100)  # 0.1秒待つ（awaitで他のタスクに譲る）
            hub.light.off()  # ライトを消す
            print(f"← プログラム {program_id} に変更")

        # ----- フォースセンサーでプログラム実行 -----
        # フォースセンサーが0.5以上の力で押されたら、プログラムを実行
        if await button.force() >= 0.5:
            hub.light.on(Color.RED)  # ハブのライトを赤色に点灯（実行中を示す）
            print(f"=== プログラム {program_id} を実行中 ===")

            try:
                # ----- 実行前の準備 -----
                await reset_robot()  # ロボットをリセット（awaitで待つ）
                await wait(50)  # リセット後に少し待機（0.05秒）

                # ----- プログラムを実行 -----
                # モジュールからrun関数を取得（例: run1_M01_M02_kanna.run）
                function = current_program["module"].run

                # パラメータ（引数）がある場合は渡して実行、ない場合はロボット情報だけ渡す
                if "params" in current_program:
                    await function(
                        *current_program["params"],
                        hub,
                        robot,
                        left_wheel,
                        right_wheel,
                        left_lift,
                        right_lift,
                    )
                else:
                    await function(hub, robot, left_wheel, right_wheel, left_lift, right_lift)

                print(f"=== プログラム {program_id} 実行完了 ===")

            except Exception as e:
                # ----- エラーが発生した場合の処理 -----
                print(f"エラー: {e}")  # エラーメッセージを表示
                hub.light.on(Color.RED)  # 赤いライトを点灯してエラーを知らせる
                await wait(500)  # 0.5秒待つ
                hub.light.off()  # ライトを消す
            finally:
                # ----- 実行後の後処理（必ず実行される） -----
                try:
                    await reset_robot()  # 実行後にロボットをリセット
                    await wait(50)  # リセット後に少し待機（0.05秒）
                except Exception as e:
                    print(f"リセットエラー: {e}")

            hub.light.off()  # ライトを消す
            print("セレクターに戻りました")

        # ----- ボタン連打防止のための待機 -----
        await wait(50)  # 0.05秒待つ（awaitで他のタスクに譲る）


# ========================================
# ===== プログラムのメイン実行部分 =====
# ========================================

# ここで、開発モード（dev）の設定に応じて、実行する内容を切り替えます

if dev:
    # ----- 開発モード（dev=True）の場合 -----
    # センサーログタスクとセレクタータスクを「同時に」実行します
    #
    # 【multitaskの仕組み】
    # multitask()は、複数のタスクを並行して実行する機能です。
    # 料理で「パスタを茹でながら、ソースを作る」ように、
    # 「センサーログを記録しながら、プログラムを選択・実行する」ことができます。
    #
    # 【実行されるタスク】
    # 1. sensor_logger_task() : 0.2秒ごとにセンサー値を画面に表示
    # 2. selector_task() : ボタンでプログラムを選択・実行
    #
    # この2つが同時に動くので、ロボットが動いている間もログが記録されます。
    print("--- 開発モードで起動（センサーログ有効） ---")
    run_task(
        multitask(
            sensor_logger_task(),  # センサー値を継続的にログに出力するタスク
            selector_task(),  # プログラム選択・実行タスク
        )
    )
else:
    # ----- 本番モード（dev=False）の場合 -----
    # セレクタータスクのみを実行します（センサーログなし）
    #
    # 【なぜログをオフにする？】
    # センサーログは便利ですが、コンピューターへのデータ送信に時間がかかります。
    # 競技本番では、ログは不要なので、オフにすると動作が少し速くなります。
    #
    # 【実行されるタスク】
    # 1. selector_task() : ボタンでプログラムを選択・実行（通常版と同じ）
    print("--- 本番モードで起動（センサーログなし） ---")
    run_task(
        multitask(
            selector_task()  # プログラム選択・実行タスク（単独）
        )
    )

# ========================================
# プログラムはここまで
# ========================================
