#!/bin/sh
# このリポジトリの git フックをインストールする。
# 各自の環境で一度だけ実行: sh scripts/install-hooks.sh
# （フックは .git/ 配下に入り git 管理されないため、clone した人は都度実行が必要）

set -e
ROOT=$(git rev-parse --show-toplevel)
SRC="$ROOT/scripts/hooks/pre-commit"
DST="$ROOT/.git/hooks/pre-commit"

cp "$SRC" "$DST"
chmod +x "$DST"
echo "installed: $DST"
