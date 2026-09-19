# setup_last_season_backup.py について

- **中身**: 昨シーズン（2025-12〜2026-03 に整備・大会で使用）の本番用 `setup.py` を、
  **1バイトも変えずに**コピーしたもの（コピー日 2026-09-07）
- **元ファイルの最終コミット**: `1a9d56d` 2026-03-21「feat: 実行ログ自動保存機能」
- **sha1**: `a925b7c4dad317b0fa58396c14c433bf7e9d5fd4`（コピー時点の `setup.py` と同一）
- **なぜ残すか**: 2026-27 シーズンはローバー型の新機体になり、`setup.py` の数値
  （wheel_diameter / axle_track / DEFAULT_*_SETTINGS / PID）を新機体の実測で書きかえる。
  昨年の値と見くらべたり、必要なら戻したりできるように、上書き前の姿を保存しておく
- **書きかえの手順**: `FLL-2026-2027-Season-Robot-Game-replication-study/06-本番機セットアップ確定の指示書.md`

## 昨年の主な値（このバックアップの中身の抜き書き）

| 項目 | 値 |
|---|---|
| wheel_diameter | 62 mm |
| axle_track | 85 mm |
| DEFAULT_STRAIGHT_SETTINGS | straight_speed 400 mm/s / straight_acceleration 500 mm/s² |
| DEFAULT_TURN_SETTINGS | turn_rate 240 deg/s / turn_acceleration 850 deg/s² |
| DEFAULT_CURVE_SETTINGS | straight_speed 240 / straight_acceleration 800 |
| distance_control PID | kp 1000 / ki 50 / kd 10 |
| heading_control PID | kp 2000 / ki 50 / kd 100 |
| ポート | 左タイヤ F（CCW）・右タイヤ B（CW）・左リフト E・右リフト A |
| ハブの向き | top_side=Axis.Z / front_side=Axis.X |
| ジャイロ | use_gyro(True) |

> **このファイルは編集しない。** 差分を見たいときは
> `git diff --no-index old/setup_last_season_backup.py setup.py` を使う。
