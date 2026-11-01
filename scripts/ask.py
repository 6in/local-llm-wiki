"""LFM3 に Wiki を調べるツール（wiki_tools.py）を使わせて、質問に答えさせる。

最初に渡すのは index.md だけ。ページを丸ごとは読ませず、検索・リンク・節の読み出しはツールが肩代わりする。

使い方: python3 scripts/ask.py "質問"          … 1 問だけ答える
        python3 scripts/ask.py --test            … query.py の 9 問を 1 問ずつ答える
"""
import json, re, sys, time, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import wiki_tools  # noqa: E402

URL = "http://127.0.0.1:1234/v1/chat/completions"
MAX_STEPS = 8  # ツールを呼ぶ往復の上限
WIKI_SEARCH_MAX = 2  # Wiki を検索できる回数。超えたら元の資料を 1 回だけ探して終える

SYSTEM = """あなたは Wiki を調べて質問に答える係です。手元にあるのは下の索引（index.md）だけです。
- まず wiki_search で答えのありそうな節を探し、必要なら wiki_read でその節を読んでください。
- 関係するページをたどるときは wiki_links を使ってください。
- Wiki に答えが無いときだけ、source_search で元の資料を探してください。Wiki の検索は 2 回までです。
- 答えが見つかったら、それ以上調べずにすぐ答えてください。
- 推測で答えず、ツールが返した内容に書いてあることだけで、日本語で簡潔に答えてください。最後の行に「出典: ページ名 / 見出し」を書いてください。
- それでも見つからなければ「資料に記載なし」と答えてください。

===== index.md =====

{index}"""


def chat(messages, tools=True):
    body = {"model": "lfm3-1.7b", "max_tokens": 16000, "temperature": 0.1, "messages": messages,
            "tools": wiki_tools.openai_tools(), "tool_choice": "auto" if tools else "none"}
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    d = json.load(urllib.request.urlopen(req, timeout=3600))
    return d["choices"][0], d["usage"]["prompt_tokens"]


def keywords(question):
    """質問から検索語を作る。元の資料は日本語なので、LLM に言い換えさせず質問の語をそのまま使う。"""
    words = re.findall(r"[A-Za-z0-9_.\-]{2,}|[ァ-ヴー]{2,}|[一-龥々]{2,}", question)
    words = [w.removeprefix("何") for w in words if not re.fullmatch(r"[\d.]+", w)]  # 「2.」のような番号と「何」は落とす
    return " ".join(dict.fromkeys(w for w in words if w))


def finish(messages, question, pending=()):
    """元の資料を質問の語で 1 回だけ探し、ツールを外して、集めた内容だけで答えさせる。"""
    found = wiki_tools.source_search(keywords(question))
    for i, tc in enumerate(pending):  # 呼びかけのツールには、最初の 1 つに検索結果、残りに打ち切りを返す
        messages.append({"role": "tool", "tool_call_id": tc["id"],
                         "content": f"元の資料を「{keywords(question)}」で探した結果:\n{found}" if i == 0 else "（打ち切り）"})
    if not pending:
        messages.append({"role": "user", "content": f"元の資料を「{keywords(question)}」で探した結果:\n{found}"})
    messages.append({"role": "user", "content": "調べるのはここまでです。ここまでにツールが返した内容だけで答えてください。"
                                                "答えが無ければ「資料に記載なし」と答えてください。"})
    c, prompt = chat(messages, tools=False)
    text = (c["message"].get("content") or "").strip()
    if c["message"].get("tool_calls") or "<tool_call>" in text:  # それでもツールを呼ぼうとしたら、答えは出なかった扱い
        text = "資料に記載なし（調べきれず）"
    return text, prompt


def ask(question):
    """答え、呼んだツールの記録、読ませた最大のトークン数を返す。

    Wiki の検索は WIKI_SEARCH_MAX 回まで。それを超えて検索しようとしたとき、LLM が元の資料を探そうとしたとき、
    往復が MAX_STEPS に達したときは、スクリプトが元の資料を質問の語で 1 回だけ探して、答えを出させる。
    """
    messages = [{"role": "system", "content": SYSTEM.format(index=(wiki_tools.WIKI / "index.md").read_text())},
                {"role": "user", "content": question}]
    calls, peak, searches = [], 0, 0
    for _ in range(MAX_STEPS):
        c, prompt = chat(messages)
        peak = max(peak, prompt)
        m = c["message"]
        if not m.get("tool_calls"):
            return (m.get("content") or "").strip() or f"（finish={c['finish_reason']}）", calls, peak
        messages.append({"role": "assistant", "content": m.get("content") or "", "tool_calls": m["tool_calls"]})
        for i, tc in enumerate(m["tool_calls"]):
            name, args = tc["function"]["name"], json.loads(tc["function"]["arguments"] or "{}")
            searches += name == "wiki_search"
            if name == "source_search" or searches > WIKI_SEARCH_MAX:
                calls.append(f"［元の資料を探して終了: {keywords(question)}］")
                text, prompt = finish(messages, question, m["tool_calls"][i:])
                return text, calls, max(peak, prompt)
            calls.append(f"{name}({', '.join(map(str, args.values()))})")
            messages.append({"role": "tool", "tool_call_id": tc["id"], "content": wiki_tools.call(name, args)})
    calls.append(f"［上限。元の資料を探して終了: {keywords(question)}］")
    text, prompt = finish(messages, question)
    return text, calls, max(peak, prompt)


if __name__ == "__main__":
    if sys.argv[1:] == ["--test"]:
        from query import QUESTIONS
        questions = [q for q in QUESTIONS.split("\n") if re.match(r"\d+\. ", q)]
    else:
        questions = [" ".join(sys.argv[1:])]
    t0 = time.time()
    for q in questions:
        t = time.time()
        answer, calls, peak = ask(q)
        print(f"■ {q}\n  ツール: {' → '.join(calls) or 'なし'}\n  （{time.time() - t:.0f}s、最大 {peak} トークン）\n"
              f"  {answer.replace(chr(10), chr(10) + '  ')}\n", flush=True)
    print(f"全体 {time.time() - t0:.0f}s")
