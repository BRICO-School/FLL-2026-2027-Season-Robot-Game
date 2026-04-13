# 🤖 ぼくら・わたしたちのロボットゲーム 2026-2027

ようこそ！ これは **FIRST LEGO League 2026-2027シーズン** の
ロボットゲーム用プログラムです。
チームでロボットを動かすための「命令書（めいれいしょ）」がここに入っています。

> メンターの方へ: 詳しい説明は [`README_FOR_MENTORS.md`](./README_FOR_MENTORS.md) を見てください。

---

## 🟢 はじめての人へ: まず覚える3つのこと

1. **自分のプログラムは `run_○○_名前.py` ファイルに書く**
2. **動かすボタンは `F5`** （VS Code の上に緑の▶が出てるときに押す）
3. **2 つのモードを使い分ける** ⬇️

### 🛠 ふだんの開発 vs 🏆 大会本番 — どっちを使う？

| いつ | 何を実行する？ | やること |
|------|----------------|----------|
| **ふだんの開発・テスト** | `run_*.py` を **直接 F5** | 1 つのミッションだけを何度も試す。うごきの調整、こわさずに試行錯誤。 |
| **大会に向けて通し練習・本番** | `selector.py` を F5 | 複数のミッションを **続けて** 実行する。ハブのボタンで番号をえらんで、フォースセンサーで発射。 |

> つまり: **ひとつずつ直したい → `run_*.py`** 、**ぜんぶ続けて走らせたい → `selector.py`**。
> 大会が近づいたら自分の `run_*.py` を `selector.py` の `programs` リストに登録しよう！

---

## 🚀 使う前のじゅんび（最初の1回だけ）

おうちの PC でも、学校の PC でも、**Windows / Mac どちらでも** 同じ手順です。

### ① Python のおまじないを入れる（仮想環境）

ターミナル（VS Code の下のまっくろい画面）で、順番にうつ：

**Windows の人:**
```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

**Mac の人:**
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

> 「`(.venv)`」がターミナルの左に出ていれば、じゅんびOK！

### ② Pybricks をハブに書きこむ

これは **ハブ（ロボットの脳みそ）ごとに1回だけ** やります。

1. Chrome で [https://code.pybricks.com](https://code.pybricks.com) を開く
2. ハブを USB ケーブルで PC につなぐ
3. 画面の「Install Pybricks Firmware」でハブに書きこむ
4. ハブに **名前** をつける （例: `Pybricks Hub`、`Pybricks Hub2`、`Pybricks Hub3` …）

> 名前が `Pybricks Hub` / `Pybricks Hub2` / `Pybricks Hub3` / `Pybricks Hub4` / `Pybricks Hub5`
> になっていると、VS Code からすぐに使えます！

---

## 💻 あたらしい PC でつかえるようにする（端末追加）

新しい PC（おうちのパソコン、学校のパソコンなど）からこのプロジェクトを
つかえるようにする手順です。**1 台につき 1 回だけ** やればOK。

### ① 道具をインストール（最初の1回）

| 入れるもの | どこから | メモ |
|----------|---------|------|
| **Git** | https://git-scm.com/ | Windows は「Git for Windows」、Mac は `brew install git` |
| **Python 3.9 以上** | https://www.python.org/ | Windows は「Add to PATH」に✅ |
| **VS Code** | https://code.visualstudio.com/ | みんなこれで書いています |
| **Google Chrome** | https://www.google.com/chrome/ | Pybricks のファームウェア書きこみに使う |

VS Code を開いたら、左の四角いマーク（拡張機能）から
「**Python**」拡張機能を入れておいてね。

### ② このプロジェクトをダウンロード（クローン）

ターミナル（VS Code の下のまっくろい画面）で:

```bash
git clone https://github.com/BRICO-School/FLL-2026-2027-Season-Robot-Game.git
cd FLL-2026-2027-Season-Robot-Game
```

> フォルダがもうある人は `cd` でそこへ移動するだけでOK。

### ③ 仮想環境をつくる

上の「🚀 使う前のじゅんび」の手順①をやってください。
（Windows と Mac で少しコマンドがちがうよ）

### ④ VS Code でフォルダをひらく

```
File → Open Folder → FLL-2026-2027-Season-Robot-Game
```

左下に「Python 3.xx (.venv)」と出ていたらOK！
もし出てなかったら **Ctrl+Shift+P**（Mac は **Cmd+Shift+P**）
→ `Python: Select Interpreter` → `.venv` をえらぶ。

### ⑤ ハブとつなぐじゅんび

- **Windows**: なにもいりません。F5 でつながります。
- **Mac**: 初めて BLE を使うとき、Bluetooth の許可画面が出ることがあります → 「許可」をおす。

### ⑥ うごかしてみる

`run_template.py` を開いて **F5** → 自分のハブをえらんで実行！
「走行完了！」と出たらセットアップ成功です🎉

---

## 🧱 あたらしいハブを追加する（ハブ追加）

新しい SPIKE Prime ハブをチームに追加するときの手順です。
**ハブ 1 台につき 1 回だけ** やればOK。

### ① Pybricks のファームウェアを書きこむ

1. **Chrome** で [https://code.pybricks.com](https://code.pybricks.com) を開く
2. ハブを **USB ケーブル** で PC につなぐ
3. ハブのボタンを押して電源ON
4. 画面の左上の **歯車マーク → Install Pybricks Firmware** をおす
5. SPIKE Prime を選んで「Install」
6. 画面のとおりにボタンをおして書きこみ完了を待つ

> 書きこみちゅうはケーブルをぬかない！

### ② ハブに名前をつける

ファームウェア書きこみの最後に **ハブの名前** を決める画面が出ます。
かならず **この中から** えらんでね:

| 名前 | 使うとき |
|------|---------|
| `Pybricks Hub` | 1台目 |
| `Pybricks Hub2` | 2台目 |
| `Pybricks Hub3` | 3台目 |
| `Pybricks Hub4` | 4台目 |
| `Pybricks Hub5` | 5台目 |

> ✋ スペルをまちがえないで！ 大文字・小文字・スペースもそっくりそのまま。
> 「Pybricks」と「Hub」の間に **半角スペース1個**、
> `Hub2` の `2` の前には **スペースなし**。

### ③ 動くかたしかめる

1. VS Code で `run_template.py` を開く
2. 左下の歯車で **いま追加したハブ番号** の構成をえらぶ（例: `🤖 Robot 3 (Pybricks Hub3)`）
3. **F5** をおす
4. ハブの Bluetooth ボタン（真ん中）が青くピカピカしてるときに、もう一度 F5 でつながる
5. ハブの画面に「走行完了！」的な出力が出たらOK！

### 🆘 6台目いじょうのハブをふやしたいとき

`.vscode/launch.json` にあたらしい構成を足す必要があります。
**メンターにそうだん** してね（README_FOR_MENTORS.md に手順があります）。

---

## ▶️ ロボットを動かす（毎回やること）

### パターンA: 自分の `run_xx.py` を1つだけ動かす（**開発中はこれ**）

1. VS Code で動かしたい `.py` ファイルを開く（例: `run_M01_kanna.py`）
2. 左下の歯車マークで **自分のハブ** をえらぶ
   - 🤖 Robot 1 (Pybricks Hub)
   - 🤖 Robot 2 (Pybricks Hub2)
   - 🤖 Robot 3 (Pybricks Hub3)
   - 🤖 Robot 4 (Pybricks Hub4)
   - 🤖 Robot 5 (Pybricks Hub5)
3. **F5** をおす
4. ハブのブルートゥースボタンをおす（青くピカピカしてるとき）

### パターンB: 通し練習・大会本番（**`selector.py`**）

> 複数のミッションを **続けて** 走らせたいときはこちら。
> 自分の `run_*.py` を先に `selector.py` の `programs` に登録しておいてね。

1. `selector.py` を開く
2. F5 でハブに送る
3. ハブの **左右ボタン** で番号をきりかえる
4. **フォースセンサー（Port.C）を押す** → プログラムが動く！

### パターンC: ログをのこして動かす（あとで見直す用）

F5 のとき「📝 Robot X + Log」をえらぶと、
`docs/logs/○○/日付.log` に **全部の記録** がのこります。
「あれ？ さっきの失敗、なんで？」となったときに見直そう。

---

## 🤖 ロボットのつくり（ポート接続）

プログラムは **このつなぎ方** を前提に動きます。
ちがうポートにつなぐとうごきません！

| ポート | つなぐもの | むき |
|:------:|-----------|------|
| **F** | 左タイヤ | 反時計まわりが「前」 |
| **B** | 右タイヤ | 時計まわりが「前」 |
| **E** | 左アーム（リフト） | 時計まわりが「正」 |
| **A** | 右アーム（リフト） | 時計まわりが「正」 |
| **C** | フォースセンサー | プログラム実行ボタン |

> タイヤ（B・F）さえつながっていれば走れるよ。
> アームがないときはダミーが入るから止まりません。

---

## ✏️ あたらしい `run_xx.py` をつくる

1. `run_template.py` をコピーする
2. **自分の名前** を入れた名前にする（例: `run2_M04_hanako.py`）
3. `run()` の中にロボットの動きを書く
4. 競技で使いたいときは `selector.py` の `programs` に足す

### よく使うめいれい

```python
# まっすぐ進む・下がる
await robot.straight(400)                   # 400mm まえへ
await robot.straight(-200)                  # 200mm うしろへ
await robot.straight(300, speed=500)        # はやく進む
await robot.straight(500, timeout=3000)     # 3秒でタイムアウト

# まわる
await robot.turn(90)                        # 右に90度
await robot.turn(-45)                       # 左に45度

# カーブ
await robot.curve(200, 90)                  # 半径200mmで90度カーブ

# アームをうごかす
await left_lift.run_angle(300, 180)         # 左アーム 180度
await right_lift.run_angle(500, -360)       # 右アーム 逆に1周

# まつ
await wait(500)                             # 0.5秒まつ
```

**つまずいたら**: `run_template.py` の中にたくさんの例がのっています。そっちも見てね！

---

## 🧪 ちょっとしたコツ

- **うごきがおかしい → ジャイロをリセット** （selector を使えば自動でリセットされます）
- **まっすぐ進まない** → `docs/how_to_reduce_SD.md` を読むとヒントがあるよ
- **こわれた！** → あわてず `old/` フォルダーを見る。前のバージョンがあるかも
- **ハブが見つからない** → Bluetooth の名前があってる？ ハブのボタンはおした？
- **ruff: command not found** → 「じゅんび①」の `requirements-dev.txt` のインストールがまだ

---

## 📚 もっと知りたいとき

- [`docs/ayumu_roadmap.md`](./docs/ayumu_roadmap.md) — チームのロードマップ
- [`docs/ayumu_guide_progress.md`](./docs/ayumu_guide_progress.md) — すすみぐあい
- [`docs/how_to_reduce_SD.md`](./docs/how_to_reduce_SD.md) — ばらつきをへらすには
- [`docs/logs/`](./docs/logs/) — 走行ログ
- [`integrated-guide-v1.md`](./integrated-guide-v1.md) — 総合ガイド
- [`old/`](./old/) — ふるいファイル

---

**たのしんで、たくさん試そう！ ミスしてもだいじょうぶ、git がもどしてくれます。**
