#!/usr/bin/env python3
"""
Read-only scan: for every Bond film (Eon + non-Eon), pull the IMDb principals
(cast rows incl. character names) from the cached IMDb dumps in %TEMP%/imdb,
and cross-reference the Fandom 'Bond Girl Actresses' category list
(%TEMP%/fandom_actresses.txt, fetched via the Fandom MediaWiki API).

Matching is by Bond-film cast membership, NOT by name alone, so a same-name
different-person nconst (the Grace Jones bug) cannot slip in.

Output: %TEMP%/imdb/bond_cast_scan.json
"""
import gzip
import io
import json
import os
import unicodedata
from pathlib import Path

IMDB = Path(os.environ["TEMP"]) / "imdb"
OUT = IMDB / "bond_cast_scan.json"

FILMS = {  # primaryTitle, year -> (label, era)
    ("Dr. No", 1962): "Connery", ("From Russia with Love", 1963): "Connery",
    ("Goldfinger", 1964): "Connery", ("Thunderball", 1965): "Connery",
    ("You Only Live Twice", 1967): "Connery",
    ("On Her Majesty's Secret Service", 1969): "Lazenby",
    ("Diamonds Are Forever", 1971): "Connery",
    ("Live and Let Die", 1973): "Moore", ("The Man with the Golden Gun", 1974): "Moore",
    ("The Spy Who Loved Me", 1977): "Moore", ("Moonraker", 1979): "Moore",
    ("For Your Eyes Only", 1981): "Moore", ("Octopussy", 1983): "Moore",
    ("A View to a Kill", 1985): "Moore",
    ("The Living Daylights", 1987): "Dalton", ("Licence to Kill", 1989): "Dalton",
    ("GoldenEye", 1995): "Brosnan", ("Tomorrow Never Dies", 1997): "Brosnan",
    ("The World Is Not Enough", 1999): "Brosnan", ("Die Another Day", 2002): "Brosnan",
    ("Casino Royale", 2006): "Craig", ("Quantum of Solace", 2008): "Craig",
    ("Skyfall", 2012): "Craig", ("Spectre", 2015): "Craig", ("No Time to Die", 2021): "Craig",
    ("Never Say Never Again", 1983): "Non-Eon (Connery)",
    ("Casino Royale", 1967): "Non-Eon (spoof)",
    ("Casino Royale", 1954): "Non-Eon (TV)",
}


def stream(name):
    return io.TextIOWrapper(gzip.open(IMDB / name), encoding="utf-8", newline="")


def norm(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower().strip()


print("title.basics...", flush=True)
films = {}  # tconst -> dict
for line in stream("title.basics.tsv.gz"):
    p = line.rstrip("\n").split("\t")
    if len(p) < 6 or not p[5].isdigit():
        continue
    key = (p[2], int(p[5]))
    if key in FILMS and p[1] in ("movie", "tvMovie", "tvEpisode"):
        # prefer the entry with most votes later; keep all candidates
        films.setdefault(key, []).append(p[0])
print({k: v for k, v in films.items() if len(v) > 1}, flush=True)

# resolve duplicates using ratings votes
cand = {t for v in films.values() for t in v}
votes = {}
for line in stream("title.ratings.tsv.gz"):
    p = line.rstrip("\n").split("\t")
    if p[0] in cand:
        votes[p[0]] = int(p[2])
tt2film = {}
for key, ts in films.items():
    best = max(ts, key=lambda t: votes.get(t, 0))
    tt2film[best] = key
missing = [k for k in FILMS if k not in {v for v in tt2film.values()}]
print("films resolved:", len(tt2film), "missing:", missing, flush=True)

print("title.principals...", flush=True)
cast = []  # (tt, ordering, nconst, category, characters)
for line in stream("title.principals.tsv.gz"):
    p = line.rstrip("\n").split("\t")
    if len(p) >= 6 and p[0] in tt2film and p[3] in ("actress", "actor", "self"):
        cast.append(p)
print("cast rows:", len(cast), flush=True)

ncs = {p[2] for p in cast}
print("name.basics...", flush=True)
names = {}
for line in stream("name.basics.tsv.gz"):
    nid = line.split("\t", 1)[0]
    if nid in ncs:
        q = line.rstrip("\n").split("\t")
        names[nid] = {"name": q[1], "birth": q[2], "death": q[3]}

fandom = [l.strip() for l in open(os.environ["TEMP"] + "/fandom_actresses.txt", encoding="utf-8-sig") if l.strip()]
fnorm = {norm(n): n for n in fandom}

matches = {}  # fandom name -> list of appearances
for p in cast:
    nm = names.get(p[2])
    if nm and norm(nm["name"]) in fnorm:
        film = tt2film[p[0]]
        matches.setdefault(fnorm[norm(nm["name"])], []).append({
            "nconst": p[2], "tt": p[0], "film": film[0], "year": film[1],
            "era": FILMS[film], "category": p[3], "billing": int(p[1]),
            "characters": p[5], "birth": nm["birth"],
        })

json.dump({"matches": matches, "unmatched": [n for n in fandom if n not in matches]},
          open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("fandom names matched via a Bond-film cast row:", len(matches), "/", len(fandom))
print("WROTE", OUT, flush=True)
