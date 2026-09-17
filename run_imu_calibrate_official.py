"""
【Pybricks 公式の IMU 3 軸校正を走らせる】（2026-09-17）

ハブを機体から外し、平らな机の上で、画面の指示どおりに 90° ずつ「手前に転がす」。
X・Y・Z の 3 軸 × 8 回（4 面 × 2 周）。持ち上げると "Lifted it!" で止まるので、机から離さずに転がす。
終わると結果がハブに保存される（ファームを入れ直すまで残る）:
  angular_velocity_bias / angular_velocity_scale / acceleration_correction

校正前の値（2026-09-17・Hub3）: bias (0.1389356, -1.317983, -0.2881232) / scale (360, 360, 360) /
  acceleration (9806.65, -9806.65, 9806.65, -9806.65, 9806.65, -9806.65) / heading_correction 360
元に戻すときは hub.imu.settings(...) に上の値を入れる。

【更新履歴】
- 2026-09-17: 公式のIMU校正を実行するスクリプトを新規追加した
"""

from pybricks.hubs import PrimeHub

hub = PrimeHub()
print("# 校正前の imu.settings:", hub.imu.settings())

import _imu_calibrate  # noqa: E402, F401  公式の校正手順（指示は英語で表示される）

print("# 校正後の imu.settings:", hub.imu.settings())
