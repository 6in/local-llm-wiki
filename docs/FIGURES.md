# ブログ図の生成指示

次の 6 枚の画像を、画像生成ツールで 1 枚ずつ生成してください。

- 各図のプロンプトは「共通スタイル」＋「その図の PROMPT」をつなげたものです。両方とも英語のまま使ってください
- 図中の日本語ラベルは、引用符の中の文字をそのまま正確に描いてください。それ以外の文字は入れないでください
- 縦横比は 16:9（1600x900 程度）
- 生成した画像は、指定のファイルパス（このファイルからの相対パス）に保存してください。形式は JPEG（.jpg）。PNG で生成された場合は .jpg に変換して保存してください
- 日本語ラベルが崩れた図は 1 回だけ作り直してください
- 6 枚とも保存できたら、各ファイルのパスを一覧にして報告してください。このファイルとブログ本文（blog.md）は編集しないでください

## 共通スタイル

```
Flat vector infographic for a friendly Japanese tech blog. White background, generous whitespace,
rounded rectangles and circles, thin clean outlines, no gradients, no 3D, no photorealism, no drop-shadow clutter.
Palette: deep navy #1E2761 (main shapes, headings), mint green #02C39A (accents, arrows, highlights),
pale blue #EFF4FD (cards), soft gray #5A6478 (secondary text), small touches of warm yellow #FFD166 for sparkles only.
Mood: pop and cheerful but tidy. Small cute robot characters (round head, antenna, simple face) may appear as mascots:
a BIG robot (Strata), a SMALL robot (LFM3) and a tiny robot holding a judge's gavel (d1).
Render every Japanese label EXACTLY as quoted, in a clean sans-serif (Noto Sans JP style),
keep labels short, and do not add any other text. Default aspect ratio 16:9 (1600x900) unless noted.
```

## FIG-01

- 保存先: `images/blog-llm-wiki/fig01-overview.jpg`
- 縦横比: 16:9

```
Three robot mascots standing around a large open notebook labeled "Wiki" in the center. Left: a BIG navy robot holding a pen, badge "Strata 125B", caption below "書く". Right: a SMALL mint robot reading the notebook with a magnifying glass, badge "LFM3 1.7B", caption below "読む". Front: a tiny gray robot holding a judge's gavel, badge "d1", caption below "見張る". Behind them, a laptop silhouette with a small house icon on its screen and a tag "料金ゼロ". A few yellow sparkles.
```

## FIG-02

- 保存先: `images/blog-llm-wiki/fig02-needle.jpg`
- 縦横比: 16:9

```
A very long horizontal scroll of gray placeholder text stretching across the image. At the far left a small mint key icon labeled "合言葉", in the middle a small navy box icon labeled "番号". Above the scroll, five mint checkmarks evenly spaced with labels "30K", "60K", "120K", "200K", "250K". At the right end the SMALL mint robot holding up the key and the box happily. Small caption at bottom right "メモリ 10GB".
```

## FIG-03

- 保存先: `images/blog-llm-wiki/fig03-ingest.jpg`
- 縦横比: 16:9

```
Two panels side by side. Left panel titled "1 回目": the BIG navy robot copying a long document word by word onto a page that runs off the edge and is cut with a jagged tear, a small red-free gray tag "途中で切れた", and a clock labeled "5 分". Right panel titled "2 回目": the same robot calmly writing a neat, shorter page with a mint checkmark, tags "1/3 に縮める" and "思考は短く", and a clock labeled "80 秒". A mint arrow from left to right.
```

## FIG-04

- 保存先: `images/blog-llm-wiki/fig04-query.jpg`
- 縦横比: 16:9

```
Two stacks of paper side by side feeding into the SMALL mint robot in the middle. Left stack tall, labeled "元の資料 5.5 万トークン". Right stack shorter and neatly bound, labeled "Wiki 2.2 万トークン". Above the robot two score cards: left card "7 問 + △1" and right card "7 問 + ✕1". Over the right card, a small thought bubble where the robot is gluing a puzzle piece labeled "500 字？" into a gap labeled "1.5K 字". Gentle, slightly humorous.
```

## FIG-05

- 保存先: `images/blog-llm-wiki/fig05-whack.jpg`
- 縦横比: 16:9

```
A whack-a-mole game board with six holes. The tiny gray robot holds its gavel like a hammer, looking puzzled. Moles popping up are labeled with tags: on the left side mint moles "1.5K" and "5 分" (labeled group "本当に落ちた"), on the right side gray moles "29 件" and "20 ターン" (labeled group "実は書いてある"). When one side goes down the other pops up, shown with small motion lines. Title tag at top "いたちごっこ". Cheerful, humorous.
```

## FIG-06

- 保存先: `images/blog-llm-wiki/fig06-roles.jpg`
- 縦横比: 16:9

```
A clean horizontal pipeline of four rounded cards left to right: "raw 資料" (stack of papers), "取り込み" with the BIG navy robot and a small moon icon tagged "夜間バッチ", "質問" with the SMALL mint robot tagged "速い・軽い", "点検" with the tiny gavel robot tagged "1 件 0.05 秒". Under the 点検 card, a small human silhouette with a checkmark tagged "最後は人か Strata". Mint arrows connect the cards, and a thin dashed arrow from 質問 back to "raw 資料" labeled "見つからなければ出典へ".
```
