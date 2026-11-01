"""LFM3 に Wiki を読ませて 9 問を 1 問ずつ聞く。順番に流す場合と、同時に N 本ずつ流す場合を比べる。

使い方: python3 scripts/par_test.py 同時実行数（1 なら順番）
"""
import json, re, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from query import QUESTIONS, URL, load  # noqa: E402

HEAD, *ITEMS = QUESTIONS.split("\n")
ITEMS = [q for q in ITEMS if re.match(r"\d+\. ", q)]


def ask(item):
    body = {"model": "lfm3-1.7b", "max_tokens": 16000, "temperature": 0.1,
            "messages": [{"role": "user", "content": CORPUS + "\n\n" + HEAD.replace("各問 1 行で、番号を付けて", "1 行で") + "\n" + item}]}
    t = time.time()
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    d = json.load(urllib.request.urlopen(req, timeout=3600))
    c = d["choices"][0]
    return item.split(".")[0], time.time() - t, d["usage"]["completion_tokens"], c["finish_reason"], \
        c["message"]["content"].strip().replace("\n", " ")


if __name__ == "__main__":
    workers = int(sys.argv[1])
    CORPUS = load("wiki")
    t0 = time.time()
    with ThreadPoolExecutor(workers) as ex:
        rows = list(ex.map(ask, ITEMS))
    total = time.time() - t0
    print(f"同時 {workers}: 全体 {total:.0f}s、出力 {sum(r[2] for r in rows)} トークン")
    for n, sec, out, fin, ans in rows:
        print(f"  Q{n}: {sec:5.0f}s out={out:5d} {fin:6s} {ans[:110]}")
