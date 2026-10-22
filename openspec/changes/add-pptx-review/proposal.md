## Why

de-ai-ui は Web フロントエンドの「AIっぽさ」しか扱えず、普段使いの PowerPoint 資料（生成AIで作った、またはAIに整えさせたスライド）に出る同じ症状（角丸カードの並び、絵文字・飾りアイコン、グラデーションと影、全部中央寄せ、「革新的」「シームレス」のようなAI文体）を直す手段がない。資料は社内外の人の目に触れる頻度が高く、ここでもAIっぽさを消したい（PBI-1）。

## What Changes

- 新スキル `/pptx-review [ファイル名]` を追加する。`input/` に置いた .pptx を1回に1ファイル扱い、引数を省略したら `input/` 内で更新日時がいちばん新しいものを対象にする。
- 分析担当の新サブエージェント `pptx-reviewer` を追加する。スライドの構造（図形・塗り・線・効果・テキスト・マスター/テーマ）とスライド画像を突き合わせ、AIっぽさと体裁の問題をパターン単位ですべて（件数の上限なし）、推奨案付きの修正案と一緒に返す。コードもファイルも編集しない。
- メインの会話は、ユーザーに確認せず、すべての指摘について推奨案を自動で採用する（選ばなかった案は report.md に残す）。採用した案は python-pptx（API に無いものは XML 直接操作）で、該当スライドにまとめて適用する。原因がスライドマスター/テーマにあれば、そちらも直す（【全スライドに影響】と明記）。
- 修正対象: 配色・グラデーション・影・角丸、絵文字・飾りアイコン、レイアウト・余白・整列、スライド本文の文章表現。発表者ノートは変更しない。
- 適用後は After を画像化し、`pptx-reviewer` がはみ出し・重なり・コントラスト・残ったAIっぽさを検証する。見つかった問題も推奨の直し方で自動で直してから出力を確定する（再検証は2回まで）。
- 出力: `output/<名前>-reviewed.pptx` と `output/<名前>-reviewed/`（変更点の `report.md`、`before-*.png` / `after-*.png`）。`input/` の元ファイルは変更しない。
- 画像化は PowerPoint の COM 操作（Windows）を優先し、使えなければ LibreOffice（`soffice`）を使う。どちらも無ければ導入方法を案内して止める。
- 資料専用の検出基準 `anti-patterns.md` と参考資料一覧 `references.md`（実在の公開資料・資料作成ガイドのうち、確認できたもの）を新設する。
- 採用した方針を `docs/slide-principles.md` に1行ルールとして溜め、次回のレビューに引き継ぐ（Web 用の `docs/design-principles.md` とは分ける）。
- `input/` と `output/` を作る。中身は `.gitignore` で除外し、`.gitkeep` でフォルダだけ管理する。
- README（日本語・英語）に `/pptx-review` の使い方と必要なもの（Python 3、python-pptx、PowerPoint または LibreOffice）を追記する。
- 既存の `/ui-review` と `ui-reviewer` は変更しない。

## Capabilities

### New Capabilities
- `pptx-review`: `input/` の .pptx からAIっぽさを検出し、すべての指摘に推奨の修正を自動で適用して（デザインと本文）、検証済みの修正版とレポートを `output/` に出力する。

### Modified Capabilities
<!-- なし。既存の spec は存在せず、/ui-review の振る舞いも変えない -->

## Impact

- 追加: `.claude/skills/pptx-review/`（`SKILL.md`、`anti-patterns.md`、`references.md`、`templates/slide-principles.md`、`scripts/` の抽出・画像化スクリプト）、`.claude/agents/pptx-reviewer.md`、`input/.gitkeep`、`output/.gitkeep`
- 変更: `.gitignore`、`README.md`、`README.en.md`
- 実行時に作られるもの: `docs/slide-principles.md`（初回）、`.pptx-review-tmp/`（作業用、ignore）
- 依存: Python 3 と python-pptx（必須）。画像化に PowerPoint（Windows、COM 操作）または LibreOffice（必須、どちらか一方）
- 既存機能への影響: なし（`/ui-review` は変更しない）
