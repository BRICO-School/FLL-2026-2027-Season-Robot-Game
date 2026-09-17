"""90° ずつ止まりながら 5 周を「回り足りなさの補正あり」で回る。補正が合っていれば元の向きに戻る。中身は run_gyro_scale_check.py

【更新履歴】
- 2026-09-17: 旋回補正付きで90度ずつ段階的に回るスクリプトを新規追加した
"""

from run_gyro_scale_check import main

main("steps", True)
