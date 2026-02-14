# FLL 2026-2027 シーズン ロボットゲーム

FIRST LEGO League 2026-2027シーズンのロボットゲーム用プログラムです。
Pybricks + LEGO SPIKE Prime Hub を使用しています。

## 🚀 クイックスタート

### 1. 環境セットアップ
```bash
# 仮想環境の作成
python -m venv .venv

# 仮想環境の有効化
# Windows (PowerShell)
.venv\Scripts\activate

# Mac / Linux
source .venv/bin/activate

# 依存パッケージのインストール
python -m pip install -r requirements.txt

# 開発用（lint/format）
python -m pip install -r requirements-dev.txt
```

### ruff（コード整形/チェック）
このリポジトリは `ruff` を使って、コードの整形（format）とチェック（lint）を行います。

```bash
# 開発用ツール（ruff / pre-commit）をインストール
python -m pip install -r requirements-dev.txt

# 整形
ruff format .

# チェック
ruff check .
```

VS Code の `F5` 実行は、起動前に `ruff` を自動実行する設定になっています（`preLaunchTask`）。
もし `ruff: command not found` が出る場合は、上の `requirements-dev.txt` のインストールが抜けています。

### pybricksdev が見つからない場合（`No module named pybricksdev`）
VS Code の実行設定は `-m pybricksdev` を使うので、`.venv` に `pybricksdev` が入っていないと起動できません。

```bash
# まず仮想環境を有効化
source .venv/bin/activate

# requirements を入れ直す
python -m pip install -r requirements.txt

# もし入らない場合（プレリリース扱いで弾かれる場合）は --pre を付ける
python -m pip install --pre -r requirements.txt

# 入ったか確認
python -m pip show pybricksdev
python -m pybricksdev --help
```

### 2. プログラムの実行方法

#### 方法A: プログラムセレクター（競技本番用）
1. VS Code で `selector.py` を開いて実行（F5）
2. ハブの **左右ボタン** でプログラムを選択（番号が表示される）
3. **フォースセンサー**（Port.C）を押して実行

| 表示番号 | プログラム | ミッション |
|:--------:|-----------|-----------|
| 1 | run1_m08_M06_M05_new | M08, M06, M05 |
| 2 | run3_M09_M07_ayumu_modified | M09, M07 |
| 3 | run1_M10_M11 | M10, M11 |
| 4 | run4_M12_ayumu | M12 |
| 5 | run1_M01_M02_kanna | M01, M02 |
| 6 | run1_M13_M03 | M13, M03 |

#### 方法B: 個別ファイルの直接実行（開発用）
1. 実行したい `run*.py` ファイルを開く
2. **F5** を押してデバッグパネルからロボットを選択

### 3. 開発モード / 本番モード
`selector.py` 内の `dev` フラグで切り替え：
```python
dev = True   # 開発モード（センサーログ有効）
dev = False  # 本番モード（センサーログなし、動作軽量）
```

## 📁 プロジェクト構成

```
FLL-2025-2026-Season-Robot-Game/
├── setup.py              # ロボット初期化（共通設定）
├── selector.py           # プログラムセレクター（競技用）
├── run_template.py       # 新規run作成用テンプレート
├── run1_*.py             # 各ミッションのプログラム
├── requirements.txt      # 依存パッケージ
├── .vscode/launch.json   # VS Code デバッグ設定
├── docs/                 # ドキュメント
└── old/                  # 旧バージョン
```

## 🤖 ロボット構成

| ポート | デバイス | 説明 |
|--------|---------|------|
| Port.F | 左タイヤ | 反時計回りが正 |
| Port.B | 右タイヤ | 時計回りが正 |
| Port.E | 左リフト | 時計回りが正 |
| Port.A | 右リフト | 時計回りが正 |
| Port.C | フォースセンサー | プログラム実行ボタン |

## 📝 新しいrunファイルの作成方法

1. `run_template.py` をコピーして新しい名前をつける（例: `run2_M04.py`）
2. `run()` 関数内にロボットの動作を記述
3. `selector.py` の `programs` リストに追加：
```python
import run2_M04  # ファイルをインポート

programs = [
    # ... 既存のプログラム
    {"module": run2_M04, "display_number": 7},  # 追加
]
```

### 使用可能なコマンド

```python
# 移動系（speed, timeout オプション対応）
await robot.straight(400)                  # 400mm直進
await robot.straight(200, speed=500)       # 500mm/sで200mm直進
await robot.straight(500, timeout=3000)    # 3秒以内に500mm直進
await robot.turn(90)                       # 90度右回転
await robot.turn(-45, rate=300)            # 300deg/sで45度左回転
await robot.curve(200, 90)                 # 半径200mmで90度カーブ

# モーター操作
await robot.run_motor(left_lift, 180)      # 左アームを180度回転
await robot.run_motor(right_lift, -360, speed=500)  # 右アームを逆方向に1回転
await left_lift.run_angle(300, 180)        # 左アームを180度回転（従来の方法）
await right_lift.run_angle(500, -360)      # 右アームを逆方向に1回転（従来の方法）

# 待機
await wait(500)                            # 0.5秒待機
```

## ⚙️ デフォルト速度設定

| 動作 | 速度 | 加速度 |
|------|------|--------|
| 直進 | 400 mm/s | 500 mm/s² |
| 回転 | 240 deg/s | 850 deg/s² |
| カーブ | 240 mm/s | 800 mm/s² |

設定は `setup.py` の `DEFAULT_*_SETTINGS` で変更可能です。

## 🔧 複数ロボットの切り替え

VS Code のデバッグドロップダウンから使用するロボットを選択できます：
- 🤖 Robot 1 (Pybricks Hub)
- 🤖 Robot 2 (Pybricks Hub2)
- 🤖 Robot 3 (Pybricks Hub3)

## 📚 技術スタック

- **Pybricks** >= 3.6.1
- **pybricksdev** >= 1.0.0a49
- LEGO SPIKE Prime Hub
