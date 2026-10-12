# /ui-review のプロジェクト設定

<!-- status: unconfigured -->

このファイルは `/ui-review` を初めて実行したときに、リポジトリを調べて自動で埋められる。
手で直してもよい。`status` が `unconfigured` のあいだは、/ui-review は最初にこのファイルの設定を行う。

## アプリの概要

- 何のアプリか: <例: 自分ひとり用の家計簿 PWA>
- 主な利用者と使い方: <例: スマホのホーム画面から毎日開いて、出費を記録し月の集計を見る>
- 主な対象の画面幅: <スマホ中心 / デスクトップ中心 / 両方>

## 技術スタック

- フレームワーク: <例: React 19 + Vite>
- ルーター: <例: react-router-dom（HashRouter）。定義は src/App.tsx>
- スタイリング: <例: 素の CSS（src/index.css の1ファイル、CSS 変数＋クラス名） / Tailwind / CSS Modules / UI ライブラリ名>
- デザイントークンの場所: <例: src/index.css の :root / tailwind.config.ts の theme>
- アイコン: <例: なし（絵文字） / lucide-react / heroicons>
- ダークモード: <例: prefers-color-scheme で切り替え / class="dark" / なし>

## dev サーバー

- 起動コマンド: <例: npm run dev>
- ベースURL: <例: http://localhost:5173/>
- 起動確認: <例: curl -s -o /dev/null -w "%{http_code}" http://localhost:5173/ が 200>
- ハッシュルーター: <はい / いいえ>（はいの場合、同じURLへの移動では再読み込みにならないので、`?reload=1#/...` のようにクエリを付けたURLを経由して再読み込みする）

## ビューポート

撮影するビューポート。1つ目を主とする。

| 名前      | 幅×高さ  | 用途                     |
| --------- | -------- | ------------------------ |
| mobile    | 390×844  | 主                       |
| mobile-sm | 360×740  | はみ出し確認             |
| desktop   | 1440×900 | デスクトップ向けの画面のみ |

## 画面一覧

| 画面名（引数で受け付ける名前） | URL | 主なファイル | spec の capability（OpenSpec を使う場合） | change 名 |
| ------------------------------ | --- | ------------ | ----------------------------------------- | --------- |
| <ホーム / home>                | <http://localhost:5173/> | <src/pages/HomePage.tsx> | <monthly-summary> | ui-refine-home |

- 動的なパラメータが要る画面は、下の「データの準備」で入る固定の ID を使う。

## データの準備

撮影用のブラウザ（Playwright）は利用者の端末とは別で、データが空のことが多い。空のままでは空状態しか撮れない画面がある場合、撮影前にデータを用意する方法をここに書く。

- 方法: <なし / 開発用のシード（例: npm run db:seed） / ログイン用のテストアカウント / ブラウザで実行するスクリプト（例: .claude/skills/ui-review/fixtures/seed.js を browser_evaluate で実行）>
- 手順: <具体的な手順>
- 注意: 利用者の本番データには触れない方法に限る。

## 変更の起票先

- OpenSpec: <使う / 使わない>
  - 使う場合: <CLI のバージョン、spec 差分が必須か（`openspec validate --strict` が「delta が無い」で落ちるか）、既存 change の書式の参考にするパス>
  - 使わない場合: `docs/ui-reviews/ui-refine-<画面>/` に proposal.md / tasks.md / screenshots/ を書き出す。
- テスト・lint のコマンド: <例: npm run lint / npm test>
