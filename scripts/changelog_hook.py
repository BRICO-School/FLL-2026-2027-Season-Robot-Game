#!/usr/bin/env python3
"""run_*.py の変更を自動で記録する pre-commit 補助スクリプト。

staged な run_*.py ごとに、agy(Antigravity CLI)の -p(ヘッドレス)で変更概要を1行生成し、
次の3か所を更新して git add する:
  1. run_*.py 先頭 docstring 内の【更新履歴】に1行追記
  2. docs/logs/<名>/HISTORY.md の表に1行追記
  3. docs/logs/<名>/YYYYMMDD_作業ログ.md に「要約 + 生diff」を追記

agy が見つからない/失敗/タイムアウト時は機械文へフォールバックし、diff は必ず残す。
WSL(python3) と Windows(py) の両方で動くよう、UTF-8/CRLF を安全に扱う。
"""

import os
import re
import shutil
import subprocess
import sys
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def repo_root():
    r = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    return r.stdout.strip()


ROOT = repo_root()

# ファイル名の断片 → 担当者名（.cursor/rules/code-change-log.mdc の推測ルール準拠）
AUTHORS = [
    ("keiichiro", "Keiichiro"),
    ("naotaro", "Naotaro"),
    ("ayumu", "Ayumu"),
    ("kidachi", "Kidachi"),
    ("kannna", "Kanna"),
    ("kanna", "Kanna"),
    ("yuta", "Yuta"),
]


def guess_author(stem):
    low = stem.lower()
    for key, name in AUTHORS:
        if key in low:
            return name
    return ""


def build_agy_call(prompt):
    """agy 実行コマンドを (cmd_list, stdin_text) で返す。呼べない場合は None。

    Windows の agy.exe はパイプ出力時に応答を出さない(TTY必須)ため、Windows からは
    WSL 側の agy へブリッジする。プロンプトは argv 長/改行の問題を避けて stdin で渡す。
    """
    if os.name == "nt":
        if shutil.which("wsl") or shutil.which("wsl.exe"):
            return (["wsl.exe", "-e", "bash", "-lc", 'agy -p "$(cat)"'], prompt)
        return None
    agy = shutil.which("agy") or os.path.expanduser("~/.local/bin/agy")
    if agy and os.path.exists(agy):
        return ([agy, "-p", prompt], None)
    return None


def agy_reachable():
    return build_agy_call("ping") is not None


def staged_diff(rel):
    r = subprocess.run(
        ["git", "diff", "--cached", "--", rel],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    return r.stdout or ""


def mechanical_summary(diff):
    add = sum(1 for ln in diff.splitlines() if ln.startswith("+") and not ln.startswith("+++"))
    rem = sum(1 for ln in diff.splitlines() if ln.startswith("-") and not ln.startswith("---"))
    return f"コードを変更（+{add}/-{rem} 行）"


def agy_summary(diff):
    prompt = (
        "次のgit diffはFLLロボットのPythonコード(pybricks)の変更です。"
        "変更内容を日本語で簡潔に1文(全角40文字以内)に要約してください。"
        "前置き・引用符・コードブロック・箇条書き・記号は付けず、要約文だけを1行で出力すること。\n\n"
        + diff[:4000]
    )
    call = build_agy_call(prompt)
    if call is None:
        return None
    cmd, stdin = call
    try:
        r = subprocess.run(
            cmd,
            input=stdin,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
        if r.returncode != 0:
            return None
        lines = [ln.strip() for ln in (r.stdout or "").splitlines() if ln.strip()]
        if not lines:
            return None
        s = lines[-1].strip(" \"'`「」")
        return s or None
    except Exception:
        return None


def sanitize(s, limit=60):
    s = s.replace("|", "/").replace("\n", " ").strip()
    if len(s) > limit:
        s = s[:limit].rstrip() + "…"
    return s


def update_docstring(path, date, summary):
    raw = open(path, "rb").read()
    text = raw.decode("utf-8")
    nl = "\r\n" if "\r\n" in text else "\n"
    start = text.find('"""')
    if start == -1:
        return False
    end = text.find('"""', start + 3)
    if end == -1:
        return False
    body = text[start + 3 : end]
    line = f"- {date}: {summary}"
    prefix, suffix = text[:end], text[end:]
    if "【更新履歴】" in body:
        ins = line + nl
        if not prefix.endswith(nl):
            ins = nl + ins
    else:
        block = "【更新履歴】" + nl + line + nl
        if prefix.endswith(nl + nl):
            ins = block
        elif prefix.endswith(nl):
            ins = nl + block
        else:
            ins = nl + nl + block
    open(path, "wb").write((prefix + ins + suffix).encode("utf-8"))
    return True


def update_history(logdir, fname, author, date, summary, worklog_name):
    hist = os.path.join(logdir, "HISTORY.md")
    if not os.path.exists(hist):
        content = (
            f"# 修正履歴: {fname}\n\n"
            f"**担当**: {author}  \n"
            f"**ファイル**: `{fname}`\n\n"
            "---\n\n"
            "| # | 日付 | 変更概要 | 詳細ログ |\n"
            "|---|---|---|---|\n"
        )
        n = 1
    else:
        content = open(hist, encoding="utf-8").read()
        n = sum(1 for ln in content.splitlines() if re.match(r"\|\s*\d+\s*\|", ln)) + 1
        if not content.endswith("\n"):
            content += "\n"
    row = f"| {n} | {date} | {summary} | [作業ログ]({worklog_name}) |\n"
    open(hist, "w", encoding="utf-8").write(content + row)


def update_worklog(logdir, worklog_name, fname, author, date, time_s, summary, diff):
    path = os.path.join(logdir, worklog_name)
    fence = "~~~" if "```" in diff else "```"
    block = (
        f"## {time_s} — {summary}\n\n"
        f"### 変更概要\n\n{summary}\n\n"
        f"### 差分\n\n{fence}diff\n{diff.rstrip()}\n{fence}\n"
    )
    if not os.path.exists(path):
        header = (
            f"# 作業ログ: {fname}\n\n"
            f"**日付**: {date}  \n"
            f"**担当**: {author}  \n"
            f"**ファイル**: `{fname}`\n\n"
            "---\n\n"
        )
        open(path, "w", encoding="utf-8").write(header + block)
    else:
        content = open(path, encoding="utf-8").read()
        if not content.endswith("\n"):
            content += "\n"
        open(path, "w", encoding="utf-8").write(content + "\n---\n\n" + block)


def main(argv):
    files = argv[1:]
    if not files:
        return 0
    if not agy_reachable():
        print("[changelog-hook] agy 未検出 → 機械文で記録します。", file=sys.stderr)
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time_s = now.strftime("%H:%M")
    ymd = now.strftime("%Y%m%d")
    to_add = []
    for rel in files:
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            continue
        fname = os.path.basename(rel)
        stem = os.path.splitext(fname)[0]
        author = guess_author(stem)
        diff = staged_diff(rel)
        if not diff.strip():
            continue
        summary = sanitize(agy_summary(diff) or mechanical_summary(diff))
        worklog_name = f"{ymd}_作業ログ.md"
        logdir = os.path.join(ROOT, "docs", "logs", stem)
        os.makedirs(logdir, exist_ok=True)
        update_docstring(path, date, summary)
        update_history(logdir, fname, author, date, summary, worklog_name)
        update_worklog(logdir, worklog_name, fname, author, date, time_s, summary, diff)
        to_add += [
            rel,
            f"docs/logs/{stem}/HISTORY.md",
            f"docs/logs/{stem}/{worklog_name}",
        ]
        print(f"[changelog-hook] 記録: {fname} — {summary}")
    if to_add:
        subprocess.run(["git", "add", "--"] + to_add)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
