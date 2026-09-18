# Desktop app

主画面を仕様の一覧と詳細に変更したmacOSアプリです。
半透明の背景とカードを使い、spec-groupで絞り込み、現在・予想/計画・過去を
同一画面のセクションで表示します。各セクションのカードを横スクロールし、
左右ボタンやトラックパッドでカードを移動し、選択したSpecを生んだIntentと後続の変更を確認できます。

## 起動

```sh
python3 -m pip install '.[desktop]'
spec-graph-desktop --graph .spec-graph/graph.json
```

引数なしで起動し、「ファイルを開く」でJSONを選択することもできます。
「GitHubから開く」はローカルのgh認証を使い、OWNER/REPOのdefault branchを読みます。
このモードのキャッシュはmacOSの `~/Library/Caches/Spec-Graph` に保存します。
ローカルJSONの閲覧は読み取り専用で、Issue/PR状態の取得はGitHubモードで行います。
読み込み失敗時はエラーを表示して以前の選択を保持します。

## .appのビルド

```sh
python3 -m pip install '.[desktop]' pyinstaller
./scripts/build_desktop.sh
open dist/Spec-Graph.app
```

Pythonとアセットを同梱します。ghは別途インストール・認証が必要です。
現在の検証対象はmacOSのみです。ローカルビルドはad-hoc署名で、
Developer ID署名・Apple公証・自動更新・インストーラー配布は未対応です。

## 選定

[pywebview](https://pywebview.flowrl.com/guide/)でOSのWebViewを使用し、Pythonの既存検証・取得ロジックに直接接続します。
[Tauri](https://v2.tauri.app/develop/sidecar/)も候補ですが、既存Pythonをsidecarとして梱包する構成が増えるため、今回はpywebviewを選びました。
[公式のパッケージ化手順](https://pywebview.flowrl.com/guide/freezing.html)に沿ってPyInstallerで.appを作ります。

仕様モデルは維持します。以前のグラフ表示は `spec-graph view` で引き続き利用できますが、
デスクトップの主画面は仕様一覧です。編集・適用は既存CLIを利用します。
