"""LFM3 に元の資料と Wiki ページを並べて読ませ、ページから落ちた事実と食い違いを挙げさせる。

使い方: python3 scripts/check.py [資料名 ...]（省略時は raw/ の全部）。結果は check/<資料名>.md
"""
import json, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW, WIKI, OUT = ROOT / "raw", ROOT / "wiki", ROOT / "check"
URL = "http://127.0.0.1:1234/v1/chat/completions"

PROMPT = """あなたは Wiki の校閲者です。「元の資料」と、それを要約した「Wiki ページ」を比べてください。

次の 2 種類を探して、Markdown の箇条書きで挙げてください。
- 欠落: 元の資料にある具体的な数値・既定値・設定名・環境変数・ファイル名・コマンド・件数・時間・終了コード・上限値のうち、Wiki ページに無いもの
- 食い違い: Wiki ページの記述が元の資料と違うもの

各項目は「種類（欠落/食い違い）: 元の資料の記述をそのまま引用 → Wiki ページでの扱い」の形で 1 行に書いてください。
言い回しの違いや、例・図の説明の省略は挙げないでください。見つからなければ「なし」と書いてください。

===== 元の資料 =====

{raw}

===== Wiki ページ =====

{page}"""


def check(name):
    raw, page = (RAW / f"{name}.md").read_text(), (WIKI / f"{name}.md").read_text()
    body = {"model": "lfm3-1.7b", "max_tokens": 16000, "temperature": 0.1,
            "messages": [{"role": "user", "content": PROMPT.format(raw=raw, page=page)}]}
    t = time.time()
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    d = json.load(urllib.request.urlopen(req, timeout=3600))
    u, m = d["usage"], d["choices"][0]["message"]
    print(f"{name}: prompt={u['prompt_tokens']} out={u['completion_tokens']} {time.time() - t:.0f}s "
          f"finish={d['choices'][0]['finish_reason']}", flush=True)
    (OUT / f"{name}.md").write_text(m["content"].strip() + "\n")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for name in [a.removesuffix(".md") for a in sys.argv[1:]] or sorted(p.stem for p in RAW.glob("*.md")):
        check(name)
