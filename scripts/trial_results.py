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

【項目ごとの記録】（2026-10-05・仕様は docs/trial_log_spec.md の §11）
  点の取れる項目がいくつもあるミッション（M12 の支柱とサポートタイなど。定義は bioglow_missions.py の parts）は、
  ミッションの結果は聞かずに、毎回すべての項目を聞く。答えは part_results 列に書く:
    M12.staff=1 M12.tie=0 M02.seeds=2 M04.leaves=1
  値は 1/0（取れた・取れない）・個数・段階で、点数は書かない。mission_results は項目から決める
  （満点 → success、1 点でも → partial、0 点 → fail）。part_results が空の古い行は、success＝全部取れた・
  fail＝全部 0・それ以外は「項目は分からない」（点は 0 として数える）。
"""

import csv
import io
import re

import bioglow_missions as bm  # 項目の定義（parts）

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
PARTS = {m["id"]: m["parts"] for m in bm.MISSIONS}

# 数える記録の始まり（trial_id と同じ形）。これより前の記録は項目ごとの記録が無いので、ダッシュボードなどで数えない
# （オーナー 2026-10-05「過去のログは捨てていい」・docs/trial_log_spec.md §11.7）。
# trials.csv の行は消さない（追記だけの決まり。union マージなので、消すとほかの PC から戻ってくる）
COUNT_FROM = "20261005_163000"


def is_counted(row):
    """数える記録か（COUNT_FROM 以後）。"""
    return (row.get("trial_id") or "") >= COUNT_FROM


def count_from_text():
    """'2026-10-05 16:30'"""
    d, t = COUNT_FROM.split("_")
    return f"{d[:4]}-{d[4:6]}-{d[6:]} {t[:2]}:{t[2:4]}"


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


# ===== 項目（2026-10-05・§11） =====
def parts_of(mid):
    """項目ごとに聞くミッションの項目。取れた／取れないの 1 項目だけのミッションは []（いままでどおり o / x / d で聞く）。"""
    parts = PARTS.get(mid, [])
    if len(parts) == 1 and parts[0]["kind"] == "yesno":
        return []
    return parts


def full_points(mid):
    """記録できる満点（M07 は相手チームとのボーナスを数えないので 20）。"""
    return sum(bm.part_full(p) for p in PARTS.get(mid, []))


def part_top(part, values):
    """その項目に入れられるいちばん上の値。count に cap があると、その項目の値まで（M14 のマット ≤ ステーション）。"""
    if part["kind"] == "yesno":
        return 1
    if part["kind"] == "level":
        return len(part["points"]) - 1
    top = part["most"]
    if part.get("cap"):
        top = min(top, values.get(part["cap"], 0))
    return top


def part_open(part, values):
    """その項目を聞くか。前提（needs＝ボーナスの「かつ」）が外れているか、入れられる値が無ければ聞かずに 0。"""
    needs = part.get("needs")
    if needs and not any(values.get(n, 0) for n in needs):
        return False
    return part_top(part, values) > 0


def settle(mid, values):
    """前提と上限をあてはめた値 {項目: 値}（点数表の項目の順に決める。前提が外れた項目は 0、上限をこえた分は切る）。"""
    out = {}
    for p in PARTS.get(mid, []):
        v = int(values.get(p["id"], 0)) if part_open(p, out) else 0
        out[p["id"]] = max(0, min(v, part_top(p, out)))
    return out


def all_values(mid, got):
    """全部取れた（got=True）か、全部 0（got=False）の値。"""
    out = {}
    for p in PARTS.get(mid, []):
        out[p["id"]] = part_top(p, out) if got and part_open(p, out) else 0
    return out


def part_points(part, value):
    if part["kind"] == "yesno":
        return part["points"] if value else 0
    if part["kind"] == "count":
        return part["points"] * value
    return part["points"][value]


def points_of_values(mid, values):
    """項目の値から、そのミッションで取れた点。"""
    values = settle(mid, values)
    return sum(part_points(p, values[p["id"]]) for p in PARTS.get(mid, []))


def result_of_values(mid, values):
    """項目の値から、そのミッションの結果（満点 → success、1 点でも → partial、0 点 → fail）。"""
    points = points_of_values(mid, values)
    if points >= full_points(mid):
        return "success"
    return "partial" if points > 0 else "fail"


def parse_parts(text):
    """'M12.staff=1 M12.tie=0' → {'M12': {'staff': 1, 'tie': 0}}"""
    out = {}
    for part in (text or "").split():
        key, _, value = part.partition("=")
        mid, _, pid = key.partition(".")
        if mid and pid and value.isdigit():
            out.setdefault(mid, {})[pid] = int(value)
    return out


def format_parts(by_mission):
    """{'M12': {'staff': 1, 'tie': 0}} → 'M12.staff=1 M12.tie=0'（項目は点数表の順）"""
    out = []
    for mid, values in by_mission.items():
        values = settle(mid, values)
        out += [f"{mid}.{p['id']}={values[p['id']]}" for p in PARTS.get(mid, [])]
    return " ".join(out)


def values_in(row, mid, result):
    """その行のそのミッションの項目の値。part_results にあればそれ、無ければ 成功＝全部取れた・失敗＝全部 0。

    項目のあるミッションの「途中まで」で part_results が無い古い行は None（項目は分からない）。
    """
    given = parse_parts(row.get("part_results")).get(mid)
    if given is not None:
        return settle(mid, given)
    if result == "success":
        return all_values(mid, True)
    if result != "partial" or not parts_of(mid):
        return all_values(mid, False)
    return None


def points_in(row, mid, result):
    """その行のそのミッションで取れた点。項目の分からない古い「途中まで」は 0 点（それまでと同じ数え方）。"""
    values = values_in(row, mid, result)
    return points_of_values(mid, values) if values is not None else 0


def value_text(part, value):
    if part["kind"] == "yesno":
        return "○" if value else "×"
    if part["kind"] == "level":
        return part["levels"][value]
    return str(value)


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


def describe(pairs, parts=None):
    """[('M12', 'partial'), ...] → 'M12 20/30 点（支柱 ○・サポートタイ ×） / M11 成功'。parts は parse_parts() の形。"""
    parts = parts or {}
    out = []
    for m, r in pairs:
        if m in parts and parts_of(m) and r != "unreached":
            values = settle(m, parts[m])
            detail = "・".join(f"{p['label']} {value_text(p, values[p['id']])}" for p in PARTS[m])
            out.append(f"{m} {points_of_values(m, values)}/{full_points(m)} 点（{detail}）")
        else:
            out.append(f"{m} {RESULT_LABEL.get(r, r)}")
    return " / ".join(out)


def describe_row(row):
    """trials.csv の 1 行のミッションごとの結果（項目があれば点と項目も）。"""
    return describe(results_of(row), parse_parts(row.get("part_results")))


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
def new_item(title, missions, default="o", answers=None, note="", whole=None, parts=None):
    """聞く 1 本ぶん。missions が空なら、ミッションを分けずに 1 回だけ聞く。

    answers は {ミッション: キー}（項目のないミッションの o / x / d / -。項目のあるミッションは「-」だけ入る）、
    parts は {ミッション: {項目: キー}}（o / x / 数字）。
    """
    return {
        "title": title,
        "missions": list(missions),
        "default": default,
        "answers": dict(answers or {}),
        "parts": {m: dict(v) for m, v in (parts or {}).items()},
        "whole": whole,  # None / "e"（動かなかった）/ "s"（記録しない）
        "whole_at": None,  # e / s を押した質問（step_key()）
        "note": note,
    }


def step_key(mission, part=None):
    """質問 1 つの名前（'M12' か 'M12.staff'）。"""
    return mission if part is None else f"{mission}.{part['id']}"


def first_step_key(missions):
    """その本の最初の質問の名前（trial_fix.py が「動かなかった」を最初の質問に出すのに使う）。"""
    first = (missions or [None])[0]
    parts = parts_of(first) if first else []
    return step_key(first, parts[0] if parts else None)


def key_value(key):
    """項目の答えのキー → 値（x → 0、o → 1、数字 → その数）。"""
    if key == "x":
        return 0
    if key == "o":
        return 1
    return int(key)


def item_values(item, mission):
    """聞いた答えから、そのミッションの項目の値（前提と上限をあてはめたもの）。"""
    keys = item["parts"].get(mission, {})
    return settle(mission, {pid: key_value(k) for pid, k in keys.items()})


def mission_result(item, mission):
    if item["answers"].get(mission) == "-":
        return "unreached"
    if parts_of(mission):
        return result_of_values(mission, item_values(item, mission))
    return MISSION_KEYS[item["answers"][mission]]


def item_results(item):
    """聞きおえた 1 本の (result, mission_results)。記録しないなら (None, "")。"""
    if item["whole"] == "s":
        return None, ""
    if item["whole"] == "e":
        return "error", ""
    if not item["missions"]:
        return MISSION_KEYS[item["answers"][None]], ""
    pairs = [(m, mission_result(item, m)) for m in item["missions"]]
    return run_result([r for _, r in pairs]), format_results(pairs)


def item_parts(item):
    """聞きおえた 1 本の part_results（項目のあるミッションで、届いたものだけ）。"""
    if item["whole"] in ("s", "e"):
        return ""
    return format_parts(
        {
            m: item_values(item, m)
            for m in item["missions"]
            if parts_of(m) and item["answers"].get(m) != "-"
        }
    )


def _summary_line(n, item, skip_label):
    if item["whole"] == "s":
        what = f"（{skip_label}）"
    elif item["whole"] == "e":
        what = "動かなかった"
    elif not item["missions"]:
        what = RESULT_LABEL[MISSION_KEYS[item["answers"][None]]]
    else:
        pairs = [(m, mission_result(item, m)) for m in item["missions"]]
        what = describe(pairs, {m: item_values(item, m) for m in item["missions"] if parts_of(m)})
    note = f" ／ メモ: {item['note']}" if item["note"] and item["whole"] != "s" else ""
    return f" {n}  {item['title']}  {what}{note}"


def part_prompt(mission, part, top, default):
    """項目 1 つの質問（'M12 支柱は とれた？（20 点）[o] > '）。子どもも答えるので、ひらがな多めの短い言葉で。"""
    if part["kind"] == "yesno":
        how = f"は とれた？（{part['points']} 点）"
    elif part["kind"] == "count":
        how = f"は いくつ？ 0〜{top}（1 つ {part['points']} 点）"
    else:
        steps = [
            f"{'x' if i == 0 else i}={name}" + (f" {pts} 点" if i else "")
            for i, (name, pts) in enumerate(zip(part["levels"], part["points"], strict=True))
        ]
        how = "（" + "・".join(steps) + "）"
    return f"{mission} {part['label']}{how}[{default}] > "


def part_key(part, key, top):
    """項目の答えをそろえる（yesno は o / x、個数・段階は x か数字）。使えないキーなら None。"""
    if part["kind"] == "yesno":
        return {"o": "o", "1": "o", "x": "x", "0": "x"}.get(key)
    if key in ("x", "0"):
        return "x"
    if key == "o":
        return str(top) if top else "x"
    if key.isdigit() and 1 <= int(key) <= top:
        return key
    return None


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
    ・項目のあるミッション（parts_of()）は、ミッションの結果ではなく項目を 1 つずつ聞く。
      前提（ボーナスの「かつ」）が外れた項目と、入れられる値が無い項目は聞かない
    skip_label は質問で s を押したときの意味（ふつうは「記録しない」、trial_fix.py では「この記録を消す」）。
    """
    ask = ask or input  # 呼んだときの input / print を使う（テストで差しかえられるように）
    out = out or print
    if cancel_label is None:
        cancel_label = "記録しない" if len(items) == 1 else "全部記録しない"
    steps = []  # (種類, 本の番号, ミッション, 項目)
    first, note_at = {}, {}
    for i, it in enumerate(items):
        first[i] = len(steps)
        for m in it["missions"] or [None]:
            parts = parts_of(m) if m else []
            for p in parts or [None]:
                steps.append(("part" if p else "result", i, m, p))
        note_at[i] = len(steps)
        steps.append(("note", i, None, None))
    confirm = len(steps)
    pos, history, back_to_confirm, shown = 0, [], False, None

    def is_first_part(m, p):
        return p is parts_of(m)[0]

    def skipped(step):
        kind, i, m, p = step
        if kind != "part" or is_first_part(m, p):
            return False
        it = items[i]
        return it["answers"].get(m) == "-" or not part_open(p, item_values(it, m))

    def advance(at):
        at += 1
        while at < confirm and skipped(steps[at]):
            at += 1
        return at

    def default_key(it, m, p=None):
        key = step_key(m, p)
        if it["whole"] and it["whole_at"] == key:
            return it["whole"]
        if p is None and m in it["answers"]:
            return it["answers"][m]
        if p is not None:
            if is_first_part(m, p) and it["answers"].get(m) == "-":
                return "-"
            given = it["parts"].get(m, {}).get(p["id"])
            if given is not None:
                top = part_top(p, item_values(it, m))
                return given if not given.isdigit() or int(given) <= top else str(top)
        is_first = key == first_step_key(it["missions"])
        d = it["default"] if is_first or it["default"] != "e" else "o"
        if p is None or d != "o":
            return d
        top = part_top(p, item_values(it, m))
        return "o" if p["kind"] == "yesno" else (str(top) if top else "x")

    def clear_whole(it, key):
        if it["whole_at"] == key:
            it["whole"], it["whole_at"] = None, None

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

            kind, i, m, p = steps[pos]
            it = items[i]
            if shown != i:
                out("")
                out(it["title"])
                keys = "o=成功  x=失敗  d=途中まで" + ("  -=届かなかった" if it["missions"] else "")
                out(f"   {keys} ／ e=動かなかった  s={skip_label} ／ b=1 つ前に戻る")
                if any(parts_of(x) for x in it["missions"]):
                    out(
                        "   ぶぶんごとに聞くよ: o=とれた  x=とれなかった  すうじ=いくつ・どこまで"
                        " ／ さいしょの質問で -=とどかなかった"
                    )
                shown = i

            if kind in ("result", "part"):
                d = default_key(it, m, p)
                if p is None:
                    prompt = f"{m} の結果 [{d}] > " if m else f"結果 [{d}] > "
                else:
                    top = part_top(p, item_values(it, m))
                    prompt = part_prompt(m, p, top, d)
                key = ask(prompt).strip().lower() or d
                if key == BACK:
                    if history:
                        pos = history.pop()
                    else:
                        out("   これより前には戻れません")
                    continue
                if p is None and key in MISSION_KEYS and (m or key != "-"):
                    it["answers"][m] = key
                    clear_whole(it, step_key(m))
                    nxt = advance(pos)
                elif p is not None and key == "-" and is_first_part(m, p):
                    it["answers"][m] = "-"
                    clear_whole(it, step_key(m, p))
                    nxt = advance(pos)
                elif p is not None and part_key(p, key, top) is not None:
                    it["parts"].setdefault(m, {})[p["id"]] = part_key(p, key, top)
                    if is_first_part(m, p):
                        it["answers"].pop(m, None)
                    clear_whole(it, step_key(m, p))
                    nxt = advance(pos)
                elif key in WHOLE_KEYS:
                    it["whole"], it["whole_at"] = key, step_key(m, p)
                    nxt = note_at[i] if key == "e" else note_at[i] + 1
                else:
                    if p is None:
                        keys = "o / x / d / - / e / s / b" if m else "o / x / d / e / s / b"
                    else:
                        first_dash = " / -" if is_first_part(m, p) else ""
                        values = "o / x" if p["kind"] == "yesno" else f"x / 1〜{top} / o"
                        keys = f"{values}{first_dash} / e / s / b"
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
                nxt = advance(pos)

            history.append(pos)
            if back_to_confirm and (nxt >= confirm or steps[nxt][1] != i):
                nxt, back_to_confirm = confirm, False
            pos = nxt
    except (EOFError, KeyboardInterrupt):
        out("")
        return None
