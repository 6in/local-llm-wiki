"""LFM3（LM Studio）に wiki/ か raw/ を丸ごと読ませ、確認用の 9 問に答えさせる。

使い方: python3 scripts/query.py wiki|raw
"""
import json, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
URL = "http://127.0.0.1:1234/v1/chat/completions"

QUESTIONS = """上の資料だけを根拠に、次の質問に日本語で答えてください。資料に答えが無い場合は「資料に記載なし」と答えてください。各問 1 行で、番号を付けて答えてください。
1. gsd-lite の state.json スキーマの例で、max_turns と retry_max の値はいくつ？
2. gsd-lite v1 では通知の実装は見送るが、例外として v1 に含めるループ終了時のフック点のファイル名は？
3. Linux で Codex sandbox を使う前提として必要な 2 つのものは？
4. ブログの V2.5 実録で、無人ターン数、green になったテストの件数、BLOCKED で待った時間は？
5. agent-console は何も設定しないと何番ポートで動く？ また設定値が不正なときの終了コードは？
6. WebMCP の send_key ツールで指定できるキーは何種類？
7. WebMCP のツールが 1 回の応答に載せる上限は何字？ また Chrome のベストプラクティスは 1 ツールあたり何字を勧めている？
8. gsd-lite の商用ライセンスの年額はいくら？
9. phase63.md（WebMCP の仕様）の内容を、ちょうど 3 つの短い箇条書きで要約してください。"""


def load(kind):
    d = ROOT / kind
    files = sorted(d.glob("*.md"), key=lambda p: (p.name != "index.md", p.name))
    return "".join(f"\n\n===== ファイル: {kind}/{p.name} =====\n\n{p.read_text()}" for p in files)


if __name__ == "__main__":
    kind = sys.argv[1]
    corpus = load(kind)
    body = {"model": "lfm3-1.7b", "max_tokens": 16000, "temperature": 0.1,
            "messages": [{"role": "user", "content": corpus + "\n\n" + QUESTIONS}]}
    t = time.time()
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    d = json.load(urllib.request.urlopen(req, timeout=3600))
    u, m = d["usage"], d["choices"][0]["message"]
    print(f"[{kind}] chars={len(corpus)} prompt={u['prompt_tokens']} out={u['completion_tokens']} "
          f"{time.time() - t:.0f}s finish={d['choices'][0]['finish_reason']}")
    print(m["content"])
