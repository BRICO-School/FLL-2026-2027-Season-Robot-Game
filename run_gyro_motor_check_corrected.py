"""止まらずに 5 周を「回り足りなさの補正あり」で → 手で定規に合わせ直す。合っていれば合わせ直しはほぼ 0°。中身は run_gyro_motor_check.py

【更新履歴】
- 2026-09-17: 補正を有効にして旋回動作を確認するスクリプトを追加した
"""

from run_gyro_motor_check import main

main("spin", None, True)
