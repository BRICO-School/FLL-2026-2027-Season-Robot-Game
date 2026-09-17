"""ハブに保存されている IMU の設定を読むだけ（モーターは動かさない・何も書きかえない）

【更新履歴】
- 2026-09-17: ハブのIMU設定と電池電圧を出力するスクリプトを新規追加した
"""

from pybricks.hubs import PrimeHub

hub = PrimeHub()
print("# imu.settings:", hub.imu.settings())
print("# 電池:", hub.battery.voltage(), "mV")
