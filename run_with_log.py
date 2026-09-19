"""
【ログ保存付き実行スクリプト】
pybricksdev の実行ログを docs/logs/ に自動保存するラッパー。

ターミナルへの出力はそのまま表示しつつ、
同じ内容をタイムスタンプ付きファイルに保存する。

走行が終わったあと、成否（o=成功 / x=失敗 / d=途中まで）を 1 キーで聞いて
docs/trials/trials.csv に記録し、走行したコードのコピーも残す。
（仕様: docs/trial_log_spec.md）

【使い方（コマンドライン）】
  python run_with_log.py run_M01_kidachi.py --name "Pybricks Hub4"
  python run_with_log.py run_lift_motor_test.py --name "Pybricks Hub4" --no-trial
      ↑ 機構テストなど、成否を記録したくないときは --no-trial
        （環境変数 TRIAL_LOG=0 でも同じ）

【サブフォルダのスクリプト（verification/ など）】
  python run_with_log.py verification/run_gyro_motor_check.py --name "Pybricks Hub3" --no-trial
  pybricksdev は「送るスクリプトと同じフォルダ」からしか import を探さないので、
  サブフォルダのスクリプトはそのままだと `from setup import ...` が見つからない。
  そこで .hub_stage/ に「ルートの setup.py ＋ そのフォルダの *.py」を写してから送る（stage_for_hub）。
  ログの保存先（docs/logs/<スクリプト名>/）は変わらない。

【使い方（VS Code）】
  launch.json に用意された「📝 Robot X + Log」構成で実行すると、
  開いているファイルが自動的にログ付きで実行される。

【保存先】
  docs/logs/<スクリプト名>/<YYYYMMDD_HHMMSS>.log   … 実行ログ
  docs/trials/trials.csv                            … 試行の記録（1 行 = 1 走行）
  docs/trials/snapshots/<code_hash>/                … 走行したコードのコピー

※ このファイルは PC 側だけで動く。ハブへ送るコード（setup.py / run_*.py）には
   一切手を入れないので、ロボットの動きには影響しない。

【更新履歴】
- 2026-09-09: 走行結果の記録とコードスナップショット保存機能を追加した。
- 2026-09-09: セレクター経由のプログラム実行ログの記録に対応した
- 2026-09-09: Ctrl+Cによる中断時にプロセスを安全に終了する処理を追加。
- 2026-09-19: サブフォルダのスクリプト実行時にルートの設定ファイルを同梱して転送する処理を追加
"""

import csv
import hashlib
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime

# ===== 試行記録の設定 =====
TRIALS_DIR = os.path.join("docs", "trials")
TRIALS_CSV = os.path.join(TRIALS_DIR, "trials.csv")
SNAPSHOTS_DIR = os.path.join(TRIALS_DIR, "snapshots")

CSV_COLUMNS = [
    "trial_id",
    "date",
    "time",
    "script",
    "mission",
    "member",
    "hub",
    "result",
    "elapsed_sec",
    "exit_code",
    "commit",
    "note",
    "log_path",
    "code_hash",
    "snapshot",
    "via",  # selector 経由なら "selector P1" のように入る。直接実行なら空
]

# selector.py が画面に出す行（この文字列を PC 側で読むだけ。ハブ側は変更しない）
SELECTOR_START = re.compile(r"=== プログラム (\d+) を実行中 ===")
SELECTOR_DONE = re.compile(r"=== プログラム (\d+) 実行完了 ===")
SELECTOR_ERROR = re.compile(r"^エラー: ")

# 入力キー → result 列の値
RESULT_KEYS = {
    "o": "success",
    "x": "fail",
    "d": "partial",
    "e": "error",
    "s": None,  # 記録しない
}


# ===== ファイル名からの推定 =====
def guess_mission(script_name):
    """run_M01_kidachi → 'M01'、run1_M05_M06_kidachi → 'M05+M06'。無ければ ''。"""
    found = re.findall(r"[Mm]\d{1,2}", script_name)
    return "+".join(m.upper() for m in found)


def guess_member(script_name):
    """run_M01_kidachi → 'kidachi'、run_keiichiro_M03 → 'keiichiro'。無ければ ''。"""
    name = re.sub(r"^run\d*_", "", script_name)
    skip = {
        "new",
        "modified",
        "test",
        "settings",
        "first",
        "selector",
        "template",
        "left",
        "right",
        "arm",
        "lift",
        "motor",
        "wheel",
        "sensor",
    }
    for token in name.split("_"):
        if re.fullmatch(r"[Mm]\d{1,2}", token):
            continue
        if token.lower() in skip or not token.isalpha():
            continue
        return token
    return ""


def git_short_head(cwd):
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return out.stdout.strip() if out.returncode == 0 else ""
    except Exception:
        return ""


# ===== コードのスナップショット =====
def snapshot_files(root, run_file):
    """走行に関わったファイルの一覧（root からの相対パス）を返す。"""
    files = [os.path.relpath(os.path.abspath(run_file), root)]
    if os.path.exists(os.path.join(root, "setup.py")):
        files.append("setup.py")
    # selector.py 経由なら、登録されている run モジュールも一緒に残す
    if os.path.basename(run_file) == "selector.py":
        with open(os.path.join(root, "selector.py"), encoding="utf-8") as f:
            for line in f:
                m = re.match(r"\s*import\s+(run\w+)\s*(#.*)?$", line)
                if m and os.path.exists(os.path.join(root, m.group(1) + ".py")):
                    files.append(m.group(1) + ".py")
    # 重複を除いて順序を保つ
    seen = []
    for p in files:
        if p not in seen:
            seen.append(p)
    return seen


def selector_programs(root):
    """selector.py の programs リストから、添字順に (モジュール名, 画面の番号) を返す。"""
    names = []
    path = os.path.join(root, "selector.py")
    if not os.path.exists(path):
        return names
    with open(path, encoding="utf-8") as f:
        in_list = False
        for line in f:
            if re.match(r"\s*programs\s*=\s*\[", line):
                in_list = True
                continue
            if in_list:
                if line.strip().startswith("]"):
                    break
                m = re.search(r'"module"\s*:\s*(\w+)', line)
                if m:
                    d = re.search(r'"display_number"\s*:\s*(\d+)', line)
                    names.append((m.group(1), d.group(1) if d else str(len(names))))
    return names


class SelectorWatcher:
    """selector.py の表示行を読んで「何番を・いつ・どうなったか」を控える。

    出力を眺めるだけで、ハブへは何も送らない。
    """

    def __init__(self):
        self.runs = []  # {"index", "start", "end", "error"}

    def feed(self, line):
        m = SELECTOR_START.search(line)
        if m:
            self.runs.append(
                {"index": int(m.group(1)), "start": datetime.now(), "end": None, "error": False}
            )
            return
        if not self.runs or self.runs[-1]["end"] is not None:
            return
        if SELECTOR_ERROR.search(line):
            self.runs[-1]["error"] = True
        elif SELECTOR_DONE.search(line) or "セレクターに戻りました" in line:
            self.runs[-1]["end"] = datetime.now()


def save_snapshot(root, files):
    """ファイル内容のハッシュを計算し、未保存ならコピーする。(hash, dir) を返す。"""
    h = hashlib.sha256()
    for rel in files:
        with open(os.path.join(root, rel), "rb") as f:
            h.update(rel.encode("utf-8") + b"\0" + f.read() + b"\0")
    code_hash = h.hexdigest()[:8]
    snap_dir = os.path.join(root, SNAPSHOTS_DIR, code_hash)
    if not os.path.isdir(snap_dir):
        os.makedirs(snap_dir)
        for rel in files:
            shutil.copy2(os.path.join(root, rel), os.path.join(snap_dir, os.path.basename(rel)))
    return code_hash, os.path.join(SNAPSHOTS_DIR, code_hash).replace(os.sep, "/")


# ===== CSV =====
def append_trial(root, row):
    path = os.path.join(root, TRIALS_CSV)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    is_new = not os.path.exists(path)
    with open(path, "a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        if is_new:
            w.writeheader()
        w.writerow(row)


def today_tally(root, date, mission):
    """その日・そのミッションの (成功数, 試行数) を返す。error は数えない。"""
    path = os.path.join(root, TRIALS_CSV)
    if not os.path.exists(path):
        return 0, 0
    ok = total = 0
    with open(path, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r.get("date") != date or r.get("mission") != mission:
                continue
            if r.get("result") in ("success", "fail", "partial"):
                total += 1
                if r["result"] == "success":
                    ok += 1
    return ok, total


# ===== 成否の入力 =====
def ask_result(default_key):
    """1 キーで成否を聞く。Ctrl+C / EOF なら None（記録しない）。"""
    prompt = f"結果 [{default_key}] > "
    while True:
        try:
            key = input(prompt).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return None
        if key == "":
            key = default_key
        if key in RESULT_KEYS:
            return RESULT_KEYS[key]
        print("   o / x / d / e / s のどれかを入力してね")


def ask_note():
    try:
        return input("メモ（なければ Enter）> ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return ""


def write_trial(
    root, run_file, hub_args, start_time, elapsed, exit_code, log_path, result, note, via=""
):
    """1 試行分を CSV に追記し、コードのコピーを残す。"""
    script_base = os.path.basename(run_file)
    script_name = os.path.splitext(script_base)[0]
    mission = guess_mission(script_name)
    code_hash, snap_rel = save_snapshot(root, snapshot_files(root, run_file))
    date = start_time.strftime("%Y-%m-%d")
    row = {
        "trial_id": start_time.strftime("%Y%m%d_%H%M%S"),
        "date": date,
        "time": start_time.strftime("%H:%M:%S"),
        "script": script_base,
        "mission": mission,
        "member": guess_member(script_name),
        "hub": " ".join(a for a in hub_args if a != "--name"),
        "result": result,
        "elapsed_sec": f"{elapsed:.1f}",
        "exit_code": exit_code,
        "commit": git_short_head(root),
        "note": note,
        "log_path": os.path.relpath(log_path, root).replace(os.sep, "/"),
        "code_hash": code_hash,
        "snapshot": snap_rel,
        "via": via,
    }
    append_trial(root, row)
    ok, total = today_tally(root, date, mission)
    name = mission or script_base
    print(f"📊 記録しました: {name} {result}（今日 {name}: {ok}/{total} 成功）")
    print(f"📊 コード: {snap_rel}")


def print_header(label):
    print()
    print("─" * 40)
    print(f"🏁 結果を記録します: {label}")
    print("   o=成功  x=失敗  d=途中まで  e=動かなかった  s=記録しない")


def record_trial(root, run_file, hub_args, start_time, elapsed, exit_code, log_path):
    """run_*.py を 1 つ走らせたあとの記録（1 プロセス = 1 試行）。"""
    script_base = os.path.basename(run_file)
    mission = guess_mission(os.path.splitext(script_base)[0])
    print_header(f"{script_base} ({mission})" if mission else script_base)
    result = ask_result("e" if exit_code != 0 else "o")
    if result is None:
        print("📊 記録しませんでした")
        return
    note = ask_note()
    write_trial(root, run_file, hub_args, start_time, elapsed, exit_code, log_path, result, note)


def record_selector_trials(root, hub_args, watcher, exit_code, log_path):
    """selector.py の通し練習: 走ったプログラムごとに順番に成否を聞く。"""
    modules = selector_programs(root)
    print()
    print("─" * 40)
    print(f"🏁 通し練習の結果を記録します（{len(watcher.runs)} 回走りました）")
    print("   o=成功  x=失敗  d=途中まで  e=動かなかった  s=記録しない")
    for i, run in enumerate(watcher.runs, 1):
        idx = run["index"]
        module, shown = modules[idx] if idx < len(modules) else (f"program{idx}", str(idx))
        run_file = os.path.join(root, module + ".py")
        if not os.path.exists(run_file):
            run_file = os.path.join(root, "selector.py")
        mission = guess_mission(module)
        end = run["end"] or datetime.now()
        elapsed = (end - run["start"]).total_seconds()
        label = f"{mission} / {module}" if mission else module
        print()
        print(
            f"[{i}/{len(watcher.runs)}] 画面の番号 {shown}: {label}"
            + ("  ⚠ エラーあり" if run["error"] else "")
        )
        result = ask_result("x" if run["error"] else "o")
        if result is None:
            print("📊 記録しませんでした")
            continue
        note = ask_note()
        write_trial(
            root,
            run_file,
            hub_args,
            run["start"],
            elapsed,
            exit_code,
            log_path,
            result,
            note,
            via=f"selector P{shown}",
        )


STAGE_DIR = ".hub_stage"


def stage_for_hub(run_file, root):
    """サブフォルダのスクリプトを、ルートの setup.py と同じフォルダに写して、その写しのパスを返す。

    ルート直下のスクリプトは何もせずそのまま返す。
    """
    src = os.path.abspath(run_file)
    src_dir = os.path.dirname(src)
    if os.path.normcase(src_dir) == os.path.normcase(os.path.abspath(root)):
        return run_file
    stage = os.path.join(root, STAGE_DIR)
    shutil.rmtree(stage, ignore_errors=True)
    os.makedirs(stage)
    for name in os.listdir(src_dir):
        if name.endswith(".py"):
            shutil.copy2(os.path.join(src_dir, name), os.path.join(stage, name))
    # ルートの setup.py を最後に写す（サブフォルダに同じ名前があっても、本番の setup.py を使う）
    shutil.copy2(os.path.join(root, "setup.py"), os.path.join(stage, "setup.py"))
    return os.path.join(stage, os.path.basename(src))


def main():
    args = sys.argv[1:]
    no_trial = "--no-trial" in args
    args = [a for a in args if a != "--no-trial"]
    if os.environ.get("TRIAL_LOG", "1") == "0":
        no_trial = True

    if len(args) < 3:
        print("Usage: python run_with_log.py <run_file.py> --name <hub_name> [--no-trial]")
        sys.exit(1)

    run_file = args[0]
    hub_args = args[1:]

    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_name = os.path.splitext(os.path.basename(run_file))[0]
    log_dir = os.path.join(script_dir, "docs", "logs", script_name)
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(log_dir, f"{timestamp}.log")

    hub_file = stage_for_hub(run_file, script_dir)
    cmd = [sys.executable, "-m", "pybricksdev", "run", "ble", hub_file] + hub_args

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

        watcher = SelectorWatcher()
        try:
            for line in process.stdout:
                print(line, end="")
                f.write(line)
                watcher.feed(line)  # 読むだけ。ハブとの通信には触らない
        except KeyboardInterrupt:
            # Ctrl+C で止めたとき: pybricksdev を終わらせてから、記録の入力に進む
            print("\n⏹ 停止しました（pybricksdev を終了します）")
            f.write("\n[Ctrl+C で停止]\n")
            try:
                process.terminate()
                process.wait(timeout=5)
            except Exception:
                process.kill()

        process.wait()

        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()

        f.write(f"\n{'=' * 50}\n")
        f.write(f"終了コード: {process.returncode}\n")
        f.write(f"終了日時  : {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"実行時間  : {elapsed:.1f} 秒\n")

    print()
    print(f"📝 ログ保存完了: {log_path}")

    # ===== 走行後の試行記録（ロボットの実行はもう終わっている） =====
    if not no_trial:
        try:
            if os.path.basename(run_file) == "selector.py" and watcher.runs:
                record_selector_trials(script_dir, hub_args, watcher, process.returncode, log_path)
            else:
                record_trial(
                    script_dir,
                    run_file,
                    hub_args,
                    start_time,
                    elapsed,
                    process.returncode,
                    log_path,
                )
        except Exception as e:  # 記録の失敗で終了コードを変えない
            print(f"⚠ 試行記録に失敗しました（走行結果には影響しません）: {e}")

    sys.exit(process.returncode)


if __name__ == "__main__":
    main()
