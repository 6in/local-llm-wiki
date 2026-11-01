"""Wiki から FAQ を作り、元の資料で答え直して照らし合わせる。

1. Strata: wiki/<名前>.md から、具体的な事実を問う FAQ を作る → faq/<名前>.json
2. LFM3: FAQ の質問を、raw/<名前>.md だけを読んで答え直す
3. d1: FAQ の答えと LFM3 の答えが同じ事実を言っているかを判定する
仕組みが誤りに気づけるかを見るため、数字をわざと書き換えた FAQ（planted）を混ぜる。

使い方: python3 scripts/faq.py [gen|check|all]（既定 all）
"""
import json, random, re, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW, WIKI, FAQ = ROOT / "raw", ROOT / "wiki", ROOT / "faq"
STRATA = "http://127.0.0.1:8080/v1/chat/completions"
LFM = "http://127.0.0.1:1234/v1/chat/completions"
D1 = "http://127.0.0.1:8081/v1/systemone"
PLANTED = 3

SAME = {"type": "noul", "instructions": "answer_a と answer_b は、question に対して同じ事実（数値・名前・可否）を答えていますか？ 言い回しの違いは気にしない。"}


def post(url, body):
    req = urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=7200))


def gen(name):
    page = (WIKI / f"{name}.md").read_text()
    prompt = f"""次の Wiki ページから、読者が問い合わせそうな FAQ を 10 個作ってください。

要件:
- 質問は、数値・既定値・設定名・ファイル名・件数・可否など、答えが 1 つに決まる具体的な事実を問う
- 答えは Wiki ページに書いてあることだけで、1 文で書く
- 出力は JSON 配列だけ: [{{"q": "質問", "a": "答え"}}, ...]

===== Wiki ページ =====

{page}"""
    t = time.time()
    d = post(STRATA, {"model": "strata", "max_tokens": 16000, "temperature": 0.2, "reasoning_effort": "low",
                      "messages": [{"role": "user", "content": prompt}]})
    text = d["choices"][0]["message"]["content"]
    faqs = json.loads(text[text.index("["):text.rindex("]") + 1])
    print(f"gen {name}: {len(faqs)} 件 {time.time() - t:.0f}s", flush=True)
    (FAQ / f"{name}.json").write_text(json.dumps(faqs, ensure_ascii=False, indent=1))


def plant(items):
    """数字を含む答えから PLANTED 件を選び、数字を 1 つ書き換えた複製を足す。"""
    rng = random.Random(1)
    pool = [it for it in items if re.search(r"\d", it["a"])]
    for it in rng.sample(pool, min(PLANTED, len(pool))):
        nums = re.findall(r"\d+", it["a"])
        n = rng.choice(nums)
        items.append({**it, "a": it["a"].replace(n, str(int(n) + 7), 1), "planted": True})


def answer_from_raw(raw, q):
    prompt = f"""{raw}

上の資料だけを根拠に、次の質問に日本語で 1 文で答えてください。資料に答えが無い場合は「資料に記載なし」と答えてください。
質問: {q}"""
    for max_tokens in (8000, 16000):  # 思考が止まらず打ち切られたら、上限を上げて 1 回だけやり直す
        d = post(LFM, {"model": "lfm3-1.7b", "max_tokens": max_tokens, "temperature": 0.1,
                       "messages": [{"role": "user", "content": prompt}]})
        c = d["choices"][0]
        if c["finish_reason"] == "stop":
            return c["message"]["content"].strip()
    return "（打ち切り）"


def check():
    items = []
    for f in sorted(FAQ.glob("*.json")):
        items += [{**it, "page": f.stem} for it in json.loads(f.read_text())]
    plant(items)
    t = time.time()
    for it in sorted(items, key=lambda x: x["page"]):  # 同じ資料を続けて読ませ、読み込みを使い回す
        raw = (RAW / f"{it['page']}.md").read_text()
        it["raw_a"] = answer_from_raw(raw, it["q"])
        state = {"question": it["q"], "answer_a": it["a"], "answer_b": it["raw_a"]}
        it["same"] = post(D1, {"state": state, "questions": {"q": SAME}})["answers"]["q"]["noul"]
        it["verdict"] = "記載なし" if "記載なし" in it["raw_a"] else ("一致" if it["same"] >= 0.5 else "食い違い")
    print(f"check: {len(items)} 件 {time.time() - t:.0f}s", flush=True)
    (ROOT / "faq-check.json").write_text(json.dumps(items, ensure_ascii=False, indent=1))
    for v in ("一致", "食い違い", "記載なし"):
        hit = [it for it in items if it["verdict"] == v]
        print(f"{v}: {len(hit)} 件（うち仕込み {sum(1 for it in hit if it.get('planted'))} 件）")
    for it in items:
        if it["verdict"] != "一致" or it.get("planted"):
            mark = "【仕込み】" if it.get("planted") else ""
            print(f"\n[{it['verdict']} {it['same']:.2f}]{mark} {it['page']}\n  Q: {it['q']}\n  FAQ: {it['a']}\n  元資料: {it['raw_a'][:200]}")


if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "all"
    FAQ.mkdir(exist_ok=True)
    if step in ("gen", "all"):
        for p in sorted(RAW.glob("*.md")):
            gen(p.stem)
    if step in ("check", "all"):
        check()
