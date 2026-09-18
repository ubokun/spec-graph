# Spec-Graph-CI

`validate` は単一グラフ、`diff` は新旧グラフ、`ci` は差分と当該PR/Issue書式を検査します。

```sh
spec-graph --graph examples/graph.json ci \
  --base examples/base.json --pr 2 \
  --pr-body examples/pr.md --issue-body examples/issue.md
```

CIでの手順:

1. 信頼する版のSpec-Graphをインストールします。
2. PRのbase SHAから旧graph.json、head SHAから新graph.jsonを取得します。
3. GitHub APIで当該PRの番号と本文、対応するIssueの本文を取得します。
4. それぞれをUTF-8ファイルに保存し、上記CLIへ渡します。

Issue番号と本文の対応は呼び出し側が保証します。CLIだけではリモートの実在確認をしません。
PR番号に対応するIntentは厳密に一件必要です。そのPRで別Intentを適用することはできません。
初回導入時のbaseには同じrepositoryを持つnullnodeのみの初期グラフを使用します。

必須見出しはMarkdownの `## 見出し` です。空の見出し・コードフェンス内の見出しは
受け入れません。本文内容の意味、測定値の正しさ、URL先エビデンスの存在は検証しません。
measurement/evidenceは人間・Skillの実施契約です。

同梱の `.github/workflows/test.yml` は本ツール自体のテストを実行します。
利用先リポジトリにグラフCI workflowを自動導入する機能はまだありません。
PR変更可能な検証コードに権限付きトークンを渡さず、read-only permissionsで実行してください。
PR由来文字列をシェルに直接展開せず、APIレスポンスやイベントJSONからファイルに保存してください。

公式参照:
- [GitHub CLI API](https://cli.github.com/manual/gh_api)
- [GitHub Actions secure use](https://docs.github.com/en/actions/reference/security/secure-use)
