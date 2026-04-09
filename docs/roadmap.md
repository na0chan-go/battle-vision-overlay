# ロードマップ

## Phase 1: bootstrap

- monorepo の基本構成を整える
- Python / Go / UI / schemas / shared の責務分離を明文化する
- 最小の起動確認手段を用意する

## Phase 2: speed engine

- 素早さ候補計算の基盤を Go 側に作る
- マスタデータ参照の流れを固める

## Phase 3: vision PoC

- 盤面 2 体の観測 PoC を作る
- 認識結果を observation DTO に落とし込む

## Phase 4: integration

- Python と Go を DTO で接続する
- 観測から判定までの流れを通す

## Phase 5: overlay

- 表示用 DTO を UI に流し込む
- 最小のオーバーレイ表示を確認する

## Phase 6: gender/form/mega support

- 性別・フォルム・メガ状態の扱いを拡張する

## Phase 7: team preview and switch tracking

- 選出情報や交代追跡を扱う

## Phase 8: advanced battle-state inference

- より高度な対戦状態推論を追加する
