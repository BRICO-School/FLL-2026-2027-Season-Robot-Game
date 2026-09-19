"""始めのジャイロの待ち（2 秒）を飛ばして、セレクターの形でジャイロの状態を確かめる。中身は run_gyro_selector_check.py

待ちを無くしても、ボタンを押すまでの時間だけで状態 B になるかを見る。

【更新履歴】
- 2026-09-19: ジャイロの静止待ちを省略して状態を確認する検証スクリプトを追加
"""

from run_gyro_selector_check import main

main(settle=False)
