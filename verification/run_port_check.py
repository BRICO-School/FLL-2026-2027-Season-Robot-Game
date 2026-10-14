"""ハブのポート A〜F に何がつながっているかを読むだけ（モーターは動かさない・何も書きかえない）

【使い方】
  ハブごとに 1 回ずつ走らせて、最後の「# まとめ:」の行をくらべる（同じなら、つながっているものは同じ）。
  python run_with_log.py verification/run_port_check.py --name "Pybricks Hub" --no-trial
  python run_with_log.py verification/run_port_check.py --name "Pybricks Hub2" --no-trial
  python run_with_log.py verification/run_port_check.py --name "Pybricks Hub3" --no-trial

  わかるのは「どのポートに、どの種類のモーター・センサーがあるか」（デバイスの ID）。
  モーターの向き・ギア・ケーブルの長さ・アームの形まではわからない。

【更新履歴】
- 2026-10-14: ハブの各ポートに接続された機器を確認するスクリプトを追加した。
"""

from pybricks.hubs import PrimeHub
from pybricks.iodevices import PUPDevice
from pybricks.parameters import Port
from pybricks.pupdevices import Motor

# デバイスの ID → 名前（LEGO Powered Up の型番号）
DEVICE_NAMES = {
    1: "WeDo 2.0 モーター",
    2: "トレインモーター",
    8: "ライト",
    37: "BOOST カラー＆距離センサー",
    38: "BOOST インタラクティブモーター",
    46: "Technic L モーター",
    47: "Technic XL モーター",
    48: "SPIKE M モーター",
    49: "SPIKE L モーター",
    61: "SPIKE カラーセンサー",
    62: "SPIKE 距離センサー",
    63: "SPIKE フォースセンサー",
    64: "3x3 カラーライトマトリックス",
    65: "SPIKE S モーター",
    75: "Technic M アンギュラーモーター（グレー）",
    76: "Technic L アンギュラーモーター（グレー）",
}

# setup.py の initialize_robot() での役目
ROLES = {
    "A": "右リフト",
    "B": "右タイヤ",
    "C": "（使っていない）",
    "D": "（使っていない）",
    "E": "左リフト",
    "F": "左タイヤ",
}

ENODEV = 19  # ポートに何もつながっていないときのエラー番号

hub = PrimeHub()
print("# ハブ:", hub.system.name())
try:
    from pybricks import version

    print("# ファーム:", version)
except ImportError:
    pass
print("# 電池:", hub.battery.voltage(), "mV")

summary = []
for name, port in (
    ("A", Port.A),
    ("B", Port.B),
    ("C", Port.C),
    ("D", Port.D),
    ("E", Port.E),
    ("F", Port.F),
):
    try:
        device_id = PUPDevice(port).info()["id"]
        label = DEVICE_NAMES.get(device_id, "わからない種類")
        summary.append(name + "=" + str(device_id))
    except OSError as e:
        if e.args and e.args[0] == ENODEV:
            device_id = None
            label = "なし"
            summary.append(name + "=-")
        else:
            # PUPDevice で読めないときは、モーターとして開けるかだけ確かめる
            try:
                Motor(port)
                label = "モーター（種類は読めなかった）"
                summary.append(name + "=motor")
            except OSError:
                label = "読めなかった（" + str(e) + "）"
                summary.append(name + "=?")
            device_id = None
    print("# ポート", name, ":", label, "/ ID:", device_id, "/ setup.py では", ROLES[name])

print("# まとめ:", " ".join(summary))
