"""待たずにすぐ 5 周 → 当て直し を 2 回。中身は run_gyro_state_repeat.py

run_gyro_state_repeat_wait.py（始めに 10 秒待つ）と同じ日に交互に走らせて比べるための対照。

【更新履歴】
- 2026-09-19: 開始待機なしで2回繰り返す比較検証用スクリプトを新規追加した
"""

from run_gyro_state_repeat import main

main(start_wait_ms=0, repeats=2)
