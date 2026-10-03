"""
【ミッションごとの成否】（2026-10-03）
trials.csv の 1 行（＝ 1 本の走行）にある「ミッションごとの成否」を、読む・書く・ターミナルで聞くための道具。
run_with_log.py・scripts/trial_dashboard.py・scripts/trial_report.py・scripts/trial_fix.py が共通で使う。
PC 側だけで動く。ハブには関係ない。仕様は docs/trial_log_spec.md の §9。

【ミッションと順番は run ファイルの名前から決める】
  run_M01M02M03_kanna.py     → M01 → M02 → M03（この順に走り、この順に成否を聞く）
  run_coach_M12M11M06M07.py  → M12 → M11 → M06 → M07
  run_M01_kanna.py           → M01 だけ（聞くのは 1 回）
  run_M01_M02_kanna.py       → M01 → M02（「_」で区切ってもよい）
  run_M9_soichiro.py         → M09（2 桁にそろえる）

【mission_results 列の書き方】空白で区切った「ミッション=結果」
  M12=fail M11=success M06=success M07=unreached
  success＝成功 / partial＝途中まで / fail＝失敗 /
  unreached＝届かなかった（前のミッションのせいで挑戦できなかった。そのミッションの分母に入れない）
  この列が空の古い行は、result 列の値を mission 列のミッション全部に当てる。

【result 列】ミッションごとの結果から自動で決める
  届いたミッションが全部成功 → success、成功か途中までが 1 つでもある → partial、それ以外 → fail
"""

import csv
import io
import re

MISSION_COUNT = 15  # BIOGLOW のミッションは M01〜M15
MISSION_RE = re.compile(r"[Mm](\d{1,2})")

RESULT_LABEL = {
    "success": "成功",
    "partial": "途中まで",
    "fail": "失敗",
    "unreached": "届かなかった",
    "error": "動かなかった",
}
COUNTED = ("success", "partial", "fail")  # 成功率の分母に入れる結果（unreached は入れない）

# 入力キー → 結果。MISSION_KEYS はミッション 1 つぶん、WHOLE_KEYS はその 1 本ぜんぶ
MISSION_KEYS = {"o": "success", "x": "fail", "d": "partial", "-": "unreached"}
WHOLE_KEYS = {"e": "error", "s": None}
KEY_OF = {v: k for k, v in MISSION_KEYS.items()}
BACK = "b"


# ===== ミッションの並び =====
def missions_in_name(name):
    """run ファイルの名前から (ミッションの並び, 注意の一覧) を返す。

    run_M01M02M03_kanna → (["M01", "M02", "M03"], [])。M01〜M15 にない番号と 2 回目の番号は外して注意に入れる。
    """
    found, notes = [], []
    for m in MISSION_RE.finditer(name):
        n = int(m.group(1))
        mid = f"M{n:02d}"
        if not 1 <= n <= MISSION_COUNT:
            notes.append(f"{m.group(0)} は M01〜M{MISSION_COUNT:02d} にない番号なので数えません")
        elif mid in found:
            notes.append(f"{mid} が 2 回あります（1 回目だけ数えます）")
        else:
            found.append(mid)
    return found, notes


def missions_of(row):
    """trials.csv の 1 行のミッションの並び（mission 列 'M12+M11' から読む。'M9' は 'M09' にそろえる）。"""
    out = []
    for part in (row.get("mission") or "").split("+"):
        m = MISSION_RE.fullmatch(part.strip())
        if m:
            mid = f"M{int(m.group(1)):02d}"
            if mid not in out:
                out.append(mid)
    return out


# ===== mission_results 列 =====
def parse_results(text):
    """'M12=fail M11=success' → {'M12': 'fail', 'M11': 'success'}（書いてある順のまま）"""
    out = {}
    for part in (text or "").split():
        key, _, value = part.partition("=")
        if key and value:
            out[key] = value
    return out


def format_results(pairs):
    """[('M12', 'fail'), ('M11', 'success')] → 'M12=fail M11=success'"""
    return " ".join(f"{m}={r}" for m, r in pairs)


def results_of(row):
    """1 行の [(ミッション, 結果)]。mission_results が空の古い行は、result を全部のミッションに当てる。"""
    given = parse_results(row.get("mission_results"))
    result = row.get("result") or ""
    missions = missions_of(row) or list(given)
    return [(m, given.get(m, result)) for m in missions]


def run_result(results):
    """ミッションごとの結果の並びから、1 本ぶんの result を決める。"""
    tried = [r for r in results if r != "unreached"]
    if tried and all(r == "success" for r in tried):
        return "success"
    if any(r in ("success", "partial") for r in tried):
        return "partial"
    return "fail"


def describe(pairs):
    """[('M12', 'fail'), ...] → 'M12 失敗 / M11 成功'"""
    return " / ".join(f"{m} {RESULT_LABEL.get(r, r)}" for m, r in pairs)


# ===== trials.csv の読み書き =====
def _newline_of(line):
    return "\r\n" if line.endswith("\r\n") else "\n"


def ensure_header(path, columns):
    """見出しに足りない列があれば、見出しの行だけ書きかえて右に足す。いまの見出し（列の並び）を返す。

    行の中身は書きかえない（古い行は右の列が無いだけで、csv.DictReader では空として読める）。
    """
    with open(path, encoding="utf-8", newline="") as f:
        lines = f.readlines()
    if not lines:
        return list(columns)
    header = next(csv.reader([lines[0]]))
    missing = [c for c in columns if c not in header]
    if missing:
        header += missing
        lines[0] = ",".join(header) + _newline_of(lines[0])
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.writelines(lines)
    return header


def read_rows(path):
    """(見出し, 行の一覧, 生の行の一覧) を返す。行 i は生の行 i+1 にあたる（メモに改行は入らないので 1 行 = 1 試行）。"""
    with open(path, encoding="utf-8", newline="") as f:
        raw = f.readlines()
    rows = list(csv.DictReader(io.StringIO("".join(raw))))
    header = next(csv.reader([raw[0]])) if raw else []
    return header, rows, raw


def replace_row(path, index, new_row):
    """行 index（0 から）を new_row で置きかえる。new_row が None ならその行を消す。ほかの行には触らない。"""
    header, rows, raw = read_rows(path)
    old = rows[index]
    line = raw[index + 1]
    check = next(csv.DictReader(io.StringIO(raw[0] + line)))
    if check.get("trial_id") != old.get("trial_id") or check.get("script") != old.get("script"):
        raise RuntimeError("trials.csv の行の並びが読めませんでした（メモに改行が入っている？）")
    if new_row is None:
        del raw[index + 1]
    else:
        buf = io.StringIO()
        w = csv.DictWriter(
            buf, fieldnames=header, extrasaction="ignore", lineterminator=_newline_of(line)
        )
        w.writerow({k: new_row.get(k, "") for k in header})
        raw[index + 1] = buf.getvalue()
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.writelines(raw)


# ===== ターミナルで聞く =====
def new_item(title, missions, default="o", answers=None, note="", whole=None):
    """聞く 1 本ぶん。missions が空なら、ミッションを分けずに 1 回だけ聞く。"""
    return {
        "title": title,
        "missions": list(missions),
        "default": default,
        "answers": dict(answers or {}),
        "whole": whole,  # None / "e"（動かなかった）/ "s"（記録しない）
        "whole_at": None,
        "note": note,
    }


def item_results(item):
    """聞きおえた 1 本の (result, mission_results)。記録しないなら (None, "")。"""
    if item["whole"] == "s":
        return None, ""
    if item["whole"] == "e":
        return "error", ""
    if not item["missions"]:
        return MISSION_KEYS[item["answers"][None]], ""
    pairs = [(m, MISSION_KEYS[item["answers"][m]]) for m in item["missions"]]
    return run_result([r for _, r in pairs]), format_results(pairs)


def _summary_line(n, item, skip_label):
    if item["whole"] == "s":
        what = f"（{skip_label}）"
    elif item["whole"] == "e":
        what = "動かなかった"
    elif not item["missions"]:
        what = RESULT_LABEL[MISSION_KEYS[item["answers"][None]]]
    else:
        what = describe([(m, MISSION_KEYS[item["answers"][m]]) for m in item["missions"]])
    note = f" ／ メモ: {item['note']}" if item["note"] and item["whole"] != "s" else ""
    return f" {n}  {item['title']}  {what}{note}"


def ask_trials(
    items,
    ask=None,
    out=None,
    heading="この内容で記録します",
    skip_label="記録しない",
    ok_label="記録する",
    cancel_label=None,
):
    """items を順に聞き、最後に確認する。確認で Enter を押したら True、やめたら False、Ctrl+C なら None。

    ・どの質問でも b を押すと 1 つ前の質問に戻る（前の本にも戻れる）
    ・確認の画面で番号を押すと、その本だけ入れ直せる
    ・確認で Enter を押すまで、呼び出し元は何も書かない約束
    skip_label は質問で s を押したときの意味（ふつうは「記録しない」、trial_fix.py では「この記録を消す」）。
    """
    ask = ask or input  # 呼んだときの input / print を使う（テストで差しかえられるように）
    out = out or print
    if cancel_label is None:
        cancel_label = "記録しない" if len(items) == 1 else "全部記録しない"
    steps = []  # (種類, 本の番号, ミッション)
    first, note_at = {}, {}
    for i, it in enumerate(items):
        first[i] = len(steps)
        for m in it["missions"] or [None]:
            steps.append(("result", i, m))
        note_at[i] = len(steps)
        steps.append(("note", i, None))
    confirm = len(steps)
    pos, history, back_to_confirm, shown = 0, [], False, None

    def default_key(it, m):
        if it["whole"] and it["whole_at"] == m:
            return it["whole"]
        if m in it["answers"]:
            return it["answers"][m]
        is_first = m == (it["missions"] or [None])[0]
        return it["default"] if is_first or it["default"] != "e" else "o"

    try:
        while True:
            if pos == confirm:
                out("")
                out(f"── {heading} ──")
                for n, it in enumerate(items, 1):
                    out(_summary_line(n, it, skip_label))
                key = ask(
                    f"Enter={ok_label}  番号=その本を入れ直す  b=1 つ前に戻る  s={cancel_label} > "
                ).strip()
                if key == "":
                    return True
                if key.lower() == "s":
                    return False
                if key.lower() == BACK and history:
                    pos = history.pop()
                    continue
                if key.isdigit() and 1 <= int(key) <= len(items):
                    history.append(pos)
                    pos, back_to_confirm, shown = first[int(key) - 1], True, None
                    continue
                out(f"   Enter / 1〜{len(items)} の番号 / b / s のどれかを入力してね")
                continue

            kind, i, m = steps[pos]
            it = items[i]
            if shown != i:
                out("")
                out(it["title"])
                keys = "o=成功  x=失敗  d=途中まで" + ("  -=届かなかった" if it["missions"] else "")
                out(f"   {keys} ／ e=動かなかった  s={skip_label} ／ b=1 つ前に戻る")
                shown = i

            if kind == "result":
                d = default_key(it, m)
                label = f"{m} の結果" if m else "結果"
                key = ask(f"{label} [{d}] > ").strip().lower() or d
                if key == BACK:
                    if history:
                        pos = history.pop()
                    else:
                        out("   これより前には戻れません")
                    continue
                if key in MISSION_KEYS and (m or key != "-"):
                    it["answers"][m] = key
                    if it["whole_at"] == m:
                        it["whole"], it["whole_at"] = None, None
                    nxt = pos + 1
                elif key in WHOLE_KEYS:
                    it["whole"], it["whole_at"] = key, m
                    nxt = note_at[i] if key == "e" else note_at[i] + 1
                else:
                    keys = "o / x / d / - / e / s / b" if m else "o / x / d / e / s / b"
                    out(f"   {keys} のどれかを入力してね")
                    continue
            else:
                if it["note"]:
                    prompt = f"メモ（Enter=そのまま「{it['note']}」・-=消す・b=戻る）> "
                else:
                    prompt = "メモ（なければ Enter・b=戻る）> "
                text = ask(prompt).strip()
                if text.lower() == BACK:
                    if history:
                        pos = history.pop()
                    continue
                if text == "-":
                    it["note"] = ""
                elif text:
                    it["note"] = text
                nxt = pos + 1

            history.append(pos)
            if back_to_confirm and (nxt >= confirm or steps[nxt][1] != i):
                nxt, back_to_confirm = confirm, False
            pos = nxt
    except (EOFError, KeyboardInterrupt):
        out("")
        return None
