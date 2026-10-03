"""
【ログ保存付き実行スクリプト】
pybricksdev の実行ログを docs/logs/ に自動保存するラッパー。

ターミナルへの出力はそのまま表示しつつ、
同じ内容をタイムスタンプ付きファイルに保存する。

走行が終わったあと、成否（o=成功 / x=失敗 / d=途中まで / -=届かなかった）を
ミッションごとに 1 キーずつ聞いて docs/trials/trials.csv に記録し、走行したコードのコピーも残す。
（仕様: docs/trial_log_spec.md。§9 がミッションごとの成否）

【ミッションごとの成否】（2026-10-03）
  ミッションと順番は run ファイルの名前から決める（run_M01M02M03_kanna.py → M01 → M02 → M03）。
  名前の順に「M01 の結果 >」「M02 の結果 >」と聞く。1 ミッションの run は 1 回だけ。
  どの質問でも b で 1 つ前に戻れる。最後に確認の画面が出て、Enter を押すまで何も書かない。
  記録したあとで直すときは scripts/trial_fix.py。聞き方と読み書きの部品は scripts/trial_results.py。

【本番でもかかる時間】（2026-10-03）
  ハブの「=== ロボット初期化完了 ===」（setup.py）から「# 走行完了！」（run ファイルの run() の最後）までを、
  PC に行が届いた時刻で測って run_sec 列に入れる（ハブを探す・接続・送る・ジャイロの待ちは入らない）。
  行がまとめて遅れて届かないよう、pybricksdev は -u と PYTHONUNBUFFERED=1 で起動する。
  ログの最後に「接続〜初期化完了」と「走行」の秒数を書く。セレクター経由はプログラムごとの「実行中 → 実行完了」。

【使い方（コマンドライン）】
  python run_with_log.py run_M01_kidachi.py --name "Pybricks Hub4"
  python run_with_log.py verification/run_lift_motor_test.py --name "Pybricks Hub4" --no-trial
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
  docs/trials/dashboard.html                        … 集計ダッシュボード（記録のたびに作り直す。git には入れない）
  docs/trials/dashboard_coach.html                  … 名前に coach が入る run ファイルだけの集計（同上。チームの方には数えない）

※ このファイルは PC 側だけで動く。ハブへ送るコード（setup.py / run_*.py）には
   一切手を入れないので、ロボットの動きには影響しない。

【更新履歴】
- 2026-09-09: 走行結果の記録とコードスナップショット保存機能を追加した。
- 2026-09-09: セレクター経由のプログラム実行ログの記録に対応した
- 2026-09-09: Ctrl+Cによる中断時にプロセスを安全に終了する処理を追加。
- 2026-09-19: サブフォルダのスクリプト実行時にルートの設定ファイルを同梱して転送する処理を追加
- 2026-09-19: 使い方の説明にあるテストスクリプトのパスを更新した
- 2026-09-19: 走行記録時に集計ダッシュボードを自動更新する処理を追加した
- 2026-10-02: 名前に coach が入る run ファイルの記録を、コーチ確認用のダッシュボードに分けて作り直すようにした
- 2026-10-02: コーチ確認用の集計ダッシュボードを分けて自動生成するようにした。
- 2026-10-03: 走行後の成否をミッションごとに個別記録できるよう変更した。
- 2026-10-03: ロボットの実走行時間を計測して試行ログに記録する機能を追加した
"""

import csv
import hashlib
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts"))
import trial_results as tr  # noqa: E402  ミッションごとの成否（scripts/trial_results.py）

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
    "mission_results",  # ミッションごとの成否「M12=fail M11=success」（2026-10-03 追加）
    "run_sec",  # 本番でもかかる時間（初期化完了 → 走行完了。セレクターはプログラムの実行中 → 実行完了）（2026-10-03 追加）
]

# selector.py が画面に出す行（この文字列を PC 側で読むだけ。ハブ側は変更しない）
SELECTOR_START = re.compile(r"=== プログラム (\d+) を実行中 ===")
SELECTOR_DONE = re.compile(r"=== プログラム (\d+) 実行完了 ===")
SELECTOR_ERROR = re.compile(r"^エラー: ")

# 本番でもかかる時間を測る目じるし（ハブがもう出している行。ハブ側は変更しない）
INIT_DONE = "=== ロボット初期化完了 ==="  # setup.py の initialize_robot() の最後
RUN_DONE = "# 走行完了！"  # run ファイルの run() の最後（run_template.py の形）


# ===== ファイル名からの推定 =====
def guess_mission(script_name):
    """run_M01_kidachi → 'M01'、run_M01M02M03_kanna → 'M01+M02+M03'、run_M9_x → 'M09'。無ければ ''。"""
    return "+".join(tr.missions_in_name(script_name)[0])


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


class RunTimer:
    """ハブの行が PC に届いた時刻から、「接続〜初期化完了」と「走行（初期化完了 → 走行完了）」の秒数を測る。

    出力を眺めるだけで、ハブへは何も送らない。pybricksdev を -u で起動していないと、行がまとめて届いて測れない。
    """

    def __init__(self):
        self.start = time.monotonic()
        self.init_done = None
        self.run_done = None

    def feed(self, line):
        now = time.monotonic()
        if self.init_done is None and INIT_DONE in line:
            self.init_done = now
        elif self.init_done is not None and self.run_done is None and RUN_DONE in line:
            self.run_done = now

    def setup_sec(self):
        return self.init_done - self.start if self.init_done is not None else None

    def run_sec(self):
        if self.init_done is None or self.run_done is None:
            return None
        return self.run_done - self.init_done


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
    """trials.csv に 1 行足す。見出しに足りない列（mission_results など）があれば、見出しだけ先に足す。"""
    path = os.path.join(root, TRIALS_CSV)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    is_new = not os.path.exists(path)
    header = CSV_COLUMNS if is_new else tr.ensure_header(path, CSV_COLUMNS)
    with open(path, "a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
        if is_new:
            w.writeheader()
        w.writerow(row)


def today_tally(root, date, missions):
    """その日の、ミッションごとの (成功数, 試行数) を返す。届かなかった・動かなかったは数えない。"""
    path = os.path.join(root, TRIALS_CSV)
    out = {m: [0, 0] for m in missions}
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r.get("date") != date:
                continue
            for m, result in tr.results_of(r):
                if m in out and result in tr.COUNTED:
                    out[m][1] += 1
                    out[m][0] += result == "success"
    return out


def write_trial(
    root,
    run_file,
    hub_args,
    start_time,
    elapsed,
    exit_code,
    log_path,
    result,
    mission_results,
    note,
    via="",
    run_sec=None,
):
    """1 試行分を CSV に追記し、コードのコピーを残す。run_sec は本番でもかかる時間（測れなければ None）。"""
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
        "mission_results": mission_results,
        "run_sec": f"{run_sec:.1f}" if run_sec is not None else "",
    }
    append_trial(root, row)
    pairs = tr.results_of(row)
    what = tr.describe(pairs) if pairs else tr.RESULT_LABEL.get(result, result)
    tally = today_tally(root, date, [m for m, _ in pairs])
    today = "・".join(f"{m} {ok}/{n}" for m, (ok, n) in tally.items() if n)
    print(f"📊 記録しました: {what}" + (f"（今日の成功: {today}）" if today else ""))
    print(f"📊 コード: {snap_rel}")


def refresh_dashboard(root):
    """docs/trials/dashboard.html と dashboard_coach.html を作り直す（scripts/trial_dashboard.py）。失敗しても走行の記録には影響させない。"""
    try:
        sys.path.insert(0, os.path.join(root, "scripts"))
        import trial_dashboard

        trial_dashboard.build_all()
        print("📊 ダッシュボード: docs/trials/dashboard.html（ブラウザで開いて F5）")
        print(
            "   コーチ確認用（名前に coach が入る run ファイル）: docs/trials/dashboard_coach.html"
        )
    except Exception as e:
        print(f"⚠ ダッシュボードを作り直せませんでした: {e}")


def new_item(script_name, title, default_key, warning=""):
    """聞く 1 本ぶん。ミッションはファイル名から（名前の順に聞く）。名前の注意があれば先に出す。"""
    missions, notes = tr.missions_in_name(script_name)
    for n in notes:
        print(f"⚠ ファイル名: {n}")
    if missions:
        title += f"（{' → '.join(missions)}）"
    return tr.new_item(title + warning, missions, default_key)


def record_trial(root, run_file, hub_args, start_time, elapsed, exit_code, log_path, run_sec=None):
    """run_*.py を 1 つ走らせたあとの記録（1 プロセス = 1 試行）。"""
    script_base = os.path.basename(run_file)
    print()
    print("─" * 40)
    print("🏁 結果を記録します")
    item = new_item(os.path.splitext(script_base)[0], script_base, "e" if exit_code != 0 else "o")
    if not tr.ask_trials([item]):
        print("📊 記録しませんでした")
        return
    result, mission_results = tr.item_results(item)
    if result is None:
        print("📊 記録しませんでした")
        return
    write_trial(
        root,
        run_file,
        hub_args,
        start_time,
        elapsed,
        exit_code,
        log_path,
        result,
        mission_results,
        item["note"],
        run_sec=run_sec,
    )
    refresh_dashboard(root)


def record_selector_trials(root, hub_args, watcher, exit_code, log_path):
    """selector.py の通し練習: 走ったプログラムごとに、ミッションの順に成否を聞く。

    全部聞きおえて確認で Enter を押すまで何も書かない（b でひとつ前のプログラムにも戻れる）。
    """
    modules = selector_programs(root)
    print()
    print("─" * 40)
    print(f"🏁 通し練習の結果を記録します（{len(watcher.runs)} 回走りました）")
    plans = []
    for i, run in enumerate(watcher.runs, 1):
        idx = run["index"]
        module, shown = modules[idx] if idx < len(modules) else (f"program{idx}", str(idx))
        run_file = os.path.join(root, module + ".py")
        if not os.path.exists(run_file):
            run_file = os.path.join(root, "selector.py")
        title = f"[{i}/{len(watcher.runs)}] 画面の番号 {shown}: {module}"
        warning = "  ⚠ エラーあり" if run["error"] else ""
        item = new_item(module, title, "x" if run["error"] else "o", warning)
        plans.append((run, run_file, shown, item))
    if not tr.ask_trials([p[3] for p in plans]):
        print("📊 記録しませんでした")
        return
    wrote = 0
    for run, run_file, shown, item in plans:
        result, mission_results = tr.item_results(item)
        if result is None:
            continue
        end = run["end"] or datetime.now()
        seconds = (end - run["start"]).total_seconds()
        write_trial(
            root,
            run_file,
            hub_args,
            run["start"],
            seconds,
            exit_code,
            log_path,
            result,
            mission_results,
            item["note"],
            via=f"selector P{shown}",
            run_sec=seconds
            if run["end"]
            else None,  # セレクターは実行中 → 実行完了がそのまま本番の時間
        )
        wrote += 1
    if wrote:
        refresh_dashboard(root)
    else:
        print("📊 記録しませんでした")


def timing_lines(timer, watcher, is_selector):
    """ログの最後と画面に出す「どこに何秒かかったか」。"""
    lines = []
    setup = timer.setup_sec()
    lines.append(
        f"接続〜初期化完了: {setup:.1f} 秒（ハブを探す・つなぐ・送る・ジャイロの待ち。本番は試合の前に 1 回だけ）"
        if setup is not None
        else f"接続〜初期化完了: 測れず（「{INIT_DONE}」の行が無い）"
    )
    if is_selector:
        for i, run in enumerate(watcher.runs, 1):
            if run["end"]:
                sec = (run["end"] - run["start"]).total_seconds()
                lines.append(
                    f"走行 {i}（プログラム {run['index']}）: {sec:.1f} 秒（本番でもかかる時間）"
                )
            else:
                lines.append(f"走行 {i}（プログラム {run['index']}）: 測れず（実行完了の行が無い）")
    else:
        sec = timer.run_sec()
        lines.append(
            f"走行: {sec:.1f} 秒（初期化完了 → 走行完了。本番でもかかる時間）"
            if sec is not None
            else f"走行: 測れず（「{RUN_DONE}」の行が無い。途中で止まった？）"
        )
    return lines


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
    # -u と PYTHONUNBUFFERED: パイプだと pybricksdev の出力がまとめて遅れて届き、時刻で測れない（2026-10-03。compare.py と同じ）
    cmd = [sys.executable, "-u", "-m", "pybricksdev", "run", "ble", hub_file] + hub_args
    env = dict(os.environ, PYTHONUNBUFFERED="1")

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
            env=env,
        )

        watcher = SelectorWatcher()
        timer = RunTimer()
        try:
            for line in process.stdout:
                print(line, end="")
                f.write(line)
                watcher.feed(line)  # 読むだけ。ハブとの通信には触らない
                timer.feed(line)
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
        for text in timing_lines(timer, watcher, os.path.basename(run_file) == "selector.py"):
            f.write(text + "\n")

    print()
    print(f"📝 ログ保存完了: {log_path}")
    for text in timing_lines(timer, watcher, os.path.basename(run_file) == "selector.py"):
        print("⏱ " + text)

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
                    timer.run_sec(),
                )
        except Exception as e:  # 記録の失敗で終了コードを変えない
            print(f"⚠ 試行記録に失敗しました（走行結果には影響しません）: {e}")

    sys.exit(process.returncode)


if __name__ == "__main__":
    main()
