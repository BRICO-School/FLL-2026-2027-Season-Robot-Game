"""
【BIOGLOW（2026-27）ロボットゲームの点数表】
出典: Robot Game Rulebook（fll-challenge-bioglow-rgr.pdf・V1）と公式の採点表
      https://firstinspires.blob.core.windows.net/fll/challenge/2026-27/fll-challenge-bioglow-software-scoresheet.pdf
      （2026-09-19 に読み取り。合計 530 点になることを確認）

ルールの更新（Challenge Updates）で点数や条件が変わったら、ここを直す。
  ・UPDATE 01（2026-09-02）: M04 は葉の位置が試合前にランダムになり、虫が「葉の生息エリア」の外に出たら 0 点。満点は変わらない。
  ・M07 のボーナス（相手チームの根とつながる 10 点 ×2）は、相手がいる試合でだけ取れる。

name は分かりやすさのための仮の日本語名（公式の和名ではない）。en が公式の英語名。
max = そのミッションの満点。items = 採点表の 1 行ずつ（条件, 点）。

【parts＝ロボットの記録で項目ごとに聞く単位】（2026-10-05・docs/trial_log_spec.md の §11）
  label はルールブック日本語版の言葉。kind は次の 3 つ:
    yesno  取れた／取れない（points 点）
    count  個数 0〜most（1 つ points 点）。cap があると、その項目の値までしか入らない（M14 のマット ≤ ステーション）
    level  段階 0〜len(points)-1（段階 i が points[i] 点。levels は段階の名前）
  needs はボーナスの「かつ」: 書いた項目のどれかが取れていないと 0 点で、聞かない。
  uncounted は記録しない点（M07 の相手チームとのボーナス）。parts の満点＋uncounted＝max になる（下の assert）。
"""

MISSIONS = [
    {
        "id": "M01",
        "name": "ドローン調査",
        "en": "Drone Survey",
        "max": 30,
        "items": [
            ("ドローンがマットから離れている", 20),
            ("ボーナス: LiDAR マップが完全に裏返り、印が調査エリアに入っている", 10),
        ],
        "parts": [
            {"id": "drone", "label": "ドローン", "kind": "yesno", "points": 20},
            {
                "id": "lidar",
                "label": "ボーナス: LiDAR マップ",
                "kind": "yesno",
                "points": 10,
                "needs": ("drone",),
            },
        ],
    },
    {
        "id": "M02",
        "name": "はじける種",
        "en": "Exploding Seeds",
        "max": 30,
        "items": [("茎から離れた種 1 つにつき（3 つまで）", 10)],
        "parts": [
            {"id": "seeds", "label": "はなれた種子", "kind": "count", "points": 10, "most": 3},
        ],
    },
    {
        "id": "M03",
        "name": "岩をめくる",
        "en": "Flip the Rock",
        "max": 30,
        "items": [("調査の旗がたおれている", 20), ("ボーナス: 岩が元の位置に戻っている", 10)],
        "parts": [
            {"id": "flag", "label": "調査フラグ", "kind": "yesno", "points": 20},
            {
                "id": "rock",
                "label": "ボーナス: 岩が元のまま",
                "kind": "yesno",
                "points": 10,
                "needs": ("flag",),
            },
        ],
    },
    {
        "id": "M04",
        "name": "ラッキーリーフ",
        "en": "Lucky Leaves",
        "max": 30,
        "items": [
            ("葉 1 枚が巣から完全に離れている", 10),
            ("ボーナス: 2 枚目も離れていて、虫が元の位置のまま", 20),
        ],
        "parts": [
            {
                "id": "leaves",
                "label": "葉っぱ",
                "kind": "level",
                "points": (0, 10, 30),
                "levels": ("0 点", "1 まい", "2 まい・キリギリスそのまま"),
            },
        ],
    },
    {
        "id": "M05",
        "name": "のびる根",
        "en": "Reaching Roots",
        "max": 20,
        "items": [("根が途中までのびている", 10), ("または 根が完全にのびている", 20)],
        "parts": [
            {
                "id": "root",
                "label": "根",
                "kind": "level",
                "points": (0, 10, 20),
                "levels": ("のびていない", "少しのびた", "ぜんぶのびた"),
            },
        ],
    },
    {
        "id": "M06",
        "name": "ハキリアリ",
        "en": "Leafcutter Frenzy",
        "max": 40,
        "items": [("アリが巣にさわっていて、巣の中にある葉のかけら 1 つにつき（4 つまで）", 10)],
        "parts": [
            {"id": "leaves", "label": "巣の中の葉っぱ", "kind": "count", "points": 10, "most": 4},
        ],
    },
    {
        "id": "M07",
        "name": "巨大キノコ",
        "en": "Humongous Fungus",
        "max": 40,
        "items": [
            ("菌糸が完全にのびている", 20),
            ("ボーナス: 相手チームの根とつながる 1 つにつき（2 つまで）", 10),
        ],
        "parts": [
            {"id": "mycelium", "label": "菌糸体", "kind": "yesno", "points": 20},
        ],
        "uncounted": [("相手チームとのボーナス（相手がいる試合だけ）", 20)],
    },
    {
        "id": "M08",
        "name": "からまったツル",
        "en": "Tangled",
        "max": 30,
        "items": [("ツルがマットにさわっている", 30)],
        "parts": [
            {"id": "vine", "label": "つる", "kind": "yesno", "points": 30},
        ],
    },
    {
        "id": "M09",
        "name": "調査プラットフォーム",
        "en": "Research Platform",
        "max": 30,
        "items": [
            ("プラットフォームが上がっている", 10),
            ("カメラトラップが開いている", 10),
            ("種が木から離れている", 10),
        ],
        "parts": [
            {"id": "platform", "label": "研究プラットフォーム", "kind": "yesno", "points": 10},
            {"id": "camera", "label": "カメラトラップ", "kind": "yesno", "points": 10},
            {"id": "seed", "label": "種子", "kind": "yesno", "points": 10},
        ],
    },
    {
        "id": "M10",
        "name": "こわれやすいすみか",
        "en": "Fragile Microhabitats",
        "max": 20,
        "items": [("クモのすみかが元の位置のまま", 10), ("カタツムリのすみかが元の位置のまま", 10)],
        "parts": [
            {"id": "spider", "label": "クモの生息地", "kind": "yesno", "points": 10},
            {"id": "snail", "label": "カタツムリの生息地", "kind": "yesno", "points": 10},
        ],
    },
    {
        "id": "M11",
        "name": "過去へのまど",
        "en": "Window to the Past",
        "max": 20,
        "items": [("根のカバーが下がって、マットにさわっている", 20)],
        "parts": [
            {"id": "cover", "label": "根のカバー", "kind": "yesno", "points": 20},
        ],
    },
    {
        "id": "M12",
        "name": "森の長老",
        "en": "Forest Elder",
        "max": 30,
        "items": [
            ("つえが完全に上がって、木にさわっている", 20),
            ("支えのひもが柱にかかっている", 10),
        ],
        "parts": [
            {"id": "staff", "label": "支柱", "kind": "yesno", "points": 20},
            {"id": "tie", "label": "サポートタイ", "kind": "yesno", "points": 10},
        ],
    },
    {
        "id": "M13",
        "name": "キーストーン種",
        "en": "Keystone Species",
        "max": 30,
        "items": [("自分たちのキーストーン種が台の上にあり、若い木が立っている", 30)],
        "parts": [
            {"id": "keystone", "label": "キーストーン種", "kind": "yesno", "points": 30},
        ],
    },
    {
        "id": "M14",
        "name": "再生の種",
        "en": "Seeds of Renewal",
        "max": 40,
        "items": [
            ("植えかえステーションの中にある種 1 つにつき（4 つまで）", 5),
            ("ボーナス: その種がマットにさわっている 1 つにつき", 5),
        ],
        "parts": [
            {
                "id": "station",
                "label": "ステーションに入った種子",
                "kind": "count",
                "points": 5,
                "most": 4,
            },
            {
                "id": "mat",
                "label": "そのうちマットにさわっている種子",
                "kind": "count",
                "points": 5,
                "most": 4,
                "cap": "station",
            },
        ],
    },
    {
        "id": "M15",
        "name": "生きものと建物",
        "en": "Biocentric Architecture",
        "max": 40,
        "items": [
            ("巣のひさしが上がっている", 10),
            ("庭の天窓が完全に入っている", 10),
            ("たい肥のハッチが完全に開いて、マットにさわっている", 10),
            (
                "環境ボーナス: 置かれたドック（鉱山・都市・農場）にいちばん必要なものができている",
                10,
            ),
        ],
        "parts": [
            {"id": "eave", "label": "巣のあるひさし", "kind": "yesno", "points": 10},
            {"id": "skylight", "label": "庭の天窓", "kind": "yesno", "points": 10},
            {"id": "hatch", "label": "コンポストハッチ", "kind": "yesno", "points": 10},
            {
                "id": "env",
                "label": "環境ボーナス",
                "kind": "yesno",
                "points": 10,
                "needs": ("eave", "skylight", "hatch"),
            },
        ],
    },
]

# ミッション以外の点（英語版ルールブック p.8・Rule 15 / 2026-10-03 に読み直して確認。Challenge Updates 09-02 で変更なし）
EQUIPMENT_INSPECTION = 20  # 試合前の点検: ロボットと装備が 1 つの発進エリアと高さ 305mm に収まる
PRECISION_TOKENS = {0: 0, 1: 10, 2: 15, 3: 25, 4: 35, 5: 50, 6: 50}  # 残ったトークンの数 → 点
# ダッシュボードで「取れる前提」の参考値として合計に足す点（名前, 点, 取れる条件）
EXTRA_POINTS = [
    ("装備の点検", EQUIPMENT_INSPECTION, "ロボットと装備が 1 つの発進エリアと高さ 305mm に収まる"),
    ("精密トークン", PRECISION_TOKENS[6], "ホームの外で手を出さず、6 つのうち 5 つ以上残す"),
]
# グレイシャス・プロフェッショナリズム（2〜4 点）はロボットゲームの得点ではなく、審査のコアバリューの点に足される（p.17）ので入れない
MATCH_SECONDS = 150

MISSION_MAX_TOTAL = sum(m["max"] for m in MISSIONS)  # 460
EXTRA_TOTAL = sum(p for _, p, _ in EXTRA_POINTS)  # 70
GRAND_TOTAL = MISSION_MAX_TOTAL + EXTRA_TOTAL  # 530
assert GRAND_TOTAL == 530, GRAND_TOTAL


def part_full(part):
    """その項目の満点。"""
    if part["kind"] == "yesno":
        return part["points"]
    if part["kind"] == "count":
        return part["points"] * part["most"]
    return part["points"][-1]


for _m in MISSIONS:
    _full = sum(part_full(p) for p in _m["parts"]) + sum(pt for _, pt in _m.get("uncounted", []))
    assert _full == _m["max"], (_m["id"], _full, _m["max"])
RECORDABLE_TOTAL = sum(
    part_full(p) for m in MISSIONS for p in m["parts"]
)  # 440（M07 の相手ボーナス 20 を引く）
