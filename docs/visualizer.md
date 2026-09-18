# Visualizer: フレームワーク選定と表示仕様

2026-09-18に公式ドキュメントとnpm配布物を確認。

| 候補 | 特徴と今回の判断 |
| --- | --- |
| [Cytoscape.js](https://js.cytoscape.org/) | グラフ可視化、ズーム・移動、イベント、レイアウト拡張を提供。Reactなしで既存のPython配信構成に組み込めるため採用。MIT。 |
| [React Flow](https://reactflow.dev/learn/customization/custom-nodes) | Reactコンポーネントでノード編集UIを構築できる。今回は閲覧中心で、Reactのビルド基盤を増やす利点が小さいため見送り。自動配置には[別のレイアウトライブラリを組み合わせる](https://reactflow.dev/learn/layouting/layouting)。 |
| [vis-network](https://visjs.github.io/vis-network/docs/network/layout.html) | 階層・物理配置を備える有力候補。今回はCytoscapeのグラフ要素操作とDagre拡張を使う設計を選んだ。 |

描画はCytoscape.js 3.34.3、階層配置はcytoscape-dagre 4.0.1。
[公式Dagre拡張](https://github.com/cytoscape/cytoscape.js-dagre)のバンドルには
Dagre 3.0.0とgraphlib 4.0.1が含まれる。すべてのライセンスを配布物に同梱する。

## 表示モデル

- Specは円、Intentは菱形の接続点。`before → Intent → after` の有向グラフに投影する。
- Intentの接続点は表示用であり、永続データ上のSpec Nodeを増やさない。
- 同じSpecは一度だけ描画し、m対nのIntentはm+n本の接続で表す。
- 現在は緑、過去は灰、候補は黄の破線。計画・予想の接続も破線。
- 横幅650px未満のキャンバスは縦配置、それ以外は左から右へ配置する。
- ドラッグ、ズーム、全体表示、再配置、Intent状態フィルター、ID/本文検索を提供する。
- 点・辺を選択すると詳細と隣接要素を強調する。キーボードでも一覧から選択できる。
- Issue/PR状態はIntent詳細に表示する。予想や変更元が過去になった計画も識別する。
- ノードの移動は表示上だけの変更で、保存されない。更新・再配置で自動配置へ戻る。
- 多数の要素は全体表示で縮小される。検索とズームで詳細を見る。大規模グラフの性能保証は未実施。

## 開発と配布

ブラウザは外部CDNへ接続しない。JS/CSSはPythonパッケージ内から配信する。
通常利用にNode.js/npmは不要。

```sh
npm ci --ignore-scripts
npm run vendor
npm test
python3 -m unittest discover -s tests -v
```

ライブラリ更新時はpackage.jsonとpackage-lock.jsonを更新し、vendorで生成した
JSとTHIRD_PARTY_LICENSES.txtもコミットする。CIで再生成結果との一致を確認する。
