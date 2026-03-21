"""
【ログ保存付き実行スクリプト】
pybricksdev の実行ログを docs/logs/ に自動保存するラッパー。

ターミナルへの出力はそのまま表示しつつ、
同じ内容をタイムスタンプ付きファイルに保存する。

【使い方（コマンドライン）】
  python run_with_log.py run_M01_kidachi.py --name "Pybricks Hub4"

【使い方（VS Code）】
  launch.json に用意された「📝 Robot X + Log」構成で実行すると、
  開いているファイルが自動的にログ付きで実行される。

【保存先】
  docs/logs/<スクリプト名>/<YYYYMMDD_HHMMSS>.log
"""

import os
import subprocess
import sys
from datetime import datetime


def main():
    if len(sys.argv) < 4:
        print("Usage: python run_with_log.py <run_file.py> --name <hub_name>")
        sys.exit(1)

    run_file = sys.argv[1]
    hub_args = sys.argv[2:]

    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_name = os.path.splitext(os.path.basename(run_file))[0]
    log_dir = os.path.join(script_dir, "docs", "logs", script_name)
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(log_dir, f"{timestamp}.log")

    cmd = [sys.executable, "-m", "pybricksdev", "run", "ble", run_file] + hub_args

    print(f"📝 ログ保存先: {log_path}")
    print(f"📝 実行コマンド: pybricksdev run ble {run_file} {' '.join(hub_args)}")
    print()

    start_time = datetime.now()

    with open(log_path, "w", encoding="utf-8") as f:
        f.write("=== 実行ログ ===\n")
        f.write(f"スクリプト: {os.path.basename(run_file)}\n")
        f.write(f"実行日時 : {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"ハブ     : {' '.join(hub_args)}\n")
        f.write(f"{'=' * 50}\n\n")

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        for line in process.stdout:
            print(line, end="")
            f.write(line)

        process.wait()

        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()

        f.write(f"\n{'=' * 50}\n")
        f.write(f"終了コード: {process.returncode}\n")
        f.write(f"終了日時  : {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"実行時間  : {elapsed:.1f} 秒\n")

    print()
    print(f"📝 ログ保存完了: {log_path}")

    sys.exit(process.returncode)


if __name__ == "__main__":
    main()
