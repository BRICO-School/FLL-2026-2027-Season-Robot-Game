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
    },
    {
        "id": "M02",
        "name": "はじける種",
        "en": "Exploding Seeds",
        "max": 30,
        "items": [("茎から離れた種 1 つにつき（3 つまで）", 10)],
    },
    {
        "id": "M03",
        "name": "岩をめくる",
        "en": "Flip the Rock",
        "max": 30,
        "items": [("調査の旗がたおれている", 20), ("ボーナス: 岩が元の位置に戻っている", 10)],
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
    },
    {
        "id": "M05",
        "name": "のびる根",
        "en": "Reaching Roots",
        "max": 20,
        "items": [("根が途中までのびている", 10), ("または 根が完全にのびている", 20)],
    },
    {
        "id": "M06",
        "name": "ハキリアリ",
        "en": "Leafcutter Frenzy",
        "max": 40,
        "items": [("アリが巣にさわっていて、巣の中にある葉のかけら 1 つにつき（4 つまで）", 10)],
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
    },
    {
        "id": "M08",
        "name": "からまったツル",
        "en": "Tangled",
        "max": 30,
        "items": [("ツルがマットにさわっている", 30)],
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
    },
    {
        "id": "M10",
        "name": "こわれやすいすみか",
        "en": "Fragile Microhabitats",
        "max": 20,
        "items": [("クモのすみかが元の位置のまま", 10), ("カタツムリのすみかが元の位置のまま", 10)],
    },
    {
        "id": "M11",
        "name": "過去へのまど",
        "en": "Window to the Past",
        "max": 20,
        "items": [("根のカバーが下がって、マットにさわっている", 20)],
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
    },
    {
        "id": "M13",
        "name": "キーストーン種",
        "en": "Keystone Species",
        "max": 30,
        "items": [("自分たちのキーストーン種が台の上にあり、若い木が立っている", 30)],
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
    },
]

# ミッション以外の点
EQUIPMENT_INSPECTION = 20  # 試合前の点検: ロボットと装備が 1 つの発進エリアと高さ 305mm に収まる
PRECISION_TOKENS = {0: 0, 1: 10, 2: 15, 3: 25, 4: 35, 5: 50, 6: 50}  # 残ったトークンの数 → 点
MATCH_SECONDS = 150

MISSION_MAX_TOTAL = sum(m["max"] for m in MISSIONS)  # 460
GRAND_TOTAL = MISSION_MAX_TOTAL + EQUIPMENT_INSPECTION + PRECISION_TOKENS[6]  # 530
assert GRAND_TOTAL == 530, GRAND_TOTAL
