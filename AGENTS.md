# AGENTS

## 基本方針

- このリポジトリでは bootstrap 段階では勝手に機能拡張しない
- Python は認識専用、Go は対戦ロジック専用
- DTO は `schemas/` を正とする
- 変更は小さく保つ
- public な仕様変更時は `docs/` を更新する
- Go 側を触ったら `gofmt` とテストを実行する
- Done の条件は、要求されたスコープだけを満たすこと
