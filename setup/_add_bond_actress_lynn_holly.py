#!/usr/bin/env python3
"""
One-off: add Lynn-Holly Johnson (Bibi Dahl, For Your Eyes Only, 1981) to
bond_actress_career_analysis.json.

She was missing from the dataset, so she never appeared in the UI even though
she is central to the "Curse of the Bond Girls" story (her quote:
"My agent told me, 'If you take that role you'll never work again'...").

Career metrics are computed from the locally cached IMDb datasets in
%TEMP%/imdb (already downloaded by setup/_imdb_fix_fetch.py), using exactly the
same formulas as setup/_fix_bond_nconsts.py. Idempotent: skips if already present.

After running: python setup/9-load-bond-data-pg.py   (and 9b-load-bond-data-ibmi.py
if BOND_PRIMARY_SOURCE=ibmi).
"""
import gzip
import io
import json
import math
import os
from pathlib import Path

NCONST = "nm0000468"
REPO = Path(__file__).resolve().parent.parent
JSON_PATH = REPO / "demo-ui" / "src" / "data" / "bond" / "bond_actress_career_analysis.json"
IMDB = Path(os.environ["TEMP"]) / "imdb"


def stream(name):
    return io.TextIOWrapper(gzip.open(IMDB / name), encoding="utf-8", newline="")


# --- extract from cached IMDb dumps -------------------------------------------------
birth = None
for line in stream("name.basics.tsv.gz"):
    p = line.rstrip("\n").split("\t")
    if p[0] == NCONST:
        birth = int(p[2])
        break

tids = set()
for line in stream("title.principals.tsv.gz"):
    p = line.rstrip("\n").split("\t")
    if len(p) > 3 and p[2] == NCONST:
        tids.add(p[0])

titles = {}
for line in stream("title.basics.tsv.gz"):
    p = line.split("\t", 6)
    if p[0] in tids:
        titles[p[0]] = {"year": p[5]}
for line in stream("title.ratings.tsv.gz"):
    p = line.rstrip("\n").split("\t")
    if p[0] in titles:
        titles[p[0]]["rating"], titles[p[0]]["votes"] = p[1], p[2]

rows = [
    (int(t["year"]),
     float(t["rating"]) if "rating" in t else None,
     int(t.get("votes", 0)))
    for t in titles.values() if t["year"].isdigit()
]


# --- metrics (same formulas as _fix_bond_nconsts.py) --------------------------------
def avg_rating(rs_):
    rs = [r[1] for r in rs_ if r[1] is not None]
    return round(sum(rs) / len(rs), 2) if rs else None


def avg_score(rs_):
    vs = [r[1] * math.log10(r[2]) for r in rs_ if r[1] is not None and r[2] > 0]
    return round(sum(vs) / len(vs) / 5, 2) if vs else None


def age_group(age):
    return "Early Career (<26)" if age < 26 else "Prime (26-31)" if age < 32 else "Established (32+)"


def trajectory(post_credits, active_years):
    if post_credits == 0:
        return "No Further Screen Credits"
    if active_years >= 10 and post_credits >= 5:
        return "Thriving Long-Term Career"
    if post_credits >= 10:
        return "Continued Steady Activity"
    return "Short Activity Tail"


by = 1981
pre = [c for c in rows if c[0] < by]
p5 = [c for c in rows if by < c[0] <= by + 5]
post = [c for c in rows if c[0] > by]
age = by - birth
post_l_r = avg_rating(post)
pre_r = avg_rating(pre)

record = {
    "actress_name": "Lynn-Holly Johnson",
    "character_name": "Bibi Dahl",
    "film_title": "For Your Eyes Only",
    "release_year": by,
    "bond_era": "Moore",
    "nconst": NCONST,
    "role_category": "Secondary Ally / Protégé",
    "occupation": "Olympic-Hopeful Ice Skater / Kristatos' Protégée",
    "character_depth_score": 3,
    "has_independent_objective": False,
    "professional_expertise": True,
    "participates_in_climax": False,
    "intelligence_or_combat_role": False,
    "survives_film": True,
    "age_at_bond": age,
    "age_group": age_group(age),
    "prior_career_years": (by - min(c[0] for c in pre)) if pre else 0,
    "pre_bond_credits": len(pre),
    "pre_bond_avg_rating": pre_r,
    "pre_bond_avg_score": avg_score(pre),
    "post_bond_credits_5y": len(p5),
    "post_bond_avg_rating_5y": avg_rating(p5),
    "post_bond_credits_lifetime": len(post),
    "post_bond_avg_rating_lifetime": post_l_r,
    "post_bond_avg_score_lifetime": avg_score(post),
    "post_bond_active_years": (max(c[0] for c in post) - by) if post else 0,
    "rating_delta_naive": round(post_l_r - pre_r, 2) if post_l_r is not None and pre_r is not None else None,
    "career_trajectory": trajectory(len(post), (max(c[0] for c in post) - by) if post else 0),
    "character_description": (
        "Teenage Olympic-hopeful ice skater sponsored by the smuggler Kristatos; "
        "infatuated with Bond, she throws herself at him and is put on a train home "
        "rather than seduced."
    ),
}

data = json.load(open(JSON_PATH, encoding="utf-8"))
if any(r["nconst"] == NCONST for r in data):
    print("Already present - nothing to do.")
else:
    # keep chronological order: insert after the last 1981 row (Carole Bouquet)
    idx = max(i for i, r in enumerate(data) if r["release_year"] <= by) + 1
    data.insert(idx, record)
    with open(JSON_PATH, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(json.dumps(record, indent=2, ensure_ascii=False))
    print("Wrote", JSON_PATH, "rows:", len(data))
