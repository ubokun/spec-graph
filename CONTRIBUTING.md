# Contributing

まずIssueで目的・影響する仕様・受け入れ条件を共有してください。
変更意図と計測方法を明示し、既存仕様の履歴を保存する変更を歓迎します。

```sh
python3 -m pip install -e .
python3 -m unittest discover -s tests -v
python3 -m spec_graph --graph examples/graph.json validate
```

コアは標準ライブラリだけで動作します。形式互換性を変える場合はversionの変更と移行方針が必要です。
PRには変更理由・変更点・検証結果を記載してください。

Visualizerを変更する場合は `npm ci --ignore-scripts` と `npm test` も実行してください。
ライブラリ更新手順は [Visualizer](docs/visualizer.md) にあります。
