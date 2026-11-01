# local-llm-wiki

Andrej Karpathy の「LLM Wiki」（資料を LLM に読ませて Wiki にまとめ、質問には Wiki で答える）を、**手元の Mac のローカル LLM だけで**試した記録です。

経緯と結果は、ブログの下書き [docs/blog.md](docs/blog.md) にまとめています。

## 3 つのモデルの分担

| 工程 | モデル | 役割 |
|---|---|---|
| 取り込み | Strata（Qwen3.8-Flash-Next 125B MoE, IQ3_S） | `raw/` の資料を読み、`wiki/` にページを書く |
| 質問 | LFM3-1.7B（LM Studio） | Wiki を丸ごと読んで質問に答える |
| 点検 | d1-2B（llama.cpp） | 落ちた事実の判定と、FAQ の答え合わせ |

試した環境は M4 Max（メモリ 128GB）です。

## 用意するもの

- Python 3（標準ライブラリだけで動きます）
- OpenAI 互換の API で動く 3 つのサーバー。URL は各スクリプトの先頭に書いてあります。

| サーバー | URL | 起動の例 |
|---|---|---|
| Strata | `http://127.0.0.1:8080/v1` | `reasoning_effort` に対応したもの |
| LM Studio | `http://127.0.0.1:1234/v1` | `lfm3-1.7b` を 262144 文脈で読み込む |
| d1 | `http://127.0.0.1:8081/v1/systemone` | `llama-server -hf LiquidAI/d1-2B-GGUF:Q8_0 -b 8192 -ub 8192 -c 16384 --port 8081` |

## 使い方

`raw/` に Markdown の資料を置いてから、順に実行します。試したときに使った資料と、できた Wiki はリポジトリに含めていません。

```sh
python3 scripts/ingest.py              # Strata が raw/ を読み、wiki/ にページと index.md を書く
python3 scripts/query.py wiki          # LFM3 が wiki/ を読んで確認用の 9 問に答える（raw なら元の資料で）
python3 scripts/check_d1.py 資料名     # 元の資料にあって Wiki に無い事実を d1 で絞り込む
python3 scripts/faq.py                 # Wiki から FAQ を作り、元の資料で答え直して d1 で照らし合わせる
```

`query.py` の 9 問は、試したときの資料に合わせたものです。別の資料で使うときは書き換えてください。

## フォルダ

```
scripts/
  ingest.py      取り込み（Strata）
  query.py       質問（LFM3）
  check_d1.py    点検その 1：落ちた事実を探す（照合 + d1）。最終版
  faq.py         点検その 2：FAQ で答え合わせ（Strata + LFM3 + d1）
  check.py       点検の試行 1：LFM3 に比べさせる（見落としが多く不採用）
  check2.py      点検の試行 2：LFM3 に判定させる（暴走して不採用）
  par_test.py    質問を並列にして速くなるかの試験（速くならなかった）
docs/
  blog.md        ブログの下書き
  FIGURES.md     図の生成指示
  images/        図（Antigravity CLI で生成）
```

## 結果のあらまし

- 取り込みは 5 本で 9.4 分。Wiki は元の資料の 4 割ほどの長さで、確認した事実 12 個のうち 11 個が残った。
- FAQ の答え合わせは 53 件中 48 件が一致。わざと数字を書き換えた 3 件は、すべて「食い違い」として見つかった。
- お金はかかっていません（すべてローカル）。
