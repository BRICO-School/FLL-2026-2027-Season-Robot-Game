"""始めに 3 秒さわらずに待ってから、5 周 → 当て直し を 1 回。中身は run_gyro_state_repeat.py

何秒止まっていれば状態 B（正確な目盛り）で始まるかを探す。10 秒なら B・0 秒なら A（9/19）。

【更新履歴】
- 2026-09-19: 開始前に3秒待機してジャイロ状態確認を行うスクリプトを追加した
"""

from run_gyro_state_repeat import main

main(start_wait_ms=3000, repeats=1)
