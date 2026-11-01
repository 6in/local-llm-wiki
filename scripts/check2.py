"""機械で「元の資料にあって Wiki に無い」数値・コード表記を抜き出し、LFM3 に足すべきものを判定させる。

使い方: python3 scripts/check2.py 資料名
"""
import json, re, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
URL = "http://127.0.0.1:1234/v1/chat/completions"


def norm(s):
    return s.replace(",", "").replace(" ", "")


def candidates(raw, wiki):
    """Wiki に無いトークンと、それが出てくる元の資料の行。行単位で探すので複数行にまたがるコード表記は拾わない。"""
    w, out = norm(wiki), {}
    for line in raw.splitlines():
        toks = re.findall(r"`([^`]{2,60})`", line) + \
            re.findall(r"\d[\d,.]*\s*(?:K|字|件|分|秒|回|ターン|種|GB|MB|%)", line)
        for t in toks:
            if norm(t) not in w and t not in out:
                out[t] = line.strip()[:300]
    return out


if __name__ == "__main__":
    name = sys.argv[1]
    raw, wiki = (ROOT / "raw" / f"{name}.md").read_text(), (ROOT / "wiki" / f"{name}.md").read_text()
    cands = candidates(raw, wiki)
    listing = "\n".join(f"{i}. 「{t}」 — 元の文: {ctx}" for i, (t, ctx) in enumerate(cands.items(), 1))
    prompt = f"""次は Wiki ページと、元の資料にあるのに Wiki ページに見当たらない語句の一覧です。
    一覧の各語句について、Wiki ページに足すべき重要な事実（仕様の数値・上限・既定値・推奨値・結果の数字など、読者が後で問い合わせそうなもの）なら「追加」、細部・例・内部実装なので不要なら「不要」と判定してください。
    Wiki ページに別の表現で既に書かれているものは「不要」にしてください。

    出力は「番号. 追加|不要」の 1 行ずつだけ。

    ===== Wiki ページ =====

    {wiki}

    ===== 一覧 =====

    {listing}"""
    body = {"model": "lfm3-1.7b", "max_tokens": 16000, "temperature": 0.1,
            "messages": [{"role": "user", "content": prompt}]}
    t = time.time()
    d = json.load(urllib.request.urlopen(urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"}), timeout=3600))
    out = d["choices"][0]["message"]["content"]
    print(f"{name}: 候補 {len(cands)} 件、out={d['usage']['completion_tokens']} {time.time() - t:.0f}s")
    keys = list(cands)
    for m in re.finditer(r"(\d+)\.\s*(追加|不要)", out):
        i = int(m.group(1))
        if m.group(2) == "追加" and 1 <= i <= len(keys):
            print(f"  追加: {keys[i - 1]}  ← {cands[keys[i - 1]][:120]}")
