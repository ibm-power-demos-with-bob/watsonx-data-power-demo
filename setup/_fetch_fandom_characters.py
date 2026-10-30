#!/usr/bin/env python3
"""Fetch each Bond character's page from the James Bond Wiki (Fandom, CC BY-SA) for the 88 cast rows.

Output: demo-ui/src/data/bond/bond_fandom_characters.json  (one record per career-analysis row)
  { actress_name, character_name, film_title, page_title, page_url, revision_id, retrieved_at,
    infobox{role, affiliation, occupation, status, nationality}, lead, biography, personality }
Text is cleaned wikitext (templates, links, refs removed). Rows with no validated page get page_title=null.

Page lookup: "Character (Actress)", then "Character", then MediaWiki search. A page is only accepted if it
mentions the actress or the film in its infobox/lead (guards against same-name characters).

Fandom blocks plain page fetches (403) but the MediaWiki API works with a browser User-Agent.
Run: python setup/_fetch_fandom_characters.py      (about 2-4 minutes)
Then: python setup/_score_bond_agency_from_text.py
"""
import json, re, sys, time, unicodedata, urllib.parse, urllib.request
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "demo-ui" / "src" / "data" / "bond"
CAREER = DATA / "bond_actress_career_analysis.json"
OUT = DATA / "bond_fandom_characters.json"
BASE = "https://jamesbond.fandom.com"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}


def api(**p):
    p.update(format="json", formatversion="2")
    url = BASE + "/api.php?" + urllib.parse.urlencode(p)
    for attempt in range(4):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30))
        except Exception:
            time.sleep(1.5 * (attempt + 1))
    return {}


def get_page(title):
    j = api(action="parse", page=title, prop="wikitext|revid", redirects="1")
    if "parse" not in j:
        return None
    p = j["parse"]
    w = p["wikitext"]
    if re.search(r"\{\{\s*disambig", w[:400], re.I):
        return None
    return {"title": p["title"], "revid": p["revid"], "wikitext": w}


def strip_templates(s):
    prev = None
    while prev != s:
        prev = s
        s = re.sub(r"\{\{[^{}]*\}\}", "", s)
    return s


def clean(s):
    s = re.sub(r"<ref[^>]*?/>", "", s)
    s = re.sub(r"<ref[^>]*>.*?</ref>", "", s, flags=re.S)
    s = re.sub(r"<gallery.*?</gallery>", "", s, flags=re.S)
    s = strip_templates(s)
    s = re.sub(r"\[\[(?:File|Image|Category):[^\]]*\]\]", "", s, flags=re.I)
    s = re.sub(r"\[\[[^\]|]*\|([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"\[\[([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"'{2,}", "", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = s.replace("&nbsp;", " ")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def infobox(w):
    m = re.search(r"\{\{Infobox character(.*?)\n\}\}", w, flags=re.S | re.I)
    out = {}
    if not m:
        return out
    for key in ("role", "affiliation", "occupation", "status", "nationality", "portrayed"):
        mm = re.search(r"^\|\s*" + key + r"\s*=(.*)$", m.group(1), flags=re.M)
        if mm:
            v = clean(mm.group(1).split("|")[0]).strip(" ,")
            if v:
                out[key] = v
    return out


def sections(w):
    parts = re.split(r"(?m)^==\s*([^=\n][^=\n]*?)\s*==\s*$", w)
    lead = parts[0]
    secs = {}
    for i in range(1, len(parts) - 1, 2):
        secs.setdefault(parts[i].strip(), parts[i + 1])
    return lead, secs


def pick(secs, names):
    for n in names:
        for k, v in secs.items():
            if k.lower() == n:
                return v
    return ""


def fold(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


def valid(page, actress, film):
    """Accept only a character page (not a subpage) whose infobox 'portrayed' names the actress."""
    if "/" in page["title"]:
        return False
    w = page["wikitext"]
    m = re.search(r"^\|\s*portrayed\s*=(.*)$", w[:6000], flags=re.M)
    last, first = fold(actress.split()[-1]), fold(actress.split()[0])
    if m:
        return last in fold(m.group(1)) and first in fold(m.group(1))
    head = fold(w[:3000])
    return last in head and first in head


# Pages found by hand where the generic lookup fails (character page title on the wiki).
NO_PAGE = {"Joanna Lumley"}  # one of the unnamed "Angels of Death": no individual character page
OVERRIDES = {
    "Halle Berry": "Jinx (Halle Berry)",
    "Cassandra Harris": "Lisl von Schlaf",
    "Lois Chiles": "Holly Goodhead (Lois Chiles)",
}


def candidates(ch, act, film):
    base = re.sub(r"^(Dr\.|Major|Colonel|Miss)\s+", "", ch).strip()
    seen = []
    for t in (f"{ch} ({act})", ch, f"{base} ({act})", base):
        if t not in seen:
            seen.append(t)
    return seen


def find(ch, act, film):
    if act in NO_PAGE:
        return None
    ov = OVERRIDES.get(act)
    if ov:
        pg = get_page(ov)
        if pg and "/" not in pg["title"]:
            return pg
    for t in candidates(ch, act, film):
        pg = get_page(t)
        if pg and valid(pg, act, film):
            return pg
    for q in (f"{ch} {act}", f"{ch} {film}", f"{act} {film}"):
        j = api(action="query", list="search", srsearch=q, srnamespace="0", srlimit="5")
        for hit in j.get("query", {}).get("search", []):
            pg = get_page(hit["title"])
            if pg and valid(pg, act, film):
                return pg
    return None


def main():
    rows = json.loads(CAREER.read_text(encoding="utf-8"))
    out, today = [], date.today().isoformat()
    for i, r in enumerate(rows, 1):
        act, ch, film = r["actress_name"], r["character_name"], r["film_title"]
        pg = find(ch, act, film)
        rec = {"nconst": r["nconst"], "actress_name": act, "character_name": ch, "film_title": film,
               "film_year": r["release_year"], "page_title": None, "page_url": None, "revision_id": None,
               "retrieved_at": today, "infobox": {}, "lead": "", "biography": "", "personality": ""}
        if pg:
            lead, secs = sections(pg["wikitext"])
            rec.update(
                page_title=pg["title"],
                page_url=f"{BASE}/wiki/{urllib.parse.quote(pg['title'].replace(' ', '_'))}?oldid={pg['revid']}",
                revision_id=pg["revid"],
                infobox=infobox(pg["wikitext"]),
                lead=clean(lead),
                biography=clean(pick(secs, ["biography", "history", "fictional character biography", "plot", "role", "in the movies", "synopsis", "characters"])),
                personality=clean(pick(secs, ["personality", "personality and traits", "characteristics"])),
            )
            rec["lead"] = re.sub(r"^.*?\n\n", "", rec["lead"], count=0) if rec["lead"].count("\n\n") > 3 else rec["lead"]
        out.append(rec)
        print(f"{i:2d}/{len(rows)} {act} / {ch}: " +
              (f"{rec['page_title']} bio={len(rec['biography'])} pers={len(rec['personality'])}" if pg else "NO PAGE"),
              flush=True)
        time.sleep(0.15)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    ok = [x for x in out if x["biography"]]
    print(f"\nwrote {OUT.name}: {len(out)} rows, {len(ok)} with biography, "
          f"{len([x for x in out if x['personality']])} with personality, {len([x for x in out if not x['page_title']])} no page")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
