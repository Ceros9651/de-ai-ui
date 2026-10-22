---
name: pptx-review
description: input/ に置いた PowerPoint 資料（.pptx）から「AIが作ったっぽさ」（角丸カードとアイコンの並び、絵文字、紫青グラデと影、全部中央寄せ、「革新的」「シームレス」のようなAI文体）を見つけ、修正方針を選択式で相談し、採用した修正をデザインと本文に適用して output/ に書き出す。/pptx-review [ファイル名] で明示的に呼ばれたときだけ使う。
argument-hint: [ファイル名]
disable-model-invocation: true
---

# /pptx-review

引数: `$ARGUMENTS`

分析は `pptx-reviewer` サブエージェントに任せ、ユーザーとの相談と pptx の書き換えはこのメインの会話で行う。サブエージェントはユーザーに質問できないため、**選択肢の提示は必ずここで AskUserQuestion を使う**。

このスキルが使うファイル（すべて `.claude/skills/pptx-review/` 配下）:

- `anti-patterns.md` … 検出基準
- `references.md` … 厳選した参考資料
- `templates/slide-principles.md` … `docs/slide-principles.md` のひな形
- `scripts/extract.py` … pptx の構造を JSON に書き出す
- `scripts/render.py` … スライドを PNG にする（PowerPoint → LibreOffice の順に試す）
- `scripts/make_sample.py` … 動作確認用の「AIっぽい」サンプル資料を作る

作業ディレクトリは `.pptx-review-tmp/`（git では無視される）。以下、`S=.claude/skills/pptx-review/scripts`、`T=.pptx-review-tmp` と書く。パスは日本語や空白を含むことがあるので、必ず引用符で囲む。

## 0. 準備（毎回）

1. 対象ファイルを決める。
   - 引数があれば、`input/<引数>` を探す。拡張子が無ければ `.pptx` を補い、`input/` が付いていれば外して解釈する。
   - 引数が無ければ `input/*.pptx` を一覧する。1つならそれを使い、2つ以上なら AskUserQuestion で選ばせる（4択まで。5つ以上なら更新日時の新しい順に4つ出し、残りは「その他」で受ける）。
   - 見つからない、または `input/` に .pptx が1つも無ければ、「`input/` にレビューしたい .pptx を置いてから、もう一度 `/pptx-review <ファイル名>` を実行してください」と伝えて終了する。
   - `.ppt`（旧形式）や `.potx` は対象外と伝えて終了する。
   - 以下、対象の拡張子を除いた名前を `<名前>` と書く。
2. `python -c "import pptx"` で python-pptx を確かめる。無ければ `pip install python-pptx` を案内して終了する。
3. `.pptx-review-tmp/` に前回の残りがあれば削除し、作り直す。
4. `docs/slide-principles.md` が無ければ、`templates/slide-principles.md` をコピーして作る。
5. 元ファイルのハッシュを記録する（最後に変わっていないことを確かめる）: `python -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" "input/<名前>.pptx"`

## 1. 抽出と画像化

1. 元ファイルを作業用にコピーする: `cp "input/<名前>.pptx" "$T/work-0.pptx"`。以降、**`input/` のファイルには触れない**。
2. `python "$S/extract.py" "$T/work-0.pptx" "$T/before.json"`
3. `python "$S/render.py" "$T/work-0.pptx" "$T" --prefix before`
   - 出力の1行目 `renderer: <手段>` を記録する。
   - 終了コード1（手段が無い）なら、標準エラーの導入方法をそのまま伝えて終了する。
   - PowerPoint で開けずに LibreOffice に切り替わった場合は、その旨（`powerpoint: ...` のエラー）をユーザーに一言伝える。元ファイル自体が PowerPoint で開けない可能性がある。
4. `references.md` に参考資料が1件も無ければ「参考リスト初期化」を先に行う。

## 参考リスト初期化（初回のみ）

1. `pptx-reviewer` を `mode: seed-references`、`file`、`work: .pptx-review-tmp/`、`renderer` で呼ぶ。
2. 返ってきた候補を AskUserQuestion（`multiSelect: true`、1問4択まで。候補が5件以上なら複数問に分ける）で提示し、気に入ったものを選ばせる。各選択肢の description に「参考になる点」を入れる。
3. 選ばれたものだけを references.md の書式で追記する（追加日は今日の日付）。1件も選ばれなければ、references.md は空のまま、レビューでは Web 検索の参考だけを使う。

## 2. レビューと相談

1. `pptx-reviewer` を `mode: review`、`file: input/<名前>.pptx`、`work: .pptx-review-tmp/`、`renderer` で呼ぶ。
2. 返ってきた指摘（最大5件）を、1指摘＝1問として AskUserQuestion で提示する（4問を超えたら2回に分ける）。
   - `header`: 指摘の短縮名（12文字以内）
   - `question`: 「<見えている問題>。どう直しますか？」＋該当スライド番号を1文
   - `options`: 案A（推奨、ラベル末尾に「（推奨）」）、案B、案C、最後に「そのままにする」。description に参考資料と影響範囲を1行で。`preview` に案のプレビューを入れる。文章の書き換え案は、preview に Before → After の文を並べる。
   - マスター/テーマ/レイアウトを変える案は、description の先頭に「【全スライドに影響】」と付ける。
3. 「その他」で自由記述された回答は、意図を自分の言葉で言い直して確認する。曖昧なら追加で1問だけ聞く。
4. 「その他の気になる点」がある場合、最後に「次回のレビューに回す／今回もう一度詳しく見る」を1問で聞く。「もう一度詳しく見る」なら、その点に絞って `pptx-reviewer` を再度呼び、同じ形で相談する（合計で5件を超えないようにする）。
5. 採用された指摘が0件なら、「修正なしのため出力しません」と伝え、`.pptx-review-tmp/` を削除して終了する。

## 3. 適用

採用した案を1件ずつ、`work-<k-1>.pptx` から `work-<k>.pptx` を作る形で適用する（k は 1 から）。1件ごとにファイルを分けるのは、壊れたときにその案だけ取り消せるようにするため。

1. 案ごとに `$T/apply-<k>.py` を書く。サブエージェントの「適用内容」をもとに、python-pptx で `work-<k-1>.pptx` を開き、該当スライド・図形（shape id で特定する）・マスター/レイアウト/テーマを書き換えて `work-<k>.pptx` に保存する。
   - 図形は `slide.shapes` を shape id で探す（グループの中は再帰的に探す）。名前やインデックスで探さない。
   - API で扱えないもの（グラデーション、影、角丸の調整値、背景）は `shape._element` などの lxml 要素を直接書き換える。下の「XML 操作の早見表」に従う。
2. `python "$T/apply-<k>.py"` を実行し、続けて `python -c "from pptx import Presentation;Presentation(r'<work-k.pptx>')"` で開き直せるか確かめる。失敗したら、スクリプトを直して再実行する。2回直しても開けなければ、その案は取り消し（`work-<k>.pptx` を `work-<k-1>.pptx` のコピーにする）、検証で報告する。
3. 全案を適用したら、最後のファイルを `work-final.pptx` としてコピーし、`$T/applied.md` に「案ごとの要約／対象（スライド番号と shape id、マスター等）／やったこと／取り消した案」を書く。

### 守ること

- 変えるのは採用した案の範囲だけ。他の図形・スライドには触れない。
- **発表者ノート**（`notes_slide`）、画像・写真・ロゴ（`p:pic` と `a:blipFill`）、アニメーション（`p:timing`）、画面切り替え（`p:transition`）は変更しない。飾りアイコンを外す案で、アイコンが画像の場合は、その `p:pic` 要素だけを削除してよい。
- 文章の書き換えでは、数字・固有名詞・社内用語を変えない。採用した Before → After 以外の文は変えない。

### XML 操作の早見表

名前空間: `a` = `http://schemas.openxmlformats.org/drawingml/2006/main`、`p` = `http://schemas.openxmlformats.org/presentationml/2006/main`。`from pptx.oxml.ns import qn` で `qn("a:solidFill")` のように書ける。

- **`p:spPr` の子の順番**は `a:xfrm` → 形（`a:prstGeom` / `a:custGeom`）→ 塗り（`a:noFill` / `a:solidFill` / `a:gradFill` / `a:blipFill` / `a:pattFill`）→ `a:ln` → `a:effectLst` → `a:scene3d` → `a:sp3d`。順番を崩すと PowerPoint で開けなくなる。要素を足すときは、既存の要素の位置を見て `insert` する。
- **グラデーション → 単色**: `a:gradFill` を削除し、同じ位置に `<a:solidFill><a:srgbClr val="RRGGBB"/></a:solidFill>` を入れる。API なら `shape.fill.solid(); shape.fill.fore_color.rgb = RGBColor(...)` でもよい（位置は自動で正しくなる）。
- **影・光彩などを消す**: `a:effectLst` の子を全部消して、空の `<a:effectLst/>` を残す。図形に `p:style/a:effectRef idx="1"` 以上があると、`a:effectLst` が無いときにテーマの影がかかるため、**空の `a:effectLst` を置くことで上書きする**。`a:scene3d` / `a:sp3d` は削除する。
- **角丸 → 角**: `a:prstGeom` の `prst="roundRect"` を `prst="rect"` にし、`a:avLst` の子（`a:gd name="adj"`）を消す。角丸を小さくするだけなら `a:gd` の `fmla` を `val 4000` 程度にする（短辺に対する 1/100000 単位）。API なら `shape.adjustments[0] = 0.04`。
- **枠線を消す／細くする**: `a:ln` の中を `<a:noFill/>` にする。細い罫線にするなら `<a:ln w="9525"><a:solidFill><a:srgbClr val="D0D0D0"/></a:solidFill></a:ln>`（`w` は EMU。9525 = 0.75pt）。
- **背景**（スライド・レイアウト・マスター共通）: `p:cSld` の最初の子が `p:bg`。**`p:bg` は1つしか置けない**。既存の `p:bg` を削除してから、`<p:bg><p:bgPr><a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill><a:effectLst/></p:bgPr></p:bg>` を `p:cSld` の先頭に入れる。スライドやレイアウトが自分の `p:bg` を持っていると、マスターを直しても効かない。マスターを直す案では、`before.json` でスライド・レイアウトの `background` が `null` であることを確かめ、`null` でないものは案の範囲に含める。
- **テーマの配色**: マスターからテーマのパートを `master.part.part_related_by(RT.THEME)`（`from pptx.opc.constants import RELATIONSHIP_TYPE as RT`）で取り、`etree.fromstring(part.blob)` で読んで `a:clrScheme` の `a:accent1` などを書き換え、`part._blob = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)` で戻す。
- **揃え**: `paragraph.alignment = PP_ALIGN.LEFT`（`from pptx.enum.text import PP_ALIGN`）。プレースホルダーの揃えがレイアウト/マスターから来ている場合は、段落で上書きするか、案の範囲に応じてレイアウト側を直す。
- **文章の置き換え（書式を保つ）**: 段落の文字が複数の run に分かれているので、`paragraph.text = ...` は使わない（書式が消える）。最初の run の `text` に新しい文を入れ、残りの run の `text` を空にする。run ごとに書式が違う（一部だけ太字など）段落は、太字の部分が新しい文でも対応するように run ごとに書き分ける。
- **絵文字を外す**: run の `text` から絵文字と直後の空白を取り除く（`extract.py` の `EMOJI_RE` を使ってよい）。run が空になったら、その run の `a:r` 要素を削除する。図形の中身が絵文字だけ（丸の中のアイコン）なら、図形ごと削除する案になっているはずなので、`shape._element.getparent().remove(shape._element)` で消す。
- **手打ちの箇条書き記号 → 段落の箇条書き**: run の先頭の「• 」「・」などを外し、`a:pPr` に `<a:buFont typeface="Arial"/><a:buChar char="•"/>` と `marL="285750" indent="-285750"` を付ける。
- **図形や線を新しく足したとき**: python-pptx の `add_shape` / `add_connector` で作った図形には `p:style`（`effectRef idx="2"` など）が付き、テーマの影がかかる。足したら必ず `spPr` の末尾（`a:ln` の後）に空の `<a:effectLst/>` を入れる。
- **位置・大きさ**: `shape.left / top / width / height`（EMU。1pt = 12700、1inch = 914400）。カードを外して詰めるときは、文字がはみ出さないよう、元のテキストボックスの高さを保つか広げる。見出しが折り返して下の本文と重なりやすいので、見出しの幅を広げるか、本文を下げる。
- **左端を揃える**: テキストボックスには内側の余白（既定で左右 0.1inch = 7.2pt）があり、`shape.left` を罫線と同じにしても文字は右にずれる。罫線や他の要素と文字の左端を揃えるときは `text_frame.margin_left = 0` にする。

## 4. 検証

1. `python "$S/extract.py" "$T/work-final.pptx" "$T/after.json"`
2. `python "$S/render.py" "$T/work-final.pptx" "$T" --prefix after`
   - PowerPoint で開けずに失敗した、または LibreOffice に切り替わった（元は PowerPoint で開けていた）なら、修正で pptx が壊れている。`work-<k>.pptx` を1つずつ `render.py --slides 1` で試して原因の案を特定し、その案を取り消してから検証をやり直す。
3. 変更したスライドを求める。`before.json` と `after.json` のマスター/レイアウト（`masters`）が違えば全スライド、そうでなければ `slides[]` を1枚ずつ比べて違うものだけ。
4. `pptx-reviewer` を `mode: verify`、`file`、`work: .pptx-review-tmp/`、`renderer` で呼ぶ。変更したスライド番号も渡す。
5. 結果に応じて:
   - すべて OK で副作用も新たなAIっぽさも無ければ、そのまま「5. 出力」へ。
   - 「要修正」「副作用」「新たなAIっぽさ」があれば、1件＝1問で AskUserQuestion にかける（「直してから出力する（推奨）」「このまま出力する」）。直すものは、追加の `apply-<k>.py` を書いて適用し、手順1から検証をやり直す。
   - 直してからの再検証は**2回まで**。それでも残る問題は、`applied.md` に「未解決」として書き、出力へ進む。
   - 「その他の気になる点」は、最後にまとめて伝える（相談にはかけない）。

## 5. 出力

1. `output/<名前>-reviewed.pptx` か `output/<名前>-reviewed/` が既にあれば、AskUserQuestion で「上書きする／やめる（出力しない）」を聞く。やめるなら `.pptx-review-tmp/` を削除して終了する。
2. 書き出す:
   - `cp "$T/work-final.pptx" "output/<名前>-reviewed.pptx"`
   - `output/<名前>-reviewed/` を作り（上書きのときは中を空にしてから）、変更したスライドの `before-<n>.png` と `after-<n>.png` だけをコピーする。
   - `output/<名前>-reviewed/report.md` を下の書式で書く。
3. 準備の5で記録したハッシュと、`input/<名前>.pptx` の今のハッシュが同じことを確かめる。違っていたら、その旨をユーザーに伝える（このスキルの手順では起きないはずなので、原因を調べる）。
4. `docs/slide-principles.md` の該当する節に、採用した案の「方針ルール」を `- <ルール>（<名前>.pptx <YYYY-MM-DD>）` の形で追記する。既存ルールと重複・矛盾する場合は追記せず、AskUserQuestion で「既存ルールを更新する／今回は例外とする」を聞く。例外にするなら「例外」の節に書く。
5. `.pptx-review-tmp/` を削除する。
6. 最後に、出力したファイルのパス、変更の要約（案ごとに1行）、未解決の問題、次回に回した点だけを短く伝える。

### report.md の書式

```markdown
# <名前>.pptx のレビュー

- 日付: YYYY-MM-DD
- 元ファイル: input/<名前>.pptx（変更していない）
- 出力: output/<名前>-reviewed.pptx
- 画像化: <powerpoint / libreoffice>

## 採用した修正

### 1. <指摘のタイトル>（<カテゴリ>）
- 問題: <見えていた問題>
- 採用した案: <要点>（参考: <資料・ガイド名>）
- 変更した箇所: <スライド番号と図形／マスター等>
- Before / After: before-<n>.png / after-<n>.png

## 採用しなかった指摘
- <タイトル>: そのままにする

## 検証結果
- <案ごとの OK / 要修正>
- 副作用: <なし、または内容と対応>

## 未解決
- <無ければ「なし」>

## 次回に回した点
- <無ければ「なし」>
```

## やらないこと

- `input/` の元ファイルを変更しない。書き換えは必ず `.pptx-review-tmp/` のコピーに対して行う。
- 発表者ノート、アニメーション、画面切り替え、画像・写真・ロゴを変更しない。
- 指摘を5件より多く相談しない。
- 1回の実行で複数のファイルを扱わない。
- 採用されていない変更を「ついでに」しない。
