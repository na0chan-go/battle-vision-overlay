# battle-vision-overlay

Unofficial personal research project for real-time battle-state recognition and overlay rendering.

This project is not affiliated with, endorsed by, or sponsored by Nintendo, Game Freak, or The Pokémon Company.

All game titles, character names, and related marks are property of their respective owners.

## 概要

`battle-vision-overlay` は、リアルタイムの対戦画面認識とオーバーレイ表示を扱う非公式の個人研究プロジェクトです。

現在は、対戦画面サンプル画像から player / opponent の名前領域を切り出し、OCR、辞書照合、gender 判定、observation DTO 生成、Go API への送信、overlay DTO 表示までを最小 PoC としてつないでいます。

## リポジトリ構成

- `vision-py/`: Python 製の画面認識レイヤー。crop、OCR、辞書照合、gender 判定、observation DTO 生成を担当します。
- `engine-go/`: Go 製の対戦ロジックレイヤー。observation DTO を受け取り、素早さ候補と overlay DTO を生成します。
- `overlay-ui/`: 表示レイヤー。overlay DTO の sample JSON や URL 指定 JSON を読み込んで表示します。
- `shared/master-data/`: species_id、display_name、gender、form、mega_state、種族値を持つ共通マスタデータです。
- `shared/player-config/`: 自分側の実数値設定です。現在は `player_speed.json` で `player.speed_actual` を管理します。
- `schemas/`: Python / Go / UI 間で受け渡す DTO 契約の JSON Schema です。
- `assets/samples/`: 検証用の対戦画面サンプル画像置き場です。
- `assets/debug/`: crop 画像、前処理後画像、observation JSON、overlay response、validation report などの debug 出力先です。生成物は git 管理対象外です。
- `docs/`: アーキテクチャやロードマップなど、README より詳細な補足資料です。

## 前提ツール

- Python 3.11 以上
- Go 1.22 以上
- `make`
- ブラウザ

`overlay-ui` は現時点では依存パッケージ不要の静的 HTML / CSS / JavaScript です。Node.js や npm install は不要です。

## セットアップ

repo root で作業します。

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e vision-py
```

Go 側は標準ライブラリ中心です。動作確認は以下で行えます。

```sh
make test-go
```

全体の bootstrap 用 target もあります。

```sh
make setup
```

OCR には Python-only の `easyocr` を使っています。初回実行時は OCR モデルの取得で時間がかかることがあります。

## 最短の動作確認

1. Go API を起動します。

```sh
make run-go
```

2. 別ターミナルで疎通確認します。

```sh
curl http://localhost:8080/healthz
```

3. Python からサンプル画像を処理し、Go API に observation DTO を送ります。

```sh
PYTHONPATH=vision-py/src python3 -m vision.main \
  --image assets/samples/battle_sample.jpeg \
  --ocr-names \
  --request-overlay
```

4. overlay UI を開きます。

```sh
python3 -m http.server 4173
```

ブラウザで以下を開きます。

```text
http://localhost:4173/overlay-ui/web/
```

## engine-go の実行

API サーバーを起動します。

```sh
make run-go
```

主なエンドポイント:

- `GET /healthz`: 疎通確認
- `GET /speed-test?base_speed=102`: Lv50 固定の素早さ候補確認
- `POST /api/v1/overlay/preview`: observation DTO を受け取り overlay DTO を返す

例:

```sh
curl "http://localhost:8080/speed-test?base_speed=102"
```

Go 側のテスト:

```sh
make test-go
```

Go 側を編集した場合は `gofmt` も実行します。

```sh
make fmt-go
```

## vision-py の実行

単一画像の status panel crop:

```sh
PYTHONPATH=vision-py/src python3 -m vision.main \
  --image assets/samples/battle_sample.jpeg
```

名前領域 OCR、辞書照合、gender 判定の確認:

```sh
PYTHONPATH=vision-py/src python3 -m vision.main \
  --image assets/samples/battle_sample.jpeg \
  --ocr-names \
  --resolve-names \
  --json
```

observation DTO を生成して保存:

```sh
PYTHONPATH=vision-py/src python3 -m vision.main \
  --image assets/samples/battle_sample.jpeg \
  --ocr-names \
  --emit-observation
```

省略時の保存先は `assets/debug/observation.json` です。

Go API へ送信して overlay DTO を受け取る:

```sh
PYTHONPATH=vision-py/src python3 -m vision.main \
  --image assets/samples/battle_sample.jpeg \
  --ocr-names \
  --request-overlay
```

省略時の保存先は `assets/debug/overlay_response.json` です。

`form` / `mega_state` は暫定入力として CLI から指定できます。`mega_state` は `base` / `mega` のみ受け付け、未指定時は `base` です。`form` は未指定時 `unknown` です。

```sh
PYTHONPATH=vision-py/src python3 -m vision.main \
  --image assets/samples/battle_sample.jpeg \
  --ocr-names \
  --request-overlay \
  --player-mega-state mega \
  --opponent-mega-state base
```

## 複数サンプル検証

`assets/samples/` 配下の `.png` / `.jpg` / `.jpeg` をまとめて処理します。

```sh
PYTHONPATH=vision-py/src python3 -m vision.main --validate-samples
```

出力:

- `assets/debug/validation_report.json`: 一覧レポート
- `assets/debug/validation/<image_file_name>/`: 画像ごとの crop、前処理後画像、gender crop、observation JSON

ステータス判定:

- `success`: player / opponent の両方で `species_id != unknown`
- `partial`: 片方だけ `species_id != unknown`
- `failed`: 両方 unknown または処理失敗

ファイル名に `1080p` / `720p` / `scaled` / `with_margin` / `dark` / `compressed` を含めると、`condition_label` と条件別集計に反映されます。

## overlay-ui の実行

repo root で静的ファイルサーバーを起動します。

```sh
python3 -m http.server 4173
```

ブラウザで以下を開きます。

```text
http://localhost:4173/overlay-ui/web/
```

ページ起動時は `overlay-ui/samples/overlay_sample_ok.json` を読み込みます。画面上のボタンから以下の sample も確認できます。

- `overlay_sample_ok.json`: 正常系
- `overlay_sample_opponent_unknown.json`: 相手 unknown
- `overlay_sample_player_unknown.json`: 自分 unknown
- `overlay_sample_unknown.json`: 両方 unknown
- `overlay_sample_error.json`: transport error 表示

`unknown` は `認識失敗`、速度や判定が比較不能な値は `−` / `比較不可` として表示します。`engine-go` は現在「最新 overlay DTO を GET する専用 API」を持たないため、UI 側では sample JSON と URL 指定 JSON の読み込みを最小導線としています。

## 設定ファイル

### `shared/master-data/pokemon.json`

ポケモンの共通マスタです。主に `engine-go` が opponent の `speed_candidates` を計算するために使います。`vision-py` の辞書照合も同じファイルの `species_id` / `display_name` を参照します。

各要素は以下の情報を持ちます。

- `species_id`
- `display_name`
- `gender`
- `form`
- `mega_state`
- `base_stats.spe`

`engine-go` は observation DTO の `species_id` / `gender` / `form` / `mega_state` を使って、通常個体、メガ、性別差分などを解決します。

### `shared/player-config/player_speed.json`

自分側の実数値設定です。`overlay DTO` の `player.speed_actual` を変えたい場合はここを編集します。

各要素は以下の情報を持ちます。

- `species_id`
- `gender`
- `form`
- `mega_state`
- `speed_actual`

設定が見つからない場合、現在の最小実装では該当ポケモンの最速候補を fallback として使います。ファイルを変更したら `engine-go` を再起動してください。

### `overlay-ui/samples/*.json`

UI 単体確認用の overlay DTO サンプルです。正常、partial、unknown、error の表示確認に使います。

### `assets/samples/`

vision-py の入力サンプル画像置き場です。validation はこのディレクトリの `.png` / `.jpg` / `.jpeg` を走査します。

### `schemas/`

DTO 契約です。public な DTO 形状を変えるときは、実装とあわせて schema も更新します。

## debug 出力の見方

省略時の出力先は `assets/debug/` です。

- `opponent_status_panel.png` / `player_status_panel.png`: status panel crop
- `opponent_name.png` / `player_name.png`: OCR 対象の raw crop
- `opponent_name_preprocessed.png` / `player_name_preprocessed.png`: OCR に渡す代表前処理画像
- `opponent_gender.png` / `player_gender.png`: gender 判定用 crop
- `observation.json`: vision-py が生成した observation DTO
- `overlay_response.json`: Go API から返った overlay DTO、または通信失敗時の error payload
- `validation_report.json`: 複数サンプル検証のサマリーと画像ごとの詳細
- `validation/<image_file_name>/`: 画像ごとの crop、前処理、gender、observation の保存先

`assets/debug/` は生成物置き場なので git 管理対象外です。

## 現在対応している範囲

- 現在の盤面の player / opponent の名前領域 crop
- OCR と辞書照合による `species_id` / `display_name` 解決
- gender 記号の最小判定
- `form` / `mega_state` の DTO 対応と CLI 暫定指定
- Python から Go への observation DTO POST
- Go 側の素早さ候補計算
- player の `speed_actual` 設定値参照
- overlay DTO の sample 表示
- unknown / partial / error 時の最小表示
- 複数サンプル画像の validation report 出力

## 未対応の範囲

- 選出画面の 6 体管理
- 交代追跡
- ターン履歴
- 耐久推定
- 技、持ち物、特性、ランク補正、天候、追い風、麻痺などの推定
- 自動メガ判定
- フォルム自動判定
- 透明ウィンドウ化などの本格 overlay 化
- 最新 overlay DTO を UI が自動購読する仕組み

## 開発ワークフロー

[CONTRIBUTING.md](./CONTRIBUTING.md) に、このリポジトリで採用するブランチ運用と日常的な開発ルールをまとめています。エージェント向けルールは [AGENTS.md](./AGENTS.md) を参照してください。

よく使う確認コマンド:

```sh
make test-go
PYTHONPATH=vision-py/src python3 -m unittest discover -s vision-py/tests -v
node --check overlay-ui/web/main.js
python3 -m json.tool schemas/observation.schema.json >/dev/null
python3 -m json.tool schemas/overlay.schema.json >/dev/null
python3 -m json.tool overlay-ui/samples/*.json >/dev/null
git diff --check
```

## 今後の予定

詳細は [docs/roadmap.md](./docs/roadmap.md) を参照してください。直近では、認識精度の検証、設定ファイルの運用整理、UI への連携導線改善を段階的に進めます。
