---
name: ui-review
description: 指定した画面のフロントエンドから「AIが作ったっぽさ」（角丸カードの多用、飾りアイコン・絵文字、グラデーション・影、均一な余白と中央寄せ）を見つけ、実在アプリを参考にした修正方針を選択式で相談し、変更計画（OpenSpec の change など）として起票する。/ui-review <画面名> または /ui-review --verify <change名> で明示的に呼ばれたときだけ使う。
argument-hint: <画面名> | --verify <change名>
disable-model-invocation: true
---

# /ui-review

引数: `$ARGUMENTS`

分析は `ui-reviewer` サブエージェントに任せ、ユーザーとの相談・ファイル作成はこのメインの会話で行う。サブエージェントはユーザーに質問できないため、**選択肢の提示は必ずここで AskUserQuestion を使う**。

このスキルが使うファイル（すべて `.claude/skills/ui-review/` 配下）:

- `project.md` … このリポジトリの設定（画面一覧・URL・スタイリング・データの準備・起票先）。初回に作る
- `anti-patterns.md` … 検出基準
- `references.md` … 厳選した参考アプリ
- `templates/` … `project.md` と `docs/design-principles.md` のひな形

## 0. 準備（毎回）

1. 引数を解釈する。
   - `--verify <change名>` → 「検証フロー」へ。
   - それ以外 → 引数を画面名として「レビューフロー」へ。
2. `project.md` が無い、または `<!-- status: unconfigured -->` が残っていれば、先に「プロジェクト設定」を行う。
3. 画面名から `project.md` の画面一覧で URL を決める。
   - 一覧に無い名前なら、ルーティング定義を読み直して近い画面を探す。決められなければ一覧の画面を AskUserQuestion で選ばせる（4択まで。残りは「その他」で受ける）。
   - 引数が空なら、同じように画面一覧から選ばせる。
   - 「アプリ全体」のような画面名でない指定のときも、1回のレビューは1画面だけなので、選ばせる。
4. dev サーバーが起動しているか、`project.md` の「起動確認」で確かめる。
   - 起動していなければ、起動コマンドを Bash の `run_in_background` で起動し、出力に URL が出るまで待つ。ポートが変わった場合は出力の URL を使う。
   - 自分で起動したサーバーは、フローの最後に止める。
5. Playwright MCP（`mcp__playwright__*`）が使えるか確認する。使えなければ、`.mcp.json` に `playwright` サーバーを追加して Claude Code を再起動するよう伝えて止める（README の導入手順を案内する）。
6. `references.md` に参考アプリが1件も無ければ「参考リスト初期化」を先に行う。
7. `docs/design-principles.md` が無ければ、`templates/design-principles.md` をコピーして作る。
8. `.ui-review-tmp/` に前回の残りがあれば削除しておく。

## プロジェクト設定（初回のみ）

1. `templates/project.md` を `project.md` にコピーする。
2. リポジトリを調べて各欄を埋める。
   - `package.json`（scripts、依存関係）、README、ルーティング定義、スタイルの設定（Tailwind 設定・グローバル CSS・テーマファイル・UI ライブラリ）、アイコンの import、ビルドツールの設定（`base` やポート）。
   - `openspec/` があれば OpenSpec を使う。CLI があれば `openspec --version` を記録し、spec 差分が必須かを確かめる（既存の change が `specs/` を持っているか、`.openspec.yaml` に `skip_specs` があるかを見る）。
   - 撮影用のブラウザで空状態しか撮れない画面があるかを調べ、データの準備方法（開発用のシード、テストアカウント、ブラウザで実行するスクリプトなど）を探す。見つからなければ「なし」とし、必要なら後でユーザーが足せるように書いておく。スクリプトを新しく作る場合は `.claude/skills/ui-review/fixtures/` に置き、利用者の本番データに触れないもの（撮影用ブラウザの中だけで完結するもの）に限る。
   - 主な画面幅（スマホ中心か、デスクトップ中心か）を、レイアウトの `max-width` やビューポート設定、README から判断してビューポート表を調整する。
3. 埋めた内容の要点（画面一覧、dev サーバー、ビューポート、データの準備、起票先）を短く示し、AskUserQuestion で「この設定で進める（推奨）／直したい点がある」を聞く。直したい点があれば反映する。
4. `<!-- status: unconfigured -->` を `<!-- status: configured -->` に書き換える。

## 参考リスト初期化（初回のみ）

1. `ui-reviewer` を `mode: seed-references` で呼ぶ。
2. 返ってきた候補を AskUserQuestion（`multiSelect: true`、1問4択まで。候補が5件以上なら複数問に分ける）で提示し、気に入ったものを選ばせる。各選択肢の description に「参考になる点」を入れる。
3. 選ばれたものだけを references.md の書式で追記する（追加日は今日の日付）。1件も選ばれなければ、references.md は空のまま、レビューでは Web 検索の参考だけを使う。

## レビューフロー

1. `ui-reviewer` を `mode: review`、`screen: <画面名> (<URL>)` で呼ぶ。
2. 返ってきた指摘（最大5件）を、1指摘＝1問として AskUserQuestion で提示する（4問を超えたら2回に分ける）。
   - `header`: 指摘の短縮名（12文字以内）
   - `question`: 「<見えている問題>。どう直しますか？」＋該当箇所を1文
   - `options`: 案A（推奨、ラベル末尾に「（推奨）」）、案B、案C、最後に「そのままにする」。description に参考アプリと影響範囲を1行で。`preview` に案のプレビューを入れる。
   - 共通の部品・クラス・デザイントークンに波及する案は、description の先頭に「【他画面にも影響】」と付ける。
3. 「その他」で自由記述された回答は、意図を自分の言葉で言い直して確認する。曖昧なら追加で1問だけ聞く。
4. 「その他の気になる点」がある場合、最後に「次回のレビューに回す／今回もう一度詳しく見る」を1問で聞く。「もう一度詳しく見る」なら、その点に絞って `ui-reviewer` を再度呼び、同じ形で相談する（合計で5件を超えないようにする）。
5. 採用された指摘が0件なら、`.ui-review-tmp/` を空にして終了する。
6. 1件以上あれば「起票」へ。

## 起票（1回のレビュー＝1 change）

change 名は `project.md` の画面一覧の change 名（無ければ `ui-refine-<画面名のkebab-case>`）。同名が既にあれば末尾に `-2`, `-3` を付ける。起票先は `project.md` の「変更の起票先」に従う。

### OpenSpec を使う場合

1. 既存の change（`openspec/changes/` と `openspec/changes/archive/`）を1つ読み、書式と文体を合わせる。
2. `openspec new change <change名>` で作る。
3. 下の「書く内容」を作成する。spec 差分が必須のプロジェクトでは、`specs/<capability>/spec.md` に見た目の要件を `## ADDED Requirements` で足す（各要件に `#### Scenario:` を1つ以上）。既存要件と名前が重ならないようにし、既存要件の書き換えが必要なら `## MODIFIED Requirements` に既存の要件全文をコピーしてから直す。
4. `openspec validate <change名> --strict` を実行し、通るまで直す。

### OpenSpec を使わない場合

1. `docs/ui-reviews/<change名>/` を作り、下の「書く内容」の proposal.md / tasks.md / screenshots/ を置く（spec 差分は作らない）。

### 書く内容

**`proposal.md`**

```markdown
# Proposal

## Why

<検出されたAIっぽさと、それが利用者にとって何の問題か（読む順番が分からない、押せる所が分からない等）>

## What Changes

- <採用した案ごとに1項目。参考アプリ名と、何を参考にしたかを明記>
- データや操作（保存される値、画面遷移）は変えない。

## Impact

- <変えるファイル・クラス・トークン・コンポーネント>
- 影響する他画面: <共通部品・トークンを変える場合に列挙。無ければ「なし（この画面だけ）」>
- テスト: <見た目の変更で期待値が変わりそうなテストがあれば挙げる>
- 検証: `/ui-review --verify <change名>` の Before/After スクショと実機で確認する。
- 参考スクショ: `screenshots/before-*.png`
```

OpenSpec の書式に `## Capabilities` などの節があれば、それも合わせて書く。

**`tasks.md`**

```markdown
# Tasks

## 1. <採用した案1>

- [ ] 1.1 <具体的な変更。対象のファイルとクラス名・コンポーネント名まで書く>。開発者ツールで <ビューポート> にして <確認すること> を確認する

## 2. <採用した案2>

...

## N. 確認

- [ ] N.1 <lint・テストのコマンド> が通ることを確認する
- [ ] N.2 （ユーザーが実行）`/ui-review --verify <change名>` で Before/After を確認する。実装担当はこのタスクにチェックを付けない
```

**`screenshots/`**: `.ui-review-tmp/` の `before-*.png` をここへ移動する（`mkdir -p` してから `mv`）。

- `design.md` は、共通部品やデザイントークンを変えて他画面に影響する場合だけ作り、影響する画面ごとの見た目の変化と、採らなかった案とその理由を書く。

### 起票の後

1. `docs/design-principles.md` の該当する節に、採用した案の「方針ルール」を `- <ルール>（<change名>）` の形で追記する。既存ルールと重複・矛盾する場合は追記せず、AskUserQuestion で「既存ルールを更新する／今回は例外とする」を聞く。例外にするなら「例外」の節に書く。
2. `.ui-review-tmp/` を空にする（ディレクトリごと削除してよい）。自分で起動した dev サーバーがあれば止める。
3. 最後に、change のパスと「実装後に `/ui-review --verify <change名>` を実行する」ことだけを短く伝える。実装はしない。

## 検証フロー（--verify）

1. change のディレクトリ（`openspec/changes/<change名>/` または `docs/ui-reviews/<change名>/`）が存在し、`screenshots/before-*.png` があることを確認する。無ければ理由を伝えて止める。
2. change 名と proposal.md から対象画面を特定し、`project.md` の画面一覧で URL を決める。準備の4・5・8を行う。
3. `ui-reviewer` を `mode: verify`、`screen: <画面名> (<URL>)`、`change: <change のディレクトリ>` で呼ぶ。
4. after 画像を `.ui-review-tmp/` から change の `screenshots/` へ移動し（同名があれば上書き）、`.ui-review-tmp/` を空にする。
5. 結果を伝える:
   - すべてOKで新たな問題も副作用もなければ、tasks.md の検証タスクにチェックを付け、完了を伝える（アーカイブは通常のフローで行う）。
   - 要修正・新たなAIっぽさ・副作用があれば、1件＝1問で AskUserQuestion にかけ（「このchangeで直す（推奨）」「次のレビューに回す」「問題ない」）、「このchangeで直す」を選んだものを、具体的な変更と確認方法を書いたタスクとして tasks.md の検証タスクの直前に追記する。仕様に関わるもの（並び順など）は spec 差分と proposal にも反映し、OpenSpec なら `validate --strict` を通す。検証タスクはチェックしないまま残す。
   - 「次のレビューに回す」ものと、サブエージェントが挙げた次回レビュー候補は、最後にまとめて伝える。
6. 自分で起動した dev サーバーがあれば止める。

## やらないこと

- このスキルの中でアプリのコードを編集しない。実装は通常のフロー（OpenSpec なら apply）で行う。
- 指定されていない画面をレビューしない（共通部品の影響確認のための撮影は除く）。
- 指摘を5件より多く相談しない。
