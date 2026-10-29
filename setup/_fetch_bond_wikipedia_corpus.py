"""Build the Bond text corpus from REAL, attributable sources: English Wikipedia (CC BY-SA 4.0).

For each (actress, Bond film) row in bond_actress_career_analysis.json this fetches the actress's Wikipedia
article through the MediaWiki API (plain-text extract + revision id) and keeps up to MAX_CHUNKS short passages
that mention the Bond film, the character or "Bond". Each kept passage is stored verbatim with a permanent
link to the exact revision (oldid), so every excerpt can be checked against its source.

Replaces the earlier hand-written (fictional) corpus. Output: demo-ui/src/data/bond/bond_semantic_corpus.json
Next step after running: python setup/_embed_bond_corpus.py, then python setup/9-load-bond-data-pg.py
"""
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests

DATA_DIR = Path(__file__).resolve().parent.parent / "demo-ui" / "src" / "data" / "bond"
API = "https://en.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "bond-demo-research/1.0 (IBM presales demo; excerpts attributed with oldid links)"}
MAX_CHUNKS = 2
MAX_CHARS = 650
MIN_CHARS = 120
LICENCE = "CC BY-SA 4.0"

# Wikipedia titles that differ from the name in our data (extend as the report below shows misses)
TITLE_OVERRIDES = {}


def sentences(par):
    return re.split(r"(?<=[.!?])\s+(?=[A-Z\"'])", par.strip())


def fetch(title):
    params = {
        "action": "query", "format": "json", "redirects": 1, "titles": title,
        "prop": "extracts|revisions|pageprops", "explaintext": 1, "exsectionformat": "plain",
        "rvprop": "ids|timestamp", "ppprop": "disambiguation",
    }
    for attempt in range(6):  # Wikipedia returns 429 when requests are too fast: back off and retry
        r = requests.get(API, headers=HEADERS, timeout=30, params=params)
        if r.status_code == 429:
            time.sleep(float(r.headers.get("Retry-After", 5)) + 2 * attempt)
            continue
        r.raise_for_status()
        break
    else:
        raise RuntimeError("still rate limited after retries")
    page = next(iter(r.json()["query"]["pages"].values()))
    if "missing" in page or "disambiguation" in page.get("pageprops", {}):
        return None
    return {"title": page["title"], "revid": page["revisions"][0]["revid"],
            "ts": page["revisions"][0]["timestamp"], "text": page.get("extract", "")}


def pick_chunks(text, film, character):
    film_core = re.sub(r"^(The|A)\s+", "", film).lower()
    char_keys = [c.strip().lower() for c in re.split(r"[/&]|\band\b", character) if len(c.strip()) > 3]
    scored = []
    for i, par in enumerate(p for p in text.split("\n") if len(p) >= 60):
        low = par.lower()
        s = 0
        if film_core in low:
            s += 3
        if any(k in low for k in char_keys):
            s += 2
        if "bond" in low or "007" in low:
            s += 1
        if s >= 3:
            scored.append((s, i, par))
    scored.sort(key=lambda t: (-t[0], t[1]))
    chunks = []
    for _, _, par in scored[:MAX_CHUNKS]:
        out = ""
        for sent in sentences(par):
            if len(out) + len(sent) + 1 > MAX_CHARS and len(out) >= MIN_CHARS:
                break
            out = (out + " " + sent).strip()
        if len(out) >= MIN_CHARS or out == par.strip():
            chunks.append(out)
    return chunks


def main():
    rows = json.loads((DATA_DIR / "bond_actress_career_analysis.json").read_text(encoding="utf-8"))
    cache, docs, misses = {}, [], []
    retrieved = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for row in rows:
        name = row["actress_name"]
        title = TITLE_OVERRIDES.get(name, name)
        if title not in cache:
            try:
                cache[title] = fetch(title)
            except Exception as e:  # network/API failure: record as an error, not as a missing page
                cache[title] = "ERROR"
                print("ERR", title, e)
            time.sleep(1.0)
        page = cache[title]
        if page == "ERROR":
            misses.append((name, row["film_title"], "FETCH ERROR (re-run)"))
            continue
        if not page:
            misses.append((name, row["film_title"], "no page / disambiguation"))
            continue
        chunks = pick_chunks(page["text"], row["film_title"], row["character_name"])
        if not chunks:
            misses.append((name, row["film_title"], "no passage mentions film/character"))
            continue
        url = f"https://en.wikipedia.org/w/index.php?title={quote(page['title'].replace(' ', '_'))}&oldid={page['revid']}"
        for n, chunk in enumerate(chunks, 1):
            docs.append({
                "doc_id": f"WP_{row['nconst']}_{row['release_year']}_{n}",
                "actress_name": name,
                "character_name": row["character_name"],
                "film_title": row["film_title"],
                "film_year": row["release_year"],
                "source_year": int(page["ts"][:4]),
                "source_type": "Wikipedia article",
                "publication": f"Wikipedia: {page['title']}",
                "page_title": page["title"],
                "source_url": url,
                "revision_id": page["revid"],
                "licence": LICENCE,
                "retrieved_at": retrieved,
                "text": chunk,
            })
    (DATA_DIR / "bond_semantic_corpus.json").write_text(json.dumps(docs, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{len(docs)} excerpts for {len({(d['actress_name'], d['film_title']) for d in docs})} of {len(rows)} rows")
    print("Rows with no excerpt:")
    for m in misses:
        print("  ", m)


if __name__ == "__main__":
    main()
