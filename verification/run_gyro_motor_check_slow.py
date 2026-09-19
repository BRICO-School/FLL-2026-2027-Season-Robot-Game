"""止まらずに 5 周を、回転速度 100 deg/s（既定 250 の 4 割）で → 手で定規に合わせ直す。中身は run_gyro_motor_check.py

【更新履歴】
- 2026-09-17: 低速で旋回動作を確認するスクリプトを新規作成した。
"""

from run_gyro_motor_check import main

main("spin", 100)
