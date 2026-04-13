# battle-vision-overlay

Unofficial personal research project for real-time battle-state recognition and overlay rendering.

This project is not affiliated with, endorsed by, or sponsored by Nintendo, Game Freak, or The Pokémon Company.

All game titles, character names, and related marks are property of their respective owners.

## 概要

`battle-vision-overlay` は、リアルタイムの対戦画面認識とオーバーレイ表示を扱う非公式の個人研究プロジェクトです。

責務は以下のように分離します。

- `vision-py`: Python 製。画面認識専用
- `engine-go`: Go 製。対戦ロジック・状態管理専用
- `overlay-ui`: 表示専用
- `shared`: 共通マスタデータ
- `schemas`: Python / Go / UI 間の DTO 契約

## MVP の範囲

最初の MVP では、現在の盤面に出ている 2 体の認識と、素早さ候補の表示までを対象にします。

以下は将来拡張の対象であり、現時点では未対応です。

- 選出管理
- 交代追跡
- 耐久推定
- 高度な対戦状態推論

## リポジトリ構成

- `docs/`: アーキテクチャとロードマップ
- `assets/`: テンプレート画像やサンプル素材置き場
- `shared/master-data/`: 共通参照データ
- `schemas/`: コンポーネント間 DTO の JSON Schema
- `vision-py/`: 認識系 Python モジュール
- `engine-go/`: 対戦ロジック系 Go モジュール
- `overlay-ui/`: UI 層の将来配置先

## 開発フロー

[CONTRIBUTING.md](./CONTRIBUTING.md) に、このリポジトリで採用するブランチ運用と日常的な開発ルールをまとめています。

bootstrap 段階でのエージェント向けルールは [AGENTS.md](./AGENTS.md) を参照してください。

## 最小起動確認

Go の API サーバーは以下で起動できます。

```sh
make run-go
```

起動後、以下で疎通確認できます。

```sh
curl http://localhost:8080/healthz
```

素早さ候補の確認用 API は以下です。

```sh
curl "http://localhost:8080/speed-test?base_speed=102"
```

## Vision PoC

固定領域の切り出し PoC は以下で実行できます。

```sh
PYTHONPATH=vision-py/src python3 -m vision.main --image assets/samples/battle_sample.jpeg
```

`--image` は必須です。出力先は省略時に実行ディレクトリ基準の `assets/debug/` になります。

名前領域の OCR PoC は以下で実行できます。

```sh
PYTHONPATH=vision-py/src python3 -m vision.main --image assets/samples/battle_sample.jpeg --ocr-names
```

JSON で確認したい場合は `--json` を付けます。前処理後画像は `assets/debug/` に保存されます。
OCR バックエンドは Python-only の `easyocr` を利用します。

OCR の生文字列をポケモン名辞書へ照合する PoC は以下です。

```sh
PYTHONPATH=vision-py/src python3 -m vision.main --image assets/samples/battle_sample.jpeg --ocr-names --resolve-names
```

辞書データは `shared/master-data/pokemon.json` を参照します。性別記号の切り出しと最小判定も同時に行い、`assets/debug/opponent_gender.png` と `assets/debug/player_gender.png` を保存します。

observation DTO の JSON を構築して標準出力とファイルへ出す PoC は以下です。

```sh
PYTHONPATH=vision-py/src python3 -m vision.main --image assets/samples/battle_sample.jpeg --ocr-names --emit-observation
```

出力ファイルは省略時に `assets/debug/observation.json` です。

## 最小連携 PoC

`vision-py` から `engine-go` へ observation DTO を POST し、overlay DTO を受け取る最小連携は以下です。

まず Go API を起動します。

```sh
make run-go
```

次に Python 側から observation を送ります。

```sh
PYTHONPATH=vision-py/src python3 -m vision.main --image assets/samples/battle_sample.jpeg --ocr-names --request-overlay
```

レスポンスは標準出力に pretty JSON で表示され、省略時は `assets/debug/overlay_response.json` にも保存されます。

## Overlay UI PoC

`overlay-ui/web` には、overlay DTO をそのまま表示する最小 UI を用意しています。

まず repo root で静的ファイルサーバーを起動します。

```sh
python3 -m http.server 4173
```

その後、ブラウザで以下を開きます。

```text
http://localhost:4173/overlay-ui/web/
```

ページを開くと `overlay-ui/samples/overlay_sample.json` を自動読込します。`URL から読む` で任意の overlay JSON を読み込むこともできます。`engine-go` は現在「最新 overlay DTO を GET する専用 API」を持たないため、UI 側では sample JSON と URL 指定の JSON 読み込みを最小導線としています。
