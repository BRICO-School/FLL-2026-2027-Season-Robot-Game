# FLL 2026-2027 ロボットゲーム — メンター向けガイド

> 対象: プロジェクトを技術的にサポートするメンター / コーチ。
> 子ども向けの日常運用ドキュメントは [`README.md`](./README.md) を参照してください。

このドキュメントは、メンターがコードベース全体を短時間で把握し、
子どもたちの試行錯誤を支援できるようにするための詳細ガイドです。

---

## 0. 実行モードの使い分け（最重要）

このプロジェクトには **2 つの実行モード** があり、フェーズによって使い分けます。
メンターはこの区別を子どもに徹底させてください。

| フェーズ | エントリポイント | 目的 | 実行方法 |
|---------|------------------|------|----------|
| **開発・調整フェーズ** | 個別の **`run_*.py`** を直接実行 | 1 つのミッションだけを繰り返しテストし、動作を追い込む | VS Code で対象の `run_*.py` を開き、`🤖 Robot N` 構成で **F5** |
| **通し練習・大会本番** | **`selector.py`** から実行 | 複数ミッションを連続実行し、ハブ単体で運用する | `selector.py` を開いて F5 → ハブの左右ボタンで番号選択 → フォースセンサーで発射 |

**ルール:**

- 開発中は `selector.py` を触らず、各自の `run_*.py` だけを直接 F5 で回す。
  → 誰かが壊しても他人に波及しない。
- 大会直前になってから、完成した `run_*.py` を `selector.py` の `programs` リストに
  登録する。登録後は全プログラムを通しで動作確認すること。
- `selector.py` への登録・並び替えは **メンターまたは担当者 1 名が責任を持って行う**。
  複数人が同時に `selector.py` を編集するとコンフリクトが頻発します。

---

## 1. プロジェクト概要

- **競技**: FIRST LEGO League 2026-2027シーズン ロボットゲーム
- **プラットフォーム**: LEGO SPIKE Prime Hub + [Pybricks](https://pybricks.com/)
- **言語**: Python（Pybricks MicroPython 環境、PC 側は CPython）
- **対象ユーザー**: 中学生チーム（複数名、複数ロボット、複数 PC）
- **開発スタイル**: 各メンバーが自分の名前入り `run_*_<name>.py` を持ち、
  競技本番は `selector.py` に登録されたプログラムをハブのボタンで選んで実行する

### 想定運用環境

このリポジトリは **複数 PC + 複数ハブ** で並行運用されることを前提にしています。

| 項目 | 想定 |
|------|------|
| PC の OS | Windows / macOS の混在（各メンバーが自分の PC を使う） |
| 物理ハブ数 | 最大 5 台（`Pybricks Hub` / `Hub2` / … / `Hub5`） |
| 同期手段 | Git（GitHub）。各メンバーがブランチを切って作業 |
| ファイル転送 | BLE 経由で `pybricksdev run ble` によりハブへ直接送信 |

OS 差分は `.vscode/tasks.json` の `windows:` セクションで吸収済みです
（PATH の区切りや PowerShell 判定）。新しくタスクを追加する場合は
Mac/Linux 側と Windows 側の両方をメンテナンスしてください。

---

## 2. リポジトリ構成

```
FLL-2026-2027-Season-Robot-Game/
├── README.md                   # 子ども向け（日常運用）
├── README_FOR_MENTORS.md       # 本ドキュメント
├── integrated-guide-v1.md      # 総合ガイド（科学的アプローチ）
├── setup.py                    # ★ ロボット初期化＋Robotクラス（全 run 共通基盤）
├── selector.py                 # ★ 競技本番のエントリポイント（multitask）
├── run_template.py             # 新しい run を作るテンプレート
├── run_template copy.py        # テンプレートの派生
├── run_with_log.py             # pybricksdev ラッパー（ログ自動保存）
├── run1_M01_M02_kanna.py       # ミッション別プログラム（担当者名付き）
├── run1_M05_M06_M07_M08_kidachi.py
├── run1_M10_M11.py
├── run1_M13_M03.py
├── run1_m08_M06_M05_new.py
├── run3_M09_M07_ayumu_modified.py
├── run4_M12_ayumu.py
├── run4_M12_kanna.py
├── run4_M12_Yuta.py
├── run_M01_kanna.py
├── run_M01_kidachi.py
├── run_test_ayumu*.py          # 歩むの検証用スクリプト
├── requirements.txt            # pybricks, pybricksdev
├── requirements-dev.txt        # ruff, pre-commit
├── pyproject.toml              # ruff 設定
├── .pre-commit-config.yaml     # ruff check/format フック
├── .vscode/
│   ├── launch.json             # Robot 1-5 / Robot 1-5 + Log の 10 構成
│   └── tasks.json              # ruff: all（pre-launch で自動実行）
├── docs/
│   ├── ayumu_roadmap.md        # 子どもの学習ロードマップ
│   ├── ayumu_guide_progress.md # 進捗管理
│   ├── how_to_reduce_SD.md     # ばらつき低減の技術メモ
│   ├── speed_test_result_tables.md
│   ├── square_test_evaluation.md
│   ├── curve_test_evaluation.md
│   ├── tread_ratio_summary.md
│   └── logs/<script>/<YYYYMMDD_HHMMSS>.log  # 実行ログの自動保存先
└── old/                        # 旧版スクリプトと旧 README（参照のみ、ruff 除外）
```

### 命名規則

- `run<ラン番号>_<ミッション列>_<担当者>.py`
  例: `run1_M01_M02_kanna.py` → 「ラン1、M01+M02、kanna 担当」
- 同じミッションでも **担当者別にファイルを分けている** のが特徴です。
  これは子どもたちが互いのコードを壊さずに試行錯誤するための運用です。
  メンター側も、他人のファイルを勝手に書き換えないよう注意してください。
- `run_test_*.py` は性能評価用の検証スクリプトで、競技には直接使いません。

---

## 3. アーキテクチャ

### 3.1 コア: `setup.py`

すべての run スクリプトが依存する共通基盤。

- **`initialize_robot()`**:
  `(hub, robot, left_wheel, right_wheel, left_lift, right_lift)` を返す。
  子ども向け run からは常にこの 6 要素を受け取る契約。
- **`Robot` クラス**: `DriveBase` を薄くラップし、
  呼び出しごとに `speed` / `acceleration` / `timeout` を任意指定可能にした。
  - `straight()` / `turn()` / `curve()` は一時的に `settings()` を書き換え、
    終了後に `DEFAULT_*_SETTINGS` へ戻す。
  - `timeout` 指定時は `wait=False` で発火し、`StopWatch` で監視して
    超過時に `stop()` する実装。ハブ側に blocking タイムアウトが無いための回避策。
  - `run_motor(motor, speed, angle, timeout=...)` は個別モーター用の同等機能。
- **`NullMotor`**: `Port.E` / `Port.A`（リフト）が物理的に未接続でも落ちないようにする
  ダミー実装。`angle()` / `run_angle(..., wait=True|False)` / `control.done()` などを提供。
  → ハードウェアが揃っていない状態でも子どもたちがコードを書き進められるようにする意図。
  **タイヤ（`Port.B` / `Port.F`）は必須** で、未接続なら素直に例外になります。
- **DriveBase の物理パラメータ**: `wheel_diameter=62mm`, `axle_track=85mm`。
  子どもがロボットを作り直した場合はここを要更新（ロボット本体変更時の落とし穴）。
- **PID ゲイン**: `distance_control` = (1000, 50, 10)、`heading_control` = (2000, 50, 100)。
  チューニング手順は `docs/how_to_reduce_SD.md` 参照。

### 3.2 エントリポイント: `selector.py`

- `dev` フラグ（`selector.py:43`）:
  - `True` → `sensor_logger_task()` と `selector_task()` を `multitask` で並走
  - `False` → セレクターのみ（本番用、通信オーバーヘッドなし）
- `programs` リスト（`selector.py:59`）に登録されたモジュールが
  ハブ LED で選択・実行される。各モジュールは
  `async def run(hub, robot, left_wheel, right_wheel, left_lift, right_lift)`
  シグネチャを満たす必要があります。
- ボタン: LEFT/RIGHT で選択、フォースセンサー（Port.C）で実行。
- `reset_robot()` が前後に走り、`hub.imu.reset_heading(0)` と `robot.reset()` で
  プログラム間の状態漏れを防ぎます。

### 3.3 ログ付き実行: `run_with_log.py`

`pybricksdev run ble <file> --name <hub>` のラッパーで、
stdout を tee しつつ `docs/logs/<script>/<YYYYMMDD_HHMMSS>.log` に保存します。

- `.vscode/launch.json` の「📝 Robot N + Log」構成から直接呼ばれます。
- ログ末尾に終了コード・実行時間が追記されるので、
  回帰調査やばらつき評価がやりやすくなります。
- 作成されたログは **Git 管理対象** になっているため、
  量が増えたら定期的に整理するか、`.gitignore` に追加するか検討してください。

### 3.4 ハードウェア構成（ポート割付）

| Port | デバイス | 正方向 | 必須 |
|------|---------|--------|------|
| F | 左駆動モーター | CCW | ✅ |
| B | 右駆動モーター | CW | ✅ |
| E | 左リフト | CW | ❌（NullMotor でフォールバック） |
| A | 右リフト | CW | ❌（NullMotor でフォールバック） |
| C | ForceSensor（開始ボタン兼用） | — | selector 使用時のみ必須 |

ハブ姿勢: `PrimeHub(top_side=Axis.Z, front_side=Axis.X)`。
ロボット本体の向きを変えるとここも修正が必要です。

---

## 4. 開発環境セットアップ

### 4.1 初回セットアップ（PC ごとに1回）

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
pre-commit install
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
pre-commit install
```

`pybricksdev` がプレリリース扱いでインストールに失敗する場合は
`python -m pip install --pre -r requirements.txt` を試してください。

### 4.2 ハブ側セットアップ

1. Chrome で https://code.pybricks.com にアクセス
2. USB 接続のハブに Pybricks firmware を書き込む
3. ハブ名を `Pybricks Hub` / `Pybricks Hub2` / … / `Pybricks Hub5` のいずれかに設定
4. `launch.json` の既存構成がそのまま使える

ハブ名が 6 台目以上になる場合は `launch.json` に構成を追加してください
（Robot 1-5 のブロックをコピーして `--name "Pybricks Hub6"` にするだけ）。

### 4.3 VS Code からの実行

- **通常実行**: `🤖 Robot N (Pybricks HubN)`（1〜5）
- **ログ付き実行**: `📝 Robot N + Log (Pybricks HubN)`（1〜5）
- すべての構成で `preLaunchTask: "ruff: all"` が走り、
  アクティブファイルが `.py` であることの検証 → `ruff format` → `ruff check --fix`
  の順で自動整形・自動修正が行われます。
- BLE 接続がうまくいかない場合は、ハブの Bluetooth ボタンを押して
  ペアリング状態にしてから F5 を押してください。

### 4.4 新しい端末（PC）を追加する手順

新しいメンバーや新しい PC をプロジェクトに参加させるときの標準手順です。
Windows / macOS どちらも同じ流れで、OS 依存部分のみ分岐します。

#### 前提ソフトウェア

| ソフト | 最低バージョン | 備考 |
|--------|--------------|------|
| Git | 2.30+ | Windows は Git for Windows、Mac は `brew install git` か Xcode Command Line Tools |
| Python | 3.9+ | `pyproject.toml` の `target-version = "py39"` に合わせる |
| VS Code | 最新 | `Python` 拡張機能を入れる |
| Google Chrome | 最新 | Pybricks firmware の書き込みに必要（Web Bluetooth） |

Windows でインストーラから Python を入れる場合は **「Add python.exe to PATH」** に
必ずチェックを入れてください（`.venv` 作成が失敗する原因の最頻値です）。

#### 初期化手順

```bash
# 1. クローン
git clone https://github.com/BRICO-School/FLL-2026-2027-Season-Robot-Game.git
cd FLL-2026-2027-Season-Robot-Game

# 2. 仮想環境作成（Windows）
python -m venv .venv
.venv\Scripts\activate

# 2. 仮想環境作成（macOS / Linux）
python3 -m venv .venv
source .venv/bin/activate

# 3. 依存インストール
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt

# 4. pre-commit フック有効化
pre-commit install

# 5. 動作確認
python -m pybricksdev --help
ruff --version
```

`pybricksdev` は a49 等のプレリリース版指定のため、素で入らない場合は
`python -m pip install --pre -r requirements.txt` を使ってください。

#### VS Code 側の初期設定

1. VS Code でプロジェクトフォルダを開く
2. **Ctrl+Shift+P**（Mac: **Cmd+Shift+P**） → `Python: Select Interpreter`
   → `.venv` を選択
3. 左下のステータスバーに `Python 3.x.x ('.venv')` が表示されることを確認
4. 推奨拡張: `ms-python.python`、`charliermarsh.ruff`

#### Git の識別情報

初回のみ、端末ごとに設定します（グローバル設定が無い場合）:

```bash
git config --global user.name  "メンバー名"
git config --global user.email "メンバーのメールアドレス"
```

メンバーごとにブランチを切って作業する運用を推奨します:

```bash
git switch -c feature/<member>-<topic>
```

#### Bluetooth / ハブ関連

- **Windows**: 標準の Bluetooth スタックで動作します。Bluetooth アダプタが
  USB ドングル式の場合、Bluetooth 4.0 以上（LE 対応）であることを確認してください。
- **macOS**: 初回の BLE 通信時にシステム設定で **Bluetooth の使用許可** が要求されます。
  VS Code に対して許可してください（一度許可すれば記憶されます）。
  社用管理端末の場合は MDM ポリシーで BLE がブロックされていないかも確認。
- **WSL**: WSL から `pybricksdev` の BLE 接続は現状サポート外です。
  WSL を使っている環境でも、pybricksdev 実行は **Windows 側の Python** で行ってください。

#### ハブ名と `launch.json` の整合

既存の `launch.json` は `Pybricks Hub` / `Pybricks Hub2` 〜 `Pybricks Hub5` を想定しています。
新しいハブを追加する詳細手順は **§4.5** を参照してください。

### 4.5 新しいハブを追加する手順

新規 SPIKE Prime ハブをチームに組み込むときの標準手順です。
**ハブごとに1回** 実施します。

#### 前提

- USB-C ケーブル（SPIKE Prime 本体の充電ポート用、データ転送対応のもの）
- Google Chrome または Edge（Web Bluetooth / Web USB 対応ブラウザ）
- 書き込みを行う PC に管理者権限は不要（ブラウザ経由のため）

#### Step 1: Pybricks firmware 書き込み

1. Chrome で https://code.pybricks.com を開く
2. ハブを USB-C で PC に接続し、中央ボタンで電源 ON
3. 左上の歯車 → **Install Pybricks Firmware** → **SPIKE Prime** を選択
4. **Firmware version**: 最新安定版を選択
   （既存ハブと揃えることを推奨。`requirements.txt` の `pybricks>=3.6.1` と整合する版）
5. **Hub name** は後述のハブ命名規則に従って入力（この時点で決める）
6. 「Install」を押し、ハブのボタン操作指示に従って DFU モードに入れる
7. プログレスバー完了まで USB を抜かない

#### Step 2: ハブ命名規則

`.vscode/launch.json` の既存構成と整合させるため、名前は **以下のパターン厳守**:

```
Pybricks Hub      ← 1 台目
Pybricks Hub2     ← 2 台目
Pybricks Hub3     ← 3 台目
Pybricks Hub4     ← 4 台目
Pybricks Hub5     ← 5 台目
Pybricks Hub6     ← 6 台目以降（launch.json 追加が必要）
...
```

**注意点:**

- `Pybricks` と `Hub` の間は **半角スペース 1 個**。全角スペースや複数スペースは NG。
- `Hub` と数字の間には **スペースを入れない**（`Hub 2` ❌ / `Hub2` ✅）。
- 1 台目は `Hub1` ではなく **数字なしの `Pybricks Hub`**。
- 既存ハブと重複しないこと。BLE スキャンで衝突して接続が不安定になります。
- 名前は Pybricks Code からいつでも変更可能（Hub 設定メニュー）。ミスに気づいたら修正を。

#### Step 3: launch.json の更新（6 台目以降のみ）

5 台目までは既存の構成で動作するため追加不要です。
6 台目以降を追加する場合、`.vscode/launch.json` に **通常構成** と **ログ付き構成** の
2 ブロックを追記します。

```jsonc
{
    "name": "🤖 Robot 6 (Pybricks Hub6)",
    "type": "debugpy",
    "request": "launch",
    "preLaunchTask": "ruff: all",
    "module": "pybricksdev",
    "args": ["run", "ble", "${file}", "--name", "Pybricks Hub6"],
    "env": { "PYTHONUTF8": "1" }
},
{
    "name": "📝 Robot 6 + Log (Pybricks Hub6)",
    "type": "debugpy",
    "request": "launch",
    "preLaunchTask": "ruff: all",
    "program": "${workspaceFolder}/run_with_log.py",
    "args": ["${file}", "--name", "Pybricks Hub6"],
    "env": { "PYTHONUTF8": "1" }
}
```

既存の「Robot 5」ブロックをコピーし、**3 箇所**（`name` の絵文字以降、`--name` の値）
を置き換えるのが確実です。`preLaunchTask` と `env.PYTHONUTF8` は必ず残すこと。

編集後は必ず JSON として妥当か VS Code で確認（赤波線が出ないこと）し、
コミットしてチーム全員に配布してください。

#### Step 4: 物理構成のセットアップ

新しいハブに対応するロボット本体を組んだら、以下を必ず確認:

- [ ] **Port F**: 左駆動モーター、`Direction.COUNTERCLOCKWISE` が前進
- [ ] **Port B**: 右駆動モーター、`Direction.CLOCKWISE` が前進
- [ ] **Port E**: 左リフト（未接続でも可、NullMotor でフォールバック）
- [ ] **Port A**: 右リフト（未接続でも可、NullMotor でフォールバック）
- [ ] **Port C**: ForceSensor（`selector.py` を使う場合は必須）
- [ ] ハブ姿勢が `top_side=Axis.Z, front_side=Axis.X` と一致している
- [ ] タイヤ径が 62mm、トレッドが 85mm と一致している
  （異なる場合は `setup.py` の `DriveBase` パラメータ調整が必要 — ロボット固有化を検討）

#### Step 5: 動作確認

1. VS Code で `run_template.py`（または簡単な直進テスト）を開く
2. デバッグ構成から追加したハブの `🤖 Robot N` を選択
3. F5 → ハブの BLE 広告待機（中央ボタン押下で青点滅）→ 自動接続
4. 走行完了メッセージが出力されることを確認
5. 続けて `📝 Robot N + Log` でも実行し、`docs/logs/run_template/` にログが生成されることを確認
6. `selector.py` も通しで動くことを確認（本番投入前に必須）

#### Step 6: 台帳管理（推奨）

ハブが増えると識別が難しくなるので、物理ハブに **シール等で番号を貼付** し、
以下の情報をチーム内で共有しておくと運用が楽になります:

| 項目 | 例 |
|------|-----|
| ハブ番号 | 3 |
| Pybricks 名 | `Pybricks Hub3` |
| firmware バージョン | 3.6.1 |
| 担当メンバー | ayumu |
| 備考 | 直進キャリブレーション済み / タイヤ交換 2026-04-01 |

#### トラブルシュート

| 症状 | 原因 | 対処 |
|------|------|------|
| firmware 書き込みが途中で止まる | USB ケーブルが充電専用 / ハブの電池残量不足 | データ転送対応ケーブルに交換、充電してから再実施 |
| 書き込み後、ハブが認識されない | BLE 名が launch.json と不一致 | Pybricks Code で名前を再設定 |
| 接続するが即切断 | 他 PC が同じハブをつかんでいる | 他 PC の VS Code デバッグを終了、ハブを再起動 |
| 「No matching device found」 | ハブが広告していない / Bluetooth OFF | ハブの中央ボタン押下で広告開始、PC の Bluetooth 確認 |
| 2 台目のハブで F5 が 1 台目につながる | `--name` 指定ミス、または launch.json で別構成を選択していない | デバッグ構成ドロップダウンで正しい Robot N を選択 |

#### 動作確認チェックリスト

新しい端末で以下がすべて通れば、セットアップ完了と判断できます。

- [ ] `.venv` を有効化した状態で `python -m pybricksdev --help` が動く
- [ ] `ruff check .` がエラーなく完了する
- [ ] `pre-commit run --all-files` が完了する
- [ ] VS Code で任意の `run_*.py` を開き、F5 → ハブ選択 → 実行できる
- [ ] `📝 Robot N + Log` 構成で実行し、`docs/logs/<script>/` にログが生成される
- [ ] `git pull` / `git push` が認証を含めて通る

### 4.6 Lint / Format / Pre-commit

- `pyproject.toml` で `target-version = "py39"`, `line-length = 100`。
- `select = ["E", "F", "I", "B", "UP"]`、`ignore = ["E501"]`（長い行は許容）。
- `run*.py` と `run_template.py` は `F401`（未使用 import）と `I001`（import ソート）を除外
  → 子どもが学習用に意図的に残している import を壊さないため。
- `old/` と `.venv` は ruff の検査対象外。
- `.pre-commit-config.yaml` は `ruff check --fix` と `ruff format` をローカルフックで実行。

---

## 5. 新しい run スクリプトを追加する（コーチ手順）

子どもと一緒に作業するときの標準フロー:

1. `run_template.py` を `run<番号>_<ミッション>_<名前>.py` にコピー
2. `async def run(hub, robot, left_wheel, right_wheel, left_lift, right_lift)` 内に動作を記述
3. 単体テストは `if __name__ == "__main__":` ブロックから F5 で実行
4. 本番投入する場合は `selector.py` の先頭で `import` し、
   `programs = [...]` に `{"module": <module>, "display_number": <int>}` を追加
5. `pre-commit` がフォーマット・Lint を自動修正するので、そのままコミット可

`run_template.py` には典型的な `straight` / `turn` / `curve` / `run_angle` の例が
コメントとして書かれています。子どもへの説明は `README.md` の該当セクションが参考になります。

---

## 6. ドキュメント類

| ファイル | 内容 | 想定利用シーン |
|----------|------|---------------|
| `integrated-guide-v1.md` | 科学的アプローチの総合ガイド（114KB） | 学期通しての指導計画 |
| `docs/ayumu_roadmap.md` | 4 フェーズのロードマップ | 次に何をやるかの意思決定 |
| `docs/ayumu_guide_progress.md` | 進捗管理 | 毎週のふりかえり |
| `docs/how_to_reduce_SD.md` | 走行ばらつきの低減手順 | トラブル時の PID / 機体調整 |
| `docs/speed_test_result_tables.md` | 速度テストの実測値 | パラメータ選定 |
| `docs/square_test_evaluation.md` | 正方形走行の評価 | キャリブレーション |
| `docs/curve_test_evaluation.md` | カーブ走行の評価 | カーブパラメータ選定 |
| `docs/tread_ratio_summary.md` | トレッド比の検証 | 機体設計の検討 |
| `docs/logs/` | 自動保存された実行ログ | 回帰調査・ばらつき解析 |

---

## 7. メンター向け注意事項

- **子どもの run ファイルを勝手に整形しない**
  pre-commit が走ると import 順やスペースが変わり、子どもが混乱します。
  `run*.py` 向けの per-file ignore は既に設定済みですが、
  構造変更を伴うリファクタは必ず本人と一緒に行ってください。
- **`setup.py` の変更は影響範囲が広い**
  全 run が依存しているため、物理パラメータや PID を変更した場合は
  必ず直線・スクエア・カーブの再評価を行い、`docs/` に記録を残してください。
- **`selector.py` は競技本番の生命線**
  `dev` フラグの取り違え、`programs` リストの順序ミスは本番事故に直結します。
  大会直前は変更を最小限にし、変更した場合は全プログラムを通しで動作確認してください。
- **ログの扱い**
  `docs/logs/` は現状 Git 管理対象です。ファイル数が増えて diff がうるさくなったら、
  `.gitignore` への追加や別リポジトリへの分離を検討してください。
- **複数 PC 運用時の衝突**
  各メンバーが別ブランチで作業し、メンターがマージする運用が安全です。
  同じファイルを複数人で同時編集させないようにしてください
  （特に `selector.py` と `setup.py`）。
- **Windows 固有の罠**
  `launch.json` の `env.PYTHONUTF8=1` は Windows での文字化け対策です。削除しないこと。

---

## 8. よくあるトラブル

| 症状 | 原因 | 対処 |
|------|------|------|
| `No module named pybricksdev` | `.venv` 未有効化 / 未インストール | `pip install --pre -r requirements.txt` |
| `ruff: command not found` | `requirements-dev.txt` 未インストール | `pip install -r requirements-dev.txt` |
| ハブに接続できない | Bluetooth 未待受 / 名前不一致 | ハブの Bluetooth ボタン押下、`launch.json` の `--name` 確認 |
| ロボットがまっすぐ進まない | PID / トレッド / タイヤ径 | `docs/how_to_reduce_SD.md` の手順で再調整 |
| リフトが動かない | `Port.A` / `Port.E` 未接続 → NullMotor | 物理接続を確認。意図的に外している場合は想定通り |
| ボタン連打で二重実行 | `selector.py` の `wait(50)` デバウンス不足 | 必要なら待機時間を延ばす |

---

## 9. 参考リンク

- Pybricks: https://pybricks.com/
- Pybricks コードエディタ: https://code.pybricks.com/
- pybricksdev: https://github.com/pybricks/pybricksdev
- FIRST LEGO League: https://www.firstlegoleague.org/
