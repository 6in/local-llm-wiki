"""Wiki を調べるツール。LLM にページを丸ごと読ませず、検索とリンクの抽出をこちらで肩代わりする。

ページは見出しごとの節に分けて扱う。検索は日本語向けに 2 文字の重なりで順位を付ける。
- wiki_search(query)        当たった節の一覧（ページ名・見出し・抜粋）
- wiki_links(page)          ページ内の [[リンク]] と、index.md にある各ページの一行説明
- wiki_read(page, heading)  1 つの節だけ
- source_search(query)      元の資料（raw/）を同じやり方で探す
"""
import math, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW, WIKI = ROOT / "raw", ROOT / "wiki"
TOP = 5        # 検索で返す節の数
SNIPPET = 300  # 抜粋の字数
LEN_NORM = 0.5  # 長い節ほど点を割り引く強さ（BM25 の b）。長い表の節がどの語にも当たって上位を占めるのを防ぐ
LINK = re.compile(r"\[\[([^\]]+)\]\]")


def bigrams(s):
    s = re.sub(r"\s+", "", s.lower())
    return {s[i:i + 2] for i in range(len(s) - 1)}


def sections(folder):
    """(ページ名, 見出し, 本文) の一覧。見出しの前の部分は見出しを「(冒頭)」とする。"""
    out = []
    for p in sorted(folder.glob("*.md")):
        if p.name == "index.md":  # 索引は LLM に最初から渡すので、検索には含めない
            continue
        heading, lines = "(冒頭)", []
        for line in p.read_text().splitlines() + ["# "]:
            m = re.match(r"#{1,6}\s+(.*)", line)
            if m:
                if "".join(lines).strip():
                    out.append((p.stem, heading, "\n".join(lines).strip()))
                heading, lines = m.group(1).strip(), []
            else:
                lines.append(line)
    return out


def snippet(text, terms):
    """terms を前から順に探し、最初に見つかった語のまわりを切り出す。どの語も当たらなければ先頭。"""
    hit = next((i for i in (text.lower().find(t.lower()) for t in terms) if i >= 0), -1)
    start = max(0, hit - SNIPPET // 3) if hit >= 0 else 0
    return ("…" if start else "") + text[start:start + SNIPPET].replace("\n", " ") + ("…" if start + SNIPPET < len(text) else "")


def match(term, body, body_bigrams):
    """語がそのまま出てくれば 1。出てこなければ 2 文字の重なりの割合（半分未満は 0）。
    英数字だけの語（send_key など）は重なりで見ない。se・en のような 2 文字はどこにでもあるため。"""
    if term.lower() in body.lower():
        return 1.0
    if term.isascii():
        return 0.0
    b = bigrams(term)
    cover = len(b & body_bigrams) / len(b) if b else 0
    return cover if cover >= 0.5 else 0.0


def search(folder, query):
    """語ごとの一致に IDF で重みを付けて足し、節の長さで割り引く。どの節にも出てくる語（WebMCP など）では順位が動かない。"""
    terms = [t.strip("\"'「」") for t in query.split() if t.strip("\"'「」")]
    secs = [(page, heading, text, heading + "\n" + text) for page, heading, text in sections(folder)]
    marks = [[match(t, body, bigrams(body)) for t in terms] for *_, body in secs]
    df = [sum(1 for m in marks if m[i] > 0) for i in range(len(terms))]
    idf = [math.log((len(secs) + 1) / (d + 0.5)) for d in df]
    avg = sum(len(body) for *_, body in secs) / max(len(secs), 1)
    scored = sorted(((sum(w * x for w, x in zip(idf, m)) / (1 - LEN_NORM + LEN_NORM * len(body) / avg), page, heading, text)
                     for (page, heading, text, body), m in zip(secs, marks)), key=lambda r: -r[0])
    rare = [t for _, t in sorted(zip(idf, terms), reverse=True)]  # 抜粋は珍しい語のまわりを優先する
    hits = [f"- [{page}] {heading}\n  {snippet(text, rare)}" for score, page, heading, text in scored[:TOP] if score > 0]
    return "\n".join(hits) or "見つかりませんでした。"


def wiki_search(query):
    return search(WIKI, query)


def source_search(query):
    return search(RAW, query)


def wiki_links(page):
    page = page.strip("[] ")
    path = WIKI / f"{page}.md"
    if not path.exists():
        return f"「{page}」というページはありません。あるのは: {', '.join(p.stem for p in sorted(WIKI.glob('*.md')))}"
    index = (WIKI / "index.md").read_text()
    out = [f"見出し: {' / '.join(h for p, h, _ in sections(WIKI) if p == page)}", "リンク:"]
    for name in dict.fromkeys(LINK.findall(path.read_text())):
        desc = next((l.split("—", 1)[1].strip() for l in index.splitlines() if l.startswith(f"- [[{name}]]") and "—" in l), "")
        out.append(f"- [[{name}]] {desc[:80]}")
    return "\n".join(out if len(out) > 2 else out + ["（なし）"])


def wiki_read(page, heading):
    page = page.strip("[] ")
    secs = [(h, t) for p, h, t in sections(WIKI) if p == page]
    if not secs:
        return f"「{page}」というページはありません。"
    exact = [(h, t) for h, t in secs if h == heading]
    near = exact or [(h, t) for h, t in secs if heading and (heading in h or h in heading)]
    if not near:
        return f"「{heading}」という見出しはありません。見出し: {' / '.join(h for h, _ in secs)}"
    h, t = near[0]
    others = f"\n\n（ほかに当てはまる見出し: {' / '.join(x for x, _ in near[1:])}）" if len(near) > 1 else ""
    return f"## {h}\n\n{t}{others}"


TOOLS = {
    "wiki_search": (wiki_search, "Wiki をキーワードで検索し、当たった節（ページ名・見出し・抜粋）を返す", {"query": "キーワード（空白区切りで複数可）"}),
    "wiki_links": (wiki_links, "Wiki のページの見出し一覧と、そのページからのリンクを返す", {"page": "ページ名"}),
    "wiki_read": (wiki_read, "Wiki のページの 1 つの節を読む", {"page": "ページ名", "heading": "見出し"}),
    "source_search": (source_search, "Wiki に答えが無いときだけ、元の資料をキーワードで検索する", {"query": "キーワード（空白区切りで複数可）"}),
}


def openai_tools():
    """OpenAI 互換 API の tools 引数の形。"""
    return [{"type": "function", "function": {"name": n, "description": d, "parameters": {
        "type": "object", "properties": {k: {"type": "string", "description": v} for k, v in args.items()},
        "required": list(args)}}} for n, (_, d, args) in TOOLS.items()]


def call(name, args):
    if name not in TOOLS:
        return f"{name} というツールはありません。"
    fn, _, params = TOOLS[name]
    return fn(*(str(args.get(k, "")) for k in params))
