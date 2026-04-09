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
PYTHONPATH=vision-py/src python3 -m vision.main
```

入力画像は `assets/samples/battle_sample.png`、出力先は `assets/debug/` です。
