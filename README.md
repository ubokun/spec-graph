# Spec-Graph

**仕様をNodeに、変更の意図をEdgeに。**

Spec-Graphは「現在、何が正しい仕様なのか」と「なぜそうなったのか」を、
ソースコードと同じリポジトリで管理するOSSです。Intentは複数の変更元と変更先を
結ぶ有向ハイパーエッジであり、仕様の分割・統合も表現できます。

初期実装（Alpha）です。Python 3.11以上、実行時の外部Python依存はありません。
GitHub連携には認証済みの `gh` CLIが必要です。

## Quick start

```sh
python3 -m pip install .
spec-graph --graph examples/graph.json validate
spec-graph --graph examples/graph.json view
# http://127.0.0.1:8765
```

管理対象リポジトリ内で初期化します。

```sh
spec-graph init --repo OWNER/REPO
```

`.spec-graph/graph.json` と `.agents/skills/spec-graph-atomizer/SKILL.md` が生成されます。
`.gitignore` に `.spec-graph/cache/` を追加してください。
既存グラフ・Skillは上書きしません。

## Components

| コンポーネント | 初期実装 |
| --- | --- |
| Spec-Graph | JSON形式、nullnode、自然言語Spec、グループ、予想と適用、CLI |
| Spec-Graph-CI | 構造・履歴差分・Issue/PR書式と対応関係の検証 |
| Spec-Graph-Atomizer | 初期化時に導入されるIntent駆動開発Skill |
| Spec-Graph-Visualizer | ローカルWeb UI、予想と履歴、Issue/PR状態、ghによる読み取り |

## Change a specification

1. `spec_groups` に画面・API・コンポーネントなどの分類を定義します。
2. 変更後の自然言語仕様を `proposals` に作成します。複数グループへの所属が可能です。
3. `intents` に理由・唯一のintent-group・`before` / `after` を記録します。
4. Issueのない予想は `issue: null`、`pr: null` とします。
5. Issue、PR、実装・検証結果を揃え、`spec-graph apply INTENT_ID` を実行します。
6. グラフをコードと一緒にレビューし、マージします。

```sh
spec-graph validate
spec-graph diff --base /path/to/base-graph.json
spec-graph ci --base /path/to/base-graph.json --pr 42 \
  --pr-body /path/to/pr.md --issue-body /path/to/issue.md
```

適用は現在のブランチ上のスナップショットを更新します。正本はdefault branchです。
IssueのクローズやPRのオープンだけで、現在の仕様を自動変更しません。

## Visualizer

```sh
# ローカルのグラフ
spec-graph view
# ghでアクセスできるGitHubリポジトリのdefault branch
spec-graph view --repo OWNER/REPO
```

ブラウザで開く／更新ボタンを押すたびに取得します。リポジトリはcloneせず、
グラフとリンク先の状態のみを保存します。ソースコード・Issue本文・PR本文は保存しません。
キャッシュの更新と制限は [設計](docs/design.md) を参照してください。

## Documentation

- [ドメインモデル・設計判断](docs/design.md)
- [データ形式・例](docs/format.md)
- [CI統合と検証範囲](docs/ci.md)
- [貢献方法](CONTRIBUTING.md)

## License

MIT。ライセンス本文は [LICENSE](LICENSE) を参照してください。
