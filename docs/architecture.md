# アーキテクチャ

## 全体像

`battle-vision-overlay` は、認識・対戦ロジック・表示を分離した monorepo として構成します。

- `vision-py`: 画面から観測事実を抽出する認識レイヤー
- `engine-go`: 観測結果をもとに素早さ候補や表示 DTO を返すロジックレイヤー
- `overlay-ui`: 利用者へ overlay DTO を表示するプレゼンテーションレイヤー
- `schemas`: 各レイヤー間で受け渡す DTO 契約
- `shared/master-data`: ポケモンの基礎データ
- `shared/player-config`: 自分側の実数値など、ユーザー設定に近いデータ

## Python と Go の責務分離

Python 側は画面認識専用です。OCR やテンプレート照合、観測値の抽出など、画面から事実を得る処理を担当します。

Go 側は対戦ロジック専用です。Python が出力した observation DTO を受け取り、マスタデータと player config を参照して、素早さ候補や表示用 overlay DTO へ変換します。

この責務分離により、認識精度の改善と対戦ロジックの改善を独立して進められるようにします。

## DTO で疎結合にする方針

各コンポーネント間の通信契約は `schemas/` に置く JSON Schema を正として扱います。

- `vision-py` は観測 DTO を生成する
- `engine-go` は観測 DTO を入力として処理する
- `overlay-ui` は表示 DTO を消費する

実装言語ごとの型定義は将来的に追加できますが、契約の起点は常に `schemas/` とします。

現在の最小連携は以下の流れです。

1. `vision-py` がサンプル画像から `observation` を生成する
2. `vision-py` が `POST /api/v1/overlay/preview` へ observation DTO を送る
3. `engine-go` が `shared/master-data/pokemon.json` と `shared/player-config/player_speed.json` を参照する
4. `engine-go` が `overlay` DTO を返す
5. `overlay-ui` が overlay DTO または sample JSON を表示する

## データ配置の方針

設定値、sample、debug 出力は役割を分けて配置します。

- `shared/master-data/`: 種族値など、アプリ全体で共有するマスタデータ
- `shared/player-config/`: 自分側の実数値など、ユーザー設定に近いデータ
- `assets/samples/battle/`: vision-py の再現用サンプル画像
- `overlay-ui/samples/`: overlay-ui の表示確認用 sample JSON
- `assets/debug/single-run/`: 単発実行の crop、前処理画像、observation、overlay response
- `assets/debug/validation/`: 複数サンプル検証の画像別 debug 出力

sample は再現用入力、debug は実行結果として扱い、混在させない方針です。

## MVP の対象

最初の MVP は、現在の盤面に出ている 2 体の認識と、素早さ候補の表示までを対象にします。

現時点では、名前 OCR、辞書照合、gender 判定、form / mega_state の DTO 受け渡し、player.speed_actual の設定値参照、unknown / error 表示の土台までを扱います。

## 後続フェーズ

選出管理や交代追跡は後続フェーズで扱います。

同様に、耐久推定、技や持ち物の推定、自動メガ判定、高度な対戦状態推論も MVP の対象外とし、段階的に拡張します。
