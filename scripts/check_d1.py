"""元の資料にあって Wiki に無い事実を探し、d1-2B で足すべきものに絞る。

1. 機械の照合: 元の資料の各行からコード表記と「数字＋単位」を抜き出し、Wiki に無いものを候補にする。
   数字は単位や桁区切り・空白を無視し、元の文に近い Wiki の段落に同じ数字があれば「ある」とみなす（1 桁は単位も一致が必要）。
2. d1（重要さ）: 候補とその元の文だけを渡し、読者が後で問い合わせそうな事実かを判定する。
3. d1（既出か）: 重要さが閾値以上のコード表記だけ、Wiki で元の文に近い段落を添えて、すでに書かれているかを聞き直す。
   数字の候補は 1. の照合（近い段落に同じ数字があるか）だけで決める。

使い方: python3 scripts/check_d1.py 資料名 [表示件数]
"""
import json, re, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
URL = "http://127.0.0.1:8081/v1/systemone"
IMPORTANT_MIN = 0.5   # これ未満は細部として捨てる
COVERED_MAX = 0.5     # 段落を添えて「書かれている」がこれを超えたら捨てる

IMPORTANT = {"type": "noul", "instructions": "candidate は、仕様の数値・上限・既定値・推奨値・結果の数字など、読者が後で問い合わせそうな重要な事実ですか？（細部・例・内部実装なら いいえ）"}
COVERED = {"type": "noul", "instructions": "wiki_excerpt には、source_sentence のうち candidate が示す事実が（別の言い方でも）書かれていますか？"}

NUM_UNIT = re.compile(r"\d[\d,.]*\s*(?:K|字|件|分|秒|回|ターン|種|GB|MB|%)")


def ask(state, question):
    body = json.dumps({"state": state, "questions": {"q": question}}).encode()
    d = json.load(urllib.request.urlopen(urllib.request.Request(URL, body, {"Content-Type": "application/json"})))
    return d["answers"]["q"]["noul"]


def code_spans(line):
    """`...` の中身。バッククォートを順に組にするので、組の間の地の文は拾わない。"""
    parts = line.split("`")
    return [p for p in parts[1:len(parts) - (len(parts) % 2 == 0):2] if 2 <= len(p) <= 60]


def paragraphs(text):
    return [p for p in re.split(r"\n\s*\n|\n(?=[-|#*])", text) if p.strip()]


def bigrams(s):
    s = re.sub(r"\s+", "", s)
    return {s[i:i + 2] for i in range(len(s) - 1)}


def nearest(paras, sentence, k=2):
    """元の文と 2 文字の重なりが多い Wiki の段落を k 個。"""
    b = bigrams(sentence)
    return sorted(paras, key=lambda p: -len(b & bigrams(p)))[:k]


def number_covered(token, sentence, paras):
    """数字が、元の文に近い Wiki の段落 2 つに出てくるか。1 桁の数字はどこにでもあるので単位まで一致を求める。"""
    num = re.sub(r"[,\s]", "", re.match(r"[\d,.]+", token).group()).rstrip(".")
    want = re.escape(re.sub(r"[,\s]", "", token)) if len(num) == 1 else rf"(?<![\d.]){re.escape(num)}(?![\d])"
    return any(re.search(want, re.sub(r"[,\s]", "", p)) for p in nearest(paras, sentence, 2))


def candidates(raw, wiki):
    flat, paras, out = re.sub(r"[,\s]", "", wiki), paragraphs(wiki), {}
    for line in raw.splitlines():
        for t in code_spans(line):
            if re.sub(r"[,\s]", "", t) not in flat:
                out.setdefault(t, line.strip()[:300])
        for t in NUM_UNIT.findall(line):
            if re.sub(r"[,\s]", "", t) not in flat and not number_covered(t, line, paras):
                out.setdefault(t, line.strip()[:300])
    return out


if __name__ == "__main__":
    name, top = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 10
    raw, wiki = (ROOT / "raw" / f"{name}.md").read_text(), (ROOT / "wiki" / f"{name}.md").read_text()
    paras = paragraphs(wiki)
    t = time.time()
    cands = candidates(raw, wiki)
    scored = sorted(((ask({"candidate": tok, "source_sentence": s}, IMPORTANT), tok, s) for tok, s in cands.items()),
                    reverse=True)
    kept, dropped = [], []
    for imp, tok, s in (r for r in scored if r[0] >= IMPORTANT_MIN):
        if NUM_UNIT.fullmatch(tok):  # 数字は 1. の照合で Wiki に無いと確かめ済み。d1 に聞くと近くの別の数字と混同する
            kept.append((imp, 0.0, tok, s))
            continue
        cov = ask({"candidate": tok, "source_sentence": s, "wiki_excerpt": "\n\n".join(nearest(paras, s))}, COVERED)
        (dropped if cov > COVERED_MAX else kept).append((imp, cov, tok, s))
    print(f"{name}: 候補 {len(cands)} 件 → 重要 {len(kept) + len(dropped)} 件 → 既出を除いて {len(kept)} 件"
          f"（{time.time() - t:.0f}s）")
    kept.sort(reverse=True)
    for i, (imp, cov, tok, s) in enumerate(kept[:top], 1):
        print(f"  {i:2d}. 重要={imp:.2f} 既出={cov:.2f}  {tok}  ← {s[:80]}")
    for imp, cov, tok, s in dropped:
        print(f"   除外 既出={cov:.2f} 重要={imp:.2f}  {tok}  ← {s[:60]}")
