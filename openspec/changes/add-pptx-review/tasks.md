## 1. 入出力フォルダ

- [ ] 1.1 `input/.gitkeep` と `output/.gitkeep` を作る
- [ ] 1.2 `.gitignore` に `input/*`・`output/*`（`!input/.gitkeep`・`!output/.gitkeep` で除外を解除）と `.pptx-review-tmp/` を足す。`input/` にダミーの .pptx を置いて `git status` に出てこないことを確かめる

## 2. 同梱スクリプト

- [ ] 2.1 `.claude/skills/pptx-review/scripts/extract.py` を作る。スライドごとの図形（スライド番号・shape id・種類・位置/サイズ・塗り〔単色/グラデ/画像〕・線・効果・`prstGeom` と角丸の調整値・テキストの段落と書式・揃え・絵文字の有無）、レイアウト名、マスターとテーマ（配色・フォント・背景）を JSON に書き出す
- [ ] 2.2 `.claude/skills/pptx-review/scripts/render.py` を作る。PowerPoint の COM 操作（pywin32 か PowerShell 経由、`DisplayAlerts` を切り、終了時に必ず `Quit()`）でスライドを `<prefix>-<番号>.png` に書き出し、使えなければ `soffice --headless` で PDF にしてから PNG にする。使った手段を標準出力に出し、どちらも無ければ導入方法を出して終了コード1で終わる
- [ ] 2.3 検証用のサンプル .pptx（角丸＋影のカード、紫青グラデ背景のマスター、絵文字付き見出し、全部中央寄せ、AI文体の本文を含む）を python-pptx で作るスクリプトを `scripts/make_sample.py` として置き、2.1・2.2 をそれに対して実行して、JSON に各要素が出ることと PNG が枚数分できることを確かめる

## 3. 検出基準・参考・方針テンプレート

- [ ] 3.1 `.claude/skills/pptx-review/anti-patterns.md` を作る。`/ui-review` の4カテゴリを DrawingML の要素名で書き直し、資料特有の項目（アイコン＋見出しカードの横並び、全スライド箇条書き、AI文体の言い回し、全テキスト中央寄せ・同じレイアウトの繰り返し）と、それぞれの「置き換えの方向」を書く
- [ ] 3.2 `.claude/skills/pptx-review/references.md` を作る。書式（名前／URL／何が参考になるか／追加日）と、確認できた実在の公開資料・資料作成ガイドだけを載せるという決まりを書く（初期値は空でよい。初回に seed する）
- [ ] 3.3 `.claude/skills/pptx-review/templates/slide-principles.md` を作る（配色・図形・アイコン・レイアウト・文章・例外の節を持つ空のひな形）

## 4. サブエージェント pptx-reviewer

- [ ] 4.1 `.claude/agents/pptx-reviewer.md` を作る。ツールは Read / Grep / Glob / Bash / WebSearch / WebFetch（Write・Edit は与えない）。絶対ルール（ファイルを編集しない、ユーザーに質問しない、指摘は抽出 JSON と画像の両方を根拠にする、`docs/slide-principles.md` と矛盾する案を出さない、資料の本文を Web 検索に含めない、装飾を剥がしただけで読みにくくなる案は出さない）を書く
- [ ] 4.2 `mode: seed-references`（参考資料の候補を6〜8件、確認できたものだけ返す）を書く
- [ ] 4.3 `mode: review` を書く。抽出 JSON で候補を絞ってから該当スライドの画像を見ること、パターン単位で最大5件、各指摘に「見えている問題／該当スライド番号と shape id／原因（スライドか、マスター/テーマか）／案A（推奨）・案B…（参考資料と影響範囲）」を含める返却形式
- [ ] 4.4 `mode: verify` を書く。Before/After の画像と抽出 JSON を比べ、案ごとの反映（OK／要修正）、副作用（はみ出し・重なり・コントラスト）、新たなAIっぽさを返す形式

## 5. スキル /pptx-review

- [ ] 5.1 `.claude/skills/pptx-review/SKILL.md` の準備の節を書く。`disable-model-invocation: true`、`argument-hint: [ファイル名]`、対象ファイルの決定（引数／`input/` から AskUserQuestion で選ぶ／無ければ案内して終了）、python-pptx と画像化の手段の確認、`.pptx-review-tmp/` の掃除、`docs/slide-principles.md` が無ければテンプレートからコピー、`references.md` が空なら seed
- [ ] 5.2 レビューの節を書く。元ファイルを `.pptx-review-tmp/` にコピー → extract・render（before）→ `pptx-reviewer` を review で呼ぶ → 1指摘＝1問で AskUserQuestion（推奨案を先頭に「（推奨）」、マスター変更案の description の先頭に「【全スライドに影響】」、最後に「そのままにする」、文言の案は preview に Before/After の文）→ 採用0件なら掃除して終了
- [ ] 5.3 適用の節を書く。メインが `.pptx-review-tmp/` に python-pptx のスクリプトを書いて作業用コピーに適用する手順と、よく使う XML 操作の早見表（`a:gradFill`→`a:solidFill`、`a:effectLst` の削除、`roundRect`→`rect` と `a:avLst`、マスターの `p:bg`、テキストの run 単位の置き換えで書式を保つ方法）。発表者ノート・画像・数字・固有名詞は変えないこと。書き換え後に python-pptx で開き直せるか確かめること
- [ ] 5.4 検証の節を書く。render（after）→ `pptx-reviewer` を verify で呼ぶ → 問題は1件＝1問で「直してから出力する（推奨）／このまま出力する」→ 再検証は2回まで、残りは「未解決」として記録
- [ ] 5.5 出力の節を書く。同名の出力があれば上書きを確認、`output/<名前>-reviewed.pptx` と `output/<名前>-reviewed/`（report.md と変更スライドの before/after 画像）を書き出す、report.md の書式（対象ファイル、画像化の手段、指摘と採用した案、変更したスライドと図形、検証結果、未解決）、`docs/slide-principles.md` への追記（重複・矛盾時は AskUserQuestion）、`.pptx-review-tmp/` の削除
- [ ] 5.6 「やらないこと」の節を書く（`input/` の元ファイルを変更しない、ノート・アニメーションに触れない、指摘を5件より多く相談しない、複数ファイルを一度に扱わない）

## 6. ドキュメント

- [ ] 6.1 `README.md` に `/pptx-review` の節（流れ、`input/` と `output/` の使い方、必要なもの: Python 3・python-pptx・PowerPoint または LibreOffice、導入手順）を足す
- [ ] 6.2 `README.en.md` に同じ内容を英語で足す

## 7. 確認

- [ ] 7.1 2.3 のサンプルを `input/` に置いて `/pptx-review` を最後まで通し、`output/<名前>-reviewed.pptx` が PowerPoint で修復ダイアログなしに開け、角丸・影・グラデ・絵文字・揃え・本文のいずれかが直っていること（受入条件: デザインに修正が入っている）、`input/` の元ファイルが変わっていないこと、report.md と before/after 画像ができていること、`docs/slide-principles.md` に方針が追記されたことを確かめる
- [ ] 7.2 引数なし（候補が複数）、存在しないファイル名、すべて「そのままにする」、既存の出力がある場合の4通りで、spec のシナリオどおりに動くことを確かめる
- [ ] 7.3 `openspec validate add-pptx-review --strict` が通ることを確かめる
- [ ] 7.4 （ユーザーが実行）普段使いの実際の資料で `/pptx-review` を試し、結果を確認する。実装担当はこのタスクにチェックを付けない
