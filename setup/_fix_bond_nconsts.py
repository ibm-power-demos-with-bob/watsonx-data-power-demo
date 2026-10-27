#!/usr/bin/env python3
"""
One-off data fix for bond_actress_career_analysis.json.

Five rows had an `nconst` pointing at a *different person* with the same name
(e.g. Grace Jones -> nm7763198, which has no credits), so all career metrics
were computed from the wrong IMDb profile. This script swaps in the correct
nconst and recomputes the career metrics using the same method the original
data used (validated against Maud Adams / Britt Ekland: exact match on credits,
active years, average rating, prior years, age and delta).

Input : %TEMP%/imdb/extract.json (produced by setup/_imdb_fix_fetch.py)
Output: rewrites demo-ui/src/data/bond/bond_actress_career_analysis.json in place
"""
import json
import math
import os
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
JSON_PATH = REPO / "demo-ui" / "src" / "data" / "bond" / "bond_actress_career_analysis.json"
EXTRACT = Path(os.environ["TEMP"]) / "imdb" / "extract.json"

# (actress, film) -> correct nconst
FIXES = {
    ("Grace Jones", "A View to a Kill"): "nm0005063",
    ("Denise Richards", "The World Is Not Enough"): "nm0000612",
    ("Jane Seymour", "Live and Let Die"): "nm0005412",
    ("Barbara Bach", "The Spy Who Loved Me"): "nm0000819",
    ("Daniela Bianchi", "From Russia with Love"): "nm0000938",
}

x = json.load(open(EXTRACT, encoding="utf-8"))


def credits(nid):
    out = []
    for tid, _, _cat in x["principals"].get(nid, []):
        t = x["titles"].get(tid)
        if t and t["year"].isdigit():
            out.append(
                (int(t["year"]),
                 float(t["rating"]) if "rating" in t else None,
                 int(t.get("votes", 0)))
            )
    return out


def avg_rating(rows):
    rs = [r[1] for r in rows if r[1] is not None]
    return round(sum(rs) / len(rs), 2) if rs else None


def avg_score(rows):
    # Vote-weighted quality score. Approximates the original metric
    # (within ~5% on calibration rows): mean(rating * log10(votes)) / 5.
    vs = [r[1] * math.log10(r[2]) for r in rows if r[1] is not None and r[2] > 0]
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


data = json.load(open(JSON_PATH, encoding="utf-8"))
for r in data:
    key = (r["actress_name"], r["film_title"])
    if key not in FIXES:
        continue
    nid = FIXES[key]
    by = r["release_year"]
    rows = credits(nid)
    birth = int(x["names"][nid][2])
    pre = [c for c in rows if c[0] < by]
    p5 = [c for c in rows if by < c[0] <= by + 5]
    post = [c for c in rows if c[0] > by]
    age = by - birth

    r["nconst"] = nid
    r["age_at_bond"] = age
    r["age_group"] = age_group(age)
    r["prior_career_years"] = (by - min(c[0] for c in pre)) if pre else 0
    r["pre_bond_credits"] = len(pre)
    r["pre_bond_avg_rating"] = avg_rating(pre)
    r["pre_bond_avg_score"] = avg_score(pre)
    r["post_bond_credits_5y"] = len(p5)
    r["post_bond_avg_rating_5y"] = avg_rating(p5)
    r["post_bond_credits_lifetime"] = len(post)
    r["post_bond_avg_rating_lifetime"] = avg_rating(post)
    r["post_bond_avg_score_lifetime"] = avg_score(post)
    r["post_bond_active_years"] = (max(c[0] for c in post) - by) if post else 0
    r["rating_delta_naive"] = (
        round(r["post_bond_avg_rating_lifetime"] - r["pre_bond_avg_rating"], 2)
        if r["post_bond_avg_rating_lifetime"] is not None and r["pre_bond_avg_rating"] is not None
        else None
    )
    r["career_trajectory"] = trajectory(len(post), r["post_bond_active_years"])
    print(key, {k: r[k] for k in (
        "nconst", "age_at_bond", "prior_career_years", "pre_bond_credits",
        "post_bond_credits_5y", "post_bond_credits_lifetime",
        "post_bond_active_years", "post_bond_avg_rating_lifetime",
        "rating_delta_naive", "career_trajectory")})

with open(JSON_PATH, "w", encoding="utf-8", newline="\n") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("Wrote", JSON_PATH)
