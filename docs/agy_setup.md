# Antigravity CLI (agy) 環境構築ガイド — Mac / Windows(WSL)

run ファイルをコミットすると変更ログが自動記録される仕組み（pre-commit フック）で、
**変更概要の1行を AI に書かせる**ために Antigravity CLI (`agy`) を使う。
このガイドは、新しい端末で `agy` をセットアップしてフックを有効化する手順をまとめたもの。

> **前提知識**
> - フック本体: `.git/hooks/pre-commit`（git では共有されないので**端末ごとに導入が必要**）
> - 導入コマンド: `sh scripts/install-hooks.sh`
> - ログの記録先: `docs/logs/<runファイル名>/`（`HISTORY.md` と `YYYYMMDD_作業ログ.md`）
> - `agy` が無い／使えない端末では、要約が**機械文(`+N/-M 行`)に降格**するだけで、
>   **生 diff は必ず記録される**（記録自体は止まらない）。

---

## 0. どの端末で AI 要約が出る？（早見表）

| 端末 | AI 要約 | 必要なもの |
|---|---|---|
| Mac | ◯（見込み） | python3 + agy(Mac版) + フック導入 |
| Windows + WSL | ◯（確認済み） | WSL + WSL内 agy + Windows の Python(py) + フック導入 |
| Windows のみ（WSLなし） | ✕ → 機械文 | ― （Windows版 agy.exe はヘッドレス出力不可） |

> **重要**: Windows ネイティブの `agy.exe` は「本物の端末(コンソール)」でしか出力しない仕様のため、
> フックからのヘッドレス利用では使えない。**Windows では必ず WSL 経由**にすること。

---

## 1. Mac のセットアップ

### 1-1. Python の確認
```bash
python3 --version   # 3.8 以上が望ましい。無ければ Homebrew 等で導入
```

### 1-2. Antigravity CLI (agy) のインストール
```bash
curl -fsSL https://antigravity.google/cli/install.sh | bash
```
- バイナリは `~/.local/bin/agy` に置かれ、PATH 追記の案内が出る。
- **ターミナルを再起動**（または `source ~/.zshrc` 等で PATH を反映）。

### 1-3. 動作確認とログイン
```bash
agy --version
agy -p "say OK"      # 初回はブラウザで Google サインインが開く
```
`OK` が返ればヘッドレス利用OK。

### 1-4. フックの導入
リポジトリのルートで一度だけ:
```bash
sh scripts/install-hooks.sh
```

> Mac 版 agy は Unix バイナリなので WSL/Linux 同様パイプ出力できる見込み（＝AI要約が出る）。
> もし要約が機械文のままになる場合は、`agy` が使えていない（未ログイン等）か、Mac版にも
> 端末出力制限がある可能性。その場合でも diff は記録される。

---

## 2. Windows のセットアップ（WSL 経由）

Windows では「WSL を入れる → WSL の中に agy を入れる」。コミットを Windows 側
(VS Code / Cursor / Antigravity GUI / Git Bash) から行っても、フックが自動で
`wsl.exe` 経由で WSL の agy を呼ぶ。

### 2-1. WSL の導入
**管理者権限の PowerShell** で:
```powershell
wsl --install
```
- 既定で Ubuntu が入る。完了後に **PC を再起動**し、初回起動時に WSL の
  ユーザー名・パスワードを設定する。
- 既に WSL がある場合はスキップ可（`wsl -l -v` で確認）。

### 2-2. WSL 内の Python と agy
WSL(Ubuntu) のターミナルで:
```bash
sudo apt update && sudo apt install -y python3 curl
curl -fsSL https://antigravity.google/cli/install.sh | bash
```
- `agy` は WSL 内の `~/.local/bin/agy` に入る。**WSL シェルを開き直して** PATH を反映。

### 2-3. WSL 内 agy のログイン（ここが肝心）
```bash
agy --version
agy -p "say OK"
```
- ブラウザが開くか、**認証用 URL とワンタイムコードが表示**されるので、
  指示に従って Google でログインする（WSL はリモート扱いになる場合がある）。
- `OK` が返れば WSL の agy はヘッドレスで使える状態。

### 2-4. Windows 側の Python（フック実行に必要）
コミットを Windows から行うと、フックは **Git for Windows の Git-Bash** で動くため、
**Windows 側にも Python が必要**（`py` ランチャ）。
```powershell
py --version
```
無ければ <https://www.python.org/downloads/windows/> から導入（"Add python.exe to PATH" と
py ランチャを有効に）。pyenv-win を使っている場合は `pyenv global <version>` で
グローバル版を設定しておく。

### 2-5. フックの導入
リポジトリのルートで一度だけ（WSL でも Git-Bash でも可）:
```bash
sh scripts/install-hooks.sh
```

> **仕組み**: Windows からコミット → フック(Git-Bash) → `py` で `scripts/changelog_hook.py`
> → Windows では `wsl.exe -e bash -lc 'agy -p "$(cat)"'` で WSL の agy にプロンプトを渡し、
> 返ってきた要約を記録する。WSL からコミットした場合は WSL の agy を直接呼ぶ。

---

## 3. 動作確認（共通）

1. 任意の `run_*.py`（トップ階層のもの）を少し編集する。
2. `git add <その run ファイル>` して `git commit` する。
3. コミット時に `[changelog-hook] 記録: <ファイル> — <要約>` が表示される。
4. `docs/logs/<runファイル名>/` に `HISTORY.md` と `YYYYMMDD_作業ログ.md` が
   作成／追記され、run ファイル先頭 docstring の `【更新履歴】` に1行増えていれば成功。
   - 要約が日本語の文になっていれば AI 要約（agy）が効いている。
   - `コードを変更（+N/-M 行）` のような機械文なら agy が使えていない（diff は記録済み）。

---

## 4. トラブルシューティング

| 症状 | 原因 | 対処 |
|---|---|---|
| コミットしても何も記録されない | フック未導入 | `sh scripts/install-hooks.sh` を実行 |
| `[changelog-hook] WARNING: python が見つからず…` | Python 不在 | Mac/WSL は python3、Windows は py を導入 |
| 要約が常に機械文（`+N/-M 行`） | agy が使えない | `agy -p "say OK"` が通るか確認（未ログイン/PATH/WSL未導入） |
| `agy: command not found`（導入直後） | PATH 未反映 | ターミナルを開き直す |
| Windows でだけ機械文になる | WSL 未導入 or WSL の agy 未ログイン | 「2. Windows のセットアップ」を実施 |
| コミットが止まる | フックは設計上止めない | 止まる場合は別のフック/設定を確認 |

---

## 5. 補足

- **フックの配布**: `.git/hooks/` は git 管理外なので、clone した人は各自
  `sh scripts/install-hooks.sh` を実行する。
  代わりに各端末で一度 `git config core.hooksPath scripts/hooks` を設定すると、
  バージョン管理された `scripts/hooks/pre-commit` が直接使われ、更新も自動反映される。
- **記録される3か所**:
  1. run ファイル先頭 docstring の `【更新履歴】`
  2. `docs/logs/<名>/HISTORY.md`（表に1行）
  3. `docs/logs/<名>/YYYYMMDD_作業ログ.md`（要約＋生diff）
- **再インストール/更新**: `agy update`（CLI 自身の更新）。サインアウトは agy 起動中に `/logout`。
