# de-ai-ui

[English](README.en.md)

**生成AIで作ったフロントエンドの「AIっぽさ」を見つけて、実在アプリを参考に直すための Claude Code 用エージェントとスキル。**

角丸カードだらけ、どこにでも付いたアイコンや絵文字、紫〜青のグラデーション、どこも同じ余白で中央寄せ。生成AIに画面を作らせると、こうした画一的な見た目になりがちです。

`/ui-review <画面名>` を実行すると、次の流れで進みます。

1. 画面のコードと実際の画面（Playwright のスクショと計測値）を突き合わせて、見つかった問題を件数の上限なく、重要度順にすべて指摘する
2. 指摘ごとに、実在アプリの手法を参考にした修正案を2〜3個、選択式で相談する（推奨案・プレビュー・影響範囲付き。「そのままにする」も選べる）
3. 採用した案を変更計画として起票する（OpenSpec の change、または `docs/ui-reviews/` の proposal / tasks）
4. 採用した方針を `docs/design-principles.md` に一行ルールとして溜め、次回のレビューと新しい画面づくりに引き継ぐ

実装した後は、`/ui-review --verify <change名>` で Before/After のスクショを比べ、タスクごとに直っているかを判定します。修正で新たに生まれた「AIっぽさ」や副作用（はみ出し、コントラスト、タップ領域など）も確かめます。

判断の基準は「装飾を剥がすこと」ではなく、**情報の重みと操作の流れに合っているか**です。装飾を消しただけで使いにくくなる案は出しません。

## 検出するもの

| カテゴリ             | 例                                                                 |
| -------------------- | ------------------------------------------------------------------ |
| 角丸カードの多用     | 性質の違う情報がすべて同じ角丸の箱に入っている、カードの入れ子     |
| 飾りアイコン・絵文字 | 文字と同じ意味を繰り返すだけのアイコン、ナビゲーションの絵文字     |
| グラデ・影・意味のない色 | 紫〜青のグラデーション、全部に付いた影、意味を持つ色の飾りへの流用 |
| 均一な余白と中央寄せ | どこも同じ余白、数値の中央寄せ、結論がスクロールしないと見えない   |
| 方針違反             | `docs/design-principles.md` に溜めたルールに反している箇所         |

基準の詳細は [anti-patterns.md](.claude/skills/ui-review/anti-patterns.md) にあります。

## 必要なもの

- [Claude Code](https://claude.com/claude-code)
- Node.js（Playwright MCP を `npx` で起動するため）
- 起動できる dev サーバーを持つ Web フロントエンド（React / Vue / Svelte など。スタイリングは CSS・Tailwind・CSS Modules・UI ライブラリのどれでもよい）
- 任意: [OpenSpec](https://github.com/Fission-AI/OpenSpec)。使っていれば change として起票し、使っていなければ `docs/ui-reviews/` に書き出します

## 導入

アプリのリポジトリ直下で実行します。

```sh
git clone --depth 1 https://github.com/Ceros9651/de-ai-ui.git /tmp/de-ai-ui
mkdir -p .claude
cp -r /tmp/de-ai-ui/.claude/. ./.claude/
```

1. `.mcp.json` に `playwright` サーバーを追加します（既に `.mcp.json` があれば `mcpServers` に `playwright` の項目だけ足します）。

   ```json
   {
     "mcpServers": {
       "playwright": {
         "command": "npx",
         "args": ["@playwright/mcp@latest", "--isolated", "--output-dir", ".ui-review-tmp"]
       }
     }
   }
   ```

2. `.gitignore` に撮影の一時フォルダを追加します。

   ```
   .ui-review-tmp/
   ```

3. 新しい画面を作るときにも方針を守らせたい場合は、`CLAUDE.md` に追記します。

   ```markdown
   ## UIデザイン

   フロントエンドの画面やコンポーネントを作成・変更するときは、必ず `docs/design-principles.md` を読んで従うこと。
   角丸カードの多用、飾りアイコンや絵文字、グラデーションや強い影、均一な余白と中央寄せは避ける（詳細は `.claude/skills/ui-review/anti-patterns.md`）。
   ```

4. Claude Code を再起動し、`playwright` MCP サーバーの利用を許可します。初回はブラウザのダウンロードが走ることがあります。

## 使い方

```text
/ui-review ホーム                      画面をレビュー → 選択式で相談 → 変更計画を起票
/ui-review --verify ui-refine-home     実装後に Before/After のスクショで検証
```

初回だけ、次の2つが先に走ります。

- **プロジェクト設定**: リポジトリを調べて、画面一覧・URL・スタイリング・ビューポート・データの準備方法・起票先を `.claude/skills/ui-review/project.md` にまとめます。内容を確認して進めます。
- **参考アプリの登録**: 同じジャンルの実在アプリの候補が出るので、気に入ったものを選ぶと `references.md` に登録されます。

実装は、起票された変更計画を使っていつものフローで行います（OpenSpec なら `/opsx:apply` など）。レビュー中にエージェントがアプリのコードを編集することはありません。

## 構成

```
.claude/
  agents/ui-reviewer.md              分析担当のサブエージェント（コード読解・スクショ・計測・案作成。編集しない）
  skills/ui-review/
    SKILL.md                         /ui-review の流れ（設定・相談・起票・検証）
    anti-patterns.md                 検出基準（4カテゴリ＋方針違反）
    references.md                    厳選した参考アプリ（初回に候補から選んで登録）
    templates/project.md             プロジェクト設定のひな形（初回に project.md として埋める）
    templates/design-principles.md   デザイン方針ファイルのひな形
.mcp.json                            Playwright MCP の設定例
```

## 設計上の決めごと

- サブエージェントはユーザーに直接質問できないため、分析（`ui-reviewer`）と相談（メインの会話の AskUserQuestion）を分けています。
- 指摘の件数に上限はありません。1回のレビューで全件を相談し、採用したものはすべて1つの change でまとめて直します（次回に先送りしません）。
- 参考にするのは実在するアプリだけです。テンプレート配布サイト、コンセプト作品、AI生成のショーケースは参考にしません。
- 撮影用のブラウザは `--isolated` で起動し、利用者の端末のデータには触れません。空状態しか撮れない画面は、`project.md` の「データの準備」に撮影用のデータの入れ方を書けます。
- `/ui-review` は明示的に呼んだときだけ動きます（`disable-model-invocation: true`）。

## ライセンス

[MIT](LICENSE)
