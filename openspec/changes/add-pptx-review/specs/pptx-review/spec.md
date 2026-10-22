## ADDED Requirements

### Requirement: 対象ファイルの選択
`/pptx-review` は1回の実行で `input/` 内の .pptx を1ファイルだけ扱わなければならない（SHALL）。引数でファイル名を渡せば、それを対象にする。引数を省略した場合は `input/` 内の .pptx を AskUserQuestion で選ばせる。

#### Scenario: 引数でファイルを指定する
- **WHEN** ユーザーが `/pptx-review deck.pptx` を実行し、`input/deck.pptx` が存在する
- **THEN** `input/deck.pptx` をレビュー対象にする

#### Scenario: 引数を省略し、候補が複数ある
- **WHEN** ユーザーが引数なしで `/pptx-review` を実行し、`input/` に .pptx が2つ以上ある
- **THEN** AskUserQuestion でファイルを選ばせ、選ばれた1ファイルだけを対象にする

#### Scenario: 対象ファイルが無い
- **WHEN** 指定したファイルが `input/` に無い、または `input/` に .pptx が1つも無い
- **THEN** `input/` に .pptx を置くよう伝えて、何も出力せずに終了する

### Requirement: 実行環境の確認
レビューを始める前に、Python 3 と python-pptx が使えることと、画像化の手段（PowerPoint の COM 操作または LibreOffice）がどちらか1つ使えることを確かめなければならない（SHALL）。画像化は PowerPoint の COM 操作を優先し、使えなければ LibreOffice を使う。

#### Scenario: PowerPoint が使える
- **WHEN** Windows で PowerPoint の COM 操作が使える
- **THEN** PowerPoint を使ってスライドを画像化する

#### Scenario: PowerPoint が無く LibreOffice がある
- **WHEN** PowerPoint の COM 操作が使えず、`soffice` が見つかる
- **THEN** LibreOffice を使ってスライドを画像化する

#### Scenario: 必要なものが足りない
- **WHEN** python-pptx が無い、または画像化の手段がどちらも無い
- **THEN** 足りないものと導入方法を伝えて、レビューを始めずに終了する

### Requirement: AIっぽさの検出
`pptx-reviewer` サブエージェントは、スライドの構造（図形の塗り・線・効果・角丸・位置・テキスト、スライドマスターとテーマ）とスライド画像の両方を根拠にAIっぽさを検出しなければならない（SHALL）。検出基準は資料専用の `anti-patterns.md` に従う。対象のカテゴリは、配色・グラデーション・影・角丸、絵文字・飾りアイコン、レイアウト・余白・整列、スライド本文の文章表現、`docs/slide-principles.md` への方針違反とする。指摘は同じ種類の問題をまとめたパターン単位で、重要度順に最大5件とし、各指摘に該当スライド番号と、マスター/テーマが原因かどうかを含める。サブエージェントはファイルを編集せず、ユーザーに質問もしない。

#### Scenario: 同じ問題が複数スライドにある
- **WHEN** 角丸＋影のカードが5枚のスライドに出ている
- **THEN** 該当スライド番号をすべて含めた1件の指摘として返す

#### Scenario: 根拠が片方しかない
- **WHEN** 画像では問題に見えるが、対応する図形やXMLを特定できない
- **THEN** その指摘は出さない

#### Scenario: 原因がマスターにある
- **WHEN** 全スライドの紫青グラデーション背景がスライドマスターで定義されている
- **THEN** 指摘に「原因: マスター/テーマ」と、影響するスライドの範囲を含める

### Requirement: 修正方針の相談
メインの会話は、指摘1件＝1問として AskUserQuestion で修正案を相談しなければならない（SHALL）。各問の選択肢は推奨案（ラベル末尾に「（推奨）」）、他の案、最後に「そのままにする」とし、マスター/テーマを変更する案の description の先頭に「【全スライドに影響】」と付ける。修正案の根拠には、`references.md` または確認できた実在の公開資料・資料作成ガイドだけを挙げる。

#### Scenario: マスターを変える案がある
- **WHEN** 修正案がスライドマスターの背景を単色に変えるものである
- **THEN** その選択肢の description が「【全スライドに影響】」で始まる

#### Scenario: すべて「そのままにする」が選ばれた
- **WHEN** 採用された指摘が0件である
- **THEN** pptx を出力せず、作業用ディレクトリを消して終了する

### Requirement: 修正の適用
採用した案は、python-pptx（API で扱えない塗り・効果・角丸などは XML の直接操作）で、指摘の該当スライドすべてにまとめて適用しなければならない（SHALL）。原因がマスター/テーマにあり、その案が採用された場合は、マスター/テーマを変更する。修正は `input/` の元ファイルのコピーに対して行い、元ファイルは変更しない。発表者ノートの文字は変更しない。

#### Scenario: 元ファイルを保護する
- **WHEN** 修正を適用して出力する
- **THEN** `input/<名前>.pptx` の内容と更新日時は実行前と変わらない

#### Scenario: 文章表現を直す
- **WHEN** 「革新的なソリューションでシームレスな体験を実現」という本文の言い換えが採用された
- **THEN** スライド上の該当テキストだけを書き換え、フォント・サイズ・色などの書式と発表者ノートは変えない

### Requirement: 適用後の検証
適用後は修正版を画像化し、`pptx-reviewer` で Before/After を比べなければならない（SHALL）。確認する内容は、採用した各案が反映されているか、文字のはみ出し・図形の重なり・コントラスト不足といった副作用、修正で新たに生まれたAIっぽさとする。問題が見つかった場合は、1件＝1問で「直してから出力する（推奨）／このまま出力する」を相談し、直す場合は再度適用・検証してから出力を確定する。直してからの再検証は2回までとし、それでも残る問題は `report.md` に「未解決」として書いて出力する。

#### Scenario: 修正で文字がはみ出した
- **WHEN** 角丸カードを外して余白を詰めた結果、テキストが枠からはみ出している
- **THEN** その問題を相談にかけ、「直してから出力する」が選ばれたら直して再検証する

#### Scenario: 問題が無い
- **WHEN** すべての案が反映され、副作用も新たなAIっぽさも無い
- **THEN** 確認を挟まずに出力へ進む

### Requirement: 出力物
出力は `output/<名前>-reviewed.pptx` と `output/<名前>-reviewed/` ディレクトリとしなければならない（SHALL）。ディレクトリには、指摘・採用した案・変更したスライドと図形・検証結果をまとめた `report.md` と、変更したスライドの `before-<スライド番号>.png` / `after-<スライド番号>.png` を置く。同名の出力が既にある場合は、上書きする前に AskUserQuestion で確認する。作業用の `.pptx-review-tmp/` は終了時に消す。

#### Scenario: 初回の出力
- **WHEN** `input/deck.pptx` のレビューで1件以上の案を適用し、検証が終わった
- **THEN** `output/deck-reviewed.pptx`、`output/deck-reviewed/report.md`、Before/After 画像ができている

#### Scenario: 既に出力がある
- **WHEN** `output/deck-reviewed.pptx` が既に存在する
- **THEN** 上書きしてよいかを確認し、拒否されたら書き出さずに終了する

### Requirement: 方針の蓄積
出力の後、採用した案の方針を `docs/slide-principles.md` に `- <ルール>（<ファイル名> <日付>）` の形で追記しなければならない（SHALL）。ファイルが無ければテンプレートから作る。既存ルールと重複・矛盾する場合は追記せず、「既存ルールを更新する／今回は例外とする」を AskUserQuestion で聞く。`pptx-reviewer` は次回以降、このファイルの方針と矛盾する案を出さない。

#### Scenario: 初回のレビュー
- **WHEN** `docs/slide-principles.md` が無い状態で案が採用された
- **THEN** テンプレートからファイルを作り、採用した方針を追記する

#### Scenario: 既存ルールと矛盾する
- **WHEN** 「タイトルは左寄せ」というルールがある状態で、中央寄せの案が採用された
- **THEN** 追記せず、既存ルールを更新するか今回は例外とするかを聞く

### Requirement: 入出力フォルダの管理
リポジトリには `input/` と `output/` を置き、中身の資料は git で管理しないようにしなければならない（SHALL）。

#### Scenario: 資料をコミットしようとする
- **WHEN** `input/` に .pptx を置き、`git status` を実行する
- **THEN** その .pptx は追跡対象に出てこず、`input/.gitkeep` と `output/.gitkeep` だけが管理されている
