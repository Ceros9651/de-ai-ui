---
name: pptx-review
description: input/ に置いた PowerPoint 資料（.pptx）から「AIが作ったっぽさ」（角丸カードとアイコンの並び、絵文字、紫青グラデと影、全部中央寄せ、「革新的」「シームレス」のようなAI文体）を見つけ、見つかったすべての指摘に推奨の修正案を自動で選んでデザインと本文に適用し、output/ に書き出す。途中でユーザーに確認しない。/pptx-review [ファイル名] で明示的に呼ばれたときだけ使う。
argument-hint: [ファイル名]
disable-model-invocation: true
---

# /pptx-review

引数: `$ARGUMENTS`

分析は `pptx-reviewer` サブエージェントに任せ、pptx の書き換えはこのメインの会話で行う。

**このスキルはユーザーに確認せずに最後まで進める（AskUserQuestion を使わない）。** 判断が要る場面では、必ず推奨の選択肢を選ぶ。

- 指摘は件数で絞らず、見つかったものをすべて直す。
- 各指摘は、サブエージェントが「（推奨）」とした案Aを採用する。
- 選ばなかった案は report.md に残し、ユーザーが後から別の直し方を選べるようにする。
- 止めるのは、続けられない場合（対象ファイルが無い、python-pptx や画像化の手段が無い）だけ。

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
   - 引数が無ければ `input/*.pptx` を一覧する。1つならそれを使い、2つ以上なら更新日時がいちばん新しいものを使う。どれを選んだかと、他のファイルは `/pptx-review <ファイル名>` で指定できることを、最初に一言伝える。
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
2. 返ってきた候補（実物を確認できたものだけ）をすべて references.md の書式で追記する（追加日は今日の日付）。「候補から外したもの」は追記しない。
3. 候補が1件も無ければ、references.md は空のまま、レビューでは Web 検索の参考だけを使う。

## 2. レビューと案の選択

1. `pptx-reviewer` を `mode: review`、`file: input/<名前>.pptx`、`work: .pptx-review-tmp/`、`renderer` で呼ぶ。返ってくる指摘に件数の上限は無い。
2. すべての指摘について、案A（推奨）を採用する。ユーザーには聞かない。
   - 推奨案が付いていない指摘があれば、`pptx-reviewer` に推奨案を付けて返すよう再依頼する（自分で勝手に決めない）。
   - 推奨案どうしがぶつかる場合（同じ図形に別々の変更をする、など）は、重要度の高い指摘の案を優先し、もう一方はぶつからない範囲だけを適用する。どう調整したかを applied.md に書く。
3. 進める前に、指摘の件数と、各指摘で選んだ推奨案を1行ずつユーザーに伝える（確認は求めず、そのまま適用に進む）。マスター/テーマ/レイアウトを変える案には「【全スライドに影響】」と付ける。
4. 指摘が0件なら、「AIっぽさは見つからなかったため出力しません」と伝え、`.pptx-review-tmp/` を削除して終了する。

## 3. 適用

採用した案を1件ずつ、`work-<k-1>.pptx` から `work-<k>.pptx` を作る形で適用する（k は 1 から）。1件ごとにファイルを分けるのは、壊れたときにその案だけ取り消せるようにするため。

1. 案ごとに `$T/apply-<k>.py` を書く。サブエージェントの「適用内容」をもとに、python-pptx で `work-<k-1>.pptx` を開き、該当スライド・図形（shape id で特定する）・マスター/レイアウト/テーマを書き換えて `work-<k>.pptx` に保存する。
   - 図形は `slide.shapes` を shape id で探す（グループの中は再帰的に探す）。名前やインデックスで探さない。
   - API で扱えないもの（グラデーション、影、角丸の調整値、背景）は `shape._element` などの lxml 要素を直接書き換える。下の「XML 操作の早見表」に従う。
   - スクリプトは Write ツールで書く（シェルのヒアドキュメントは、日本語や引用符を含むと壊れやすい）。shape id での検索や背景の差し替えなど、何度も使う処理は `$T/common.py` にまとめ、各スクリプトから `sys.path.insert(0, ".pptx-review-tmp")` で読み込んでよい。
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
   - 「要修正」「副作用」「新たなAIっぽさ」「その他の気になる点」があれば、ユーザーに聞かずに、すべて推奨の直し方で直す。追加の `apply-<k>.py` を書いて適用し、手順1から検証をやり直す。
   - 直してからの再検証は**2回まで**。それでも残る問題は、`applied.md` に「未解決」として書き、出力へ進む。
   - 直すにはユーザーしか知らない事実が要るもの（出典の中身、日付、発表者名など）は作らない。サブエージェントの推奨案（記入欄を置く、など）で対応し、report.md の「未解決」に「ユーザーの記入が必要」として書く。

## 5. 出力

1. `output/<名前>-reviewed.pptx` か `output/<名前>-reviewed/` が既にあれば、上書きする（最後に上書きしたことを伝える）。
2. 書き出す:
   - `cp "$T/work-final.pptx" "output/<名前>-reviewed.pptx"`
   - `output/<名前>-reviewed/` を作り（上書きのときは中を空にしてから）、変更したスライドの `before-<n>.png` と `after-<n>.png` だけをコピーする。
   - `output/<名前>-reviewed/report.md` を下の書式で書く。
3. 準備の5で記録したハッシュと、`input/<名前>.pptx` の今のハッシュが同じことを確かめる。違っていたら、その旨をユーザーに伝える（このスキルの手順では起きないはずなので、原因を調べる）。
4. `docs/slide-principles.md` の該当する節に、採用した案の「方針ルール」を `- <ルール>（<名前>.pptx <YYYY-MM-DD>）` の形で追記する。既存ルールと重複するものは追記しない。矛盾するものは既存ルールを書き換えず、「例外」の節に `- <ルール>（<名前>.pptx <YYYY-MM-DD>。「<既存ルール>」の例外）` として書き、最後に伝える。
5. `.pptx-review-tmp/` を削除する。
6. 最後に次のものだけを短く伝える。
   - 出力したファイルのパス
   - 変更の要約（指摘ごとに1行。選んだ推奨案）
   - 未解決の問題（ユーザーの記入が必要なものを含む）
   - 上書きしたもの、方針の例外として書いたもの
   - 別の直し方を選びたいときは report.md の「選ばなかった案」を見て指示すればよいこと

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
- 採用した案（推奨）: <要点>（参考: <資料・ガイド名>）
- 変更した箇所: <スライド番号と図形／マスター等>
- Before / After: before-<n>.png / after-<n>.png
- 選ばなかった案: <案B: 要点> / <案C: 要点>（無ければ「なし」）

## 検証で見つかり直したもの
- <内容と対応。無ければ「なし」>

## 検証結果
- <案ごとの OK / 要修正>
- 副作用: <なし、または内容と対応>

## 未解決
- <2回の再検証で直らなかったもの、ユーザーの記入が必要なもの。無ければ「なし」>
```

## やらないこと

- `input/` の元ファイルを変更しない。書き換えは必ず `.pptx-review-tmp/` のコピーに対して行う。
- 発表者ノート、アニメーション、画面切り替え、画像・写真・ロゴを変更しない。
- ユーザーに確認を求めない（AskUserQuestion を使わない）。止めるのは続けられないときだけ。
- 指摘の件数で絞らない。見つかったものはすべて直す。
- ユーザーしか知らない事実（数字・出典・日付・名前）を作らない。
- 1回の実行で複数のファイルを扱わない。
- 指摘に無い変更を「ついでに」しない。
