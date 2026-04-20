# ロードマップ

## Phase 1: bootstrap

- monorepo の基本構成を整える
- Python / Go / UI / schemas / shared の責務分離を明文化する
- 最小の起動確認手段を用意する
- 状態: 完了

## Phase 2: speed engine

- 素早さ候補計算の基盤を Go 側に作る
- マスタデータ参照の流れを固める
- player.speed_actual を設定値から参照する
- 状態: 最小実装済み

## Phase 3: vision PoC

- 盤面 2 体の観測 PoC を作る
- 認識結果を observation DTO に落とし込む
- 複数サンプル画像で検証し、debug 出力を確認できるようにする
- 状態: 最小実装済み、精度改善を継続

## Phase 4: integration

- Python と Go を DTO で接続する
- 観測から判定までの流れを通す
- unknown / error の扱いを整理する
- 状態: 最小実装済み

## Phase 5: overlay

- 表示用 DTO を UI に流し込む
- 最小のオーバーレイ表示を確認する
- sample JSON で正常、partial、unknown、error を確認できるようにする
- 状態: 最小実装済み

## Phase 6: gender/form/mega support

- 性別・フォルム・メガ状態の扱いを拡張する
- 現在は gender の最小判定と、form / mega_state の DTO 受け渡しを扱う
- 自動メガ判定やフォルム自動判定は未対応

## Phase 7: team preview and switch tracking

- 選出情報や交代追跡を扱う
- 状態: 未着手

## Phase 8: advanced battle-state inference

- より高度な対戦状態推論を追加する
- 状態: 未着手
