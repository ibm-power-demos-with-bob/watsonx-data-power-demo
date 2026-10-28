#!/usr/bin/env python3
"""
Recompute career_trajectory and post_bond_active_years from ACTING credits only.

Why: the original method counted every IMDb credit after the Bond film, including
`self` and `archive_footage` appearances (premieres, talk shows, anniversary specials).
That made e.g. Tania Mallet (1 acting credit after Goldfinger) "Thriving Long-Term Career".

Scope (deliberately narrow): only these two columns change.
  - post_bond_active_years  = last ACTING credit year - Bond year
  - career_trajectory       = same thresholds as before, applied to acting credits
Credit counts and rating averages are left exactly as the validated original method produced them.

Acting = IMDb principals category 'actress' or 'actor'.
Idempotent. Needs the cached IMDb dumps in %TEMP%/imdb. Afterwards reload both databases:
    python setup/9-load-bond-data-pg.py ; python setup/9b-load-bond-data-ibmi.py
"""
import gzip, io, json, os
from pathlib import Path

T = Path(os.environ["TEMP"]) / "imdb"
REPO = Path(__file__).resolve().parent.parent
JSON_PATH = REPO / "demo-ui" / "src" / "data" / "bond" / "bond_actress_career_analysis.json"


def stream(n):
    return io.TextIOWrapper(gzip.open(T / n), encoding="utf-8", newline="")


def trajectory(n, yrs):
    if n == 0: return "No Further Acting Credits"
    if yrs >= 10 and n >= 5: return "Thriving Long-Term Career"
    if n >= 10: return "Continued Steady Activity"
    return "Short Activity Tail"


data = json.load(open(JSON_PATH, encoding="utf-8"))
want = {r["nconst"] for r in data}

acting = {n: set() for n in want}
for line in stream("title.principals.tsv.gz"):
    p = line.rstrip("\n").split("\t")
    if len(p) > 3 and p[2] in want and p[3] in ("actress", "actor"):
        acting[p[2]].add(p[0])
tids = {t for s in acting.values() for t in s}
year = {}
for line in stream("title.basics.tsv.gz"):
    p = line.split("\t", 6)
    if p[0] in tids and p[5].isdigit():
        year[p[0]] = int(p[5])

changed = []
for r in data:
    by = r["release_year"]
    yrs_list = [year[t] for t in acting[r["nconst"]] if t in year and year[t] > by]
    n = len(yrs_list)
    active = (max(yrs_list) - by) if yrs_list else 0
    traj = trajectory(n, active)
    if traj != r["career_trajectory"] or active != r["post_bond_active_years"]:
        changed.append((r["actress_name"], r["film_title"], n, r["post_bond_credits_lifetime"],
                        r["career_trajectory"], traj, r["post_bond_active_years"], active))
    r["career_trajectory"] = traj
    r["post_bond_active_years"] = active

with open(JSON_PATH, "w", encoding="utf-8", newline="\n") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.write("\n")

print("rows:", len(data), "| changed:", len(changed))
for c in changed:
    print(f"  {c[0]:22} {c[1]:30} acting_post={c[2]:3} (all={c[3]:4})  {c[4]} -> {c[5]} | active yrs {c[6]} -> {c[7]}")
