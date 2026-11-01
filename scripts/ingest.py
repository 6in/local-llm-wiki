"""raw/ の資料を Strata に読ませ、wiki/ に資料ごとのページと index.md を書かせる。

使い方: python3 scripts/ingest.py [資料名 ...]（省略時は raw/ の全部。最後に index.md を作り直す）
"""
import json, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW, WIKI = ROOT / "raw", ROOT / "wiki"
URL = "http://127.0.0.1:8080/v1/chat/completions"


def chat(prompt, max_tokens=32000):
    body = {"model": "strata", "max_tokens": max_tokens, "temperature": 0.2, "reasoning_effort": "low",
            "messages": [{"role": "user", "content": prompt}]}
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    t = time.time()
    d = json.load(urllib.request.urlopen(req, timeout=7200))
    u = d["usage"]
    m = d["choices"][0]["message"]
    print(f"  prompt={u['prompt_tokens']} out={u['completion_tokens']} {time.time() - t:.0f}s "
          f"finish={d['choices'][0]['finish_reason']} thinking={len(m.get('reasoning_content') or '')}字 "
          f"page={len(m['content'])}字", flush=True)
    return m["content"].strip()


def strip_fence(text):
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0]
    return text.strip() + "\n"


def ingest(src, all_names):
    others = ", ".join(f"[[{n}]]" for n in all_names if n != src.stem)
    text = src.read_text()
    limit = len(text) // 3
    prompt = f"""あなたは個人用 Wiki の管理者です。次の資料を読み、この資料に対応する Wiki ページを Markdown で書いてください。

要件:
- 1 行目は `# <ページの題>`、2 行目に資料の内容を 1 文で書く
- 資料の章立てに沿って見出しを付け、内容を整理して書く。長さは資料の 3 分の 1 程度（目安 {limit} 字以内）。言い回しや例・図の説明は削り、事実を残す
- 具体的な数値・既定値・設定名・環境変数・ファイル名・パス・コマンド・件数・時間・終了コードは省略せず、そのままの値で残す
- 資料に書かれていないことは書かない。推測で補わない
- 他のページと関係する箇所には [[ページ名]] の形でリンクを張る。使えるページ名: {others}
- 最後に `## 出典` を置き、`raw/{src.name}` と書く
- 出力はページの本文だけ。前置きや説明は付けない

===== 資料: raw/{src.name} =====

{text}"""
    print(f"ingest {src.name}", flush=True)
    (WIKI / f"{src.stem}.md").write_text(strip_fence(chat(prompt)))


def build_index():
    pages = sorted(p for p in WIKI.glob("*.md") if p.name != "index.md")
    heads = "\n\n".join(f"### [[{p.stem}]]\n" + "\n".join(p.read_text().splitlines()[:40]) for p in pages)
    prompt = f"""あなたは個人用 Wiki の管理者です。次は Wiki の各ページの冒頭部分です。これを元に、Wiki の入口となる index.md を Markdown で書いてください。

要件:
- 1 行目は `# 索引`
- 各ページについて、[[ページ名]] と、そのページに何が書いてあるかを 1〜2 文で書く
- 続けて `## 話題から探す` を置き、主な話題（例: 設定、セキュリティ、運用）ごとに、どのページを見ればよいかを書く
- ページに書かれていないことは書かない
- 出力は index.md の本文だけ

{heads}"""
    print("build index.md", flush=True)
    (WIKI / "index.md").write_text(strip_fence(chat(prompt, 8000)))


if __name__ == "__main__":
    all_srcs = sorted(RAW.glob("*.md"))
    names = [s.stem for s in all_srcs]
    targets = [RAW / f"{a.removesuffix('.md')}.md" for a in sys.argv[1:]] or all_srcs
    t0 = time.time()
    for src in targets:
        ingest(src, names)
    build_index()
    print(f"done in {(time.time() - t0) / 60:.1f} min", flush=True)
