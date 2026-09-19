"""90° ずつ止まりながら 5 周を「補正あり」で → 手で定規に合わせ直す。中身は run_gyro_motor_check.py

【更新履歴】
- 2026-09-17: 補正ありで段階的に旋回確認を行うスクリプトを新規追加した
"""

from run_gyro_motor_check import main

main("steps", None, True)
