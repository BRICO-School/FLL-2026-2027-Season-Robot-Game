"""90° ずつ止まりながら 5 周（止まる回数 20）。中身は run_gyro_scale_check.py。止まらずに 5 周と比べて「止まるたびのズレ」を出す

【更新履歴】
- 2026-09-17: 段階的な停止旋回でジャイロのズレを検証するスクリプトを新規追加
"""

from run_gyro_scale_check import main

main("steps")
