# Format v1

トップレベルは `version`, `repository`, `spec_groups`, `intent_groups`, `nodes`, `proposals`,
`intents` の七つです。未知フィールドは誤記を見逃さないため拒否します。
実行可能な検証仕様は `spec_graph/core.py`、完全な例は `examples/graph.json` です。

| オブジェクト | フィールド |
| --- | --- |
| Spec-group | description: 空でない文字列 |
| Intent-group | description, measurement, evidence: 空でない文字列 / issue_sections, pr_sections: 見出し文字列の配列 |
| Spec Node | text: 自然言語 / groups: spec-group ID配列 / state: currentまたはpast |
| Proposal | text: 自然言語 / groups: spec-group ID配列 |
| Intent | text: 理由 / group: intent-group ID / state: plannedまたはapplied / before, after: ID配列 / issue, pr: 正整数またはnull |

Node、候補、Intent、各グループはIDをキーとするJSONオブジェクトです。
同じgraph内でNodeと候補のIDは重複できません。
配列内IDは重複不可、参照先は存在必須です。
通常Nodeのgroups、Intentのbefore/afterは空にできません。

```json
{
  "text": "入力の負担を減らすため、パスキー認証に変更する。",
  "group": "spec-graph:correctness@1",
  "state": "planned",
  "before": ["spec:login:v1"],
  "after": ["spec:login:v2"],
  "issue": null,
  "pr": null
}
```

この予想を進める場合、まずIssue番号を設定します。PRがある場合はPR番号も設定します。
`spec-graph apply INTENT_ID` は候補をNodeにし、変更元をpastにします。
履歴の削除、本文の直接編集、過去Nodeの復活は差分検証で拒否されます。

差分はversion=1と、applied_intents / added_nodes / retired_nodes / planned_intentsの
ソート済みID配列です。planned_intentsは追加・編集された計画のみを含みます。
計画削除・候補編集・グループ追加の完全な監査には元のGit差分を利用してください。
