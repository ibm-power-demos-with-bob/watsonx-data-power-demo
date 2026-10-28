#!/usr/bin/env python3
"""
Widen bond_actress_career_analysis.json using the Fandom 'Bond Girl Actresses' category
(film-cast members only; games/radio/music/voice-dubbers excluded).

Career metrics are computed from the cached IMDb datasets (%TEMP%/imdb) with the SAME formulas
as setup/_fix_bond_nconsts.py. Identity safety: an nconst is only accepted if
  (A) the person appears in that Bond film's IMDb principals, or
  (B) a unique IMDb actress match whose own credits include a title within +/-5 years of the Bond year.
Anyone failing is written to %TEMP%/imdb/needs_review.json instead of being added.

Role fields (role_category, occupation, depth score, flags, description) are editorial judgment,
not IMDb data. Idempotent: rows already present (by nconst) are skipped.

Inputs : %TEMP%/imdb/candidates.json (from the scan), IMDb dumps.  Run: python setup/_add_bond_actresses_fandom.py
Then   : python setup/9-load-bond-data-pg.py ; python setup/9b-load-bond-data-ibmi.py
"""
import gzip, io, json, math, os
from pathlib import Path

T = Path(os.environ["TEMP"]) / "imdb"
REPO = Path(__file__).resolve().parent.parent
JSON_PATH = REPO / "demo-ui" / "src" / "data" / "bond" / "bond_actress_career_analysis.json"
NON_EON = "Non-Eon"

# flags string: independent_objective, professional_expertise, climax, intel/combat, survives  (T/F)
# (name, film, year, era, character, role_category, occupation, depth, flags, description)
ROWS = [
    ("Alison Doody", "A View to a Kill", 1985, "Moore", "Jenny Flex", "Villainess / Henchwoman", "Zorin's Assistant", 3, "FFFFF", "One of Max Zorin's female associates in the plot to destroy Silicon Valley."),
    ("Barbara Carrera", "Never Say Never Again", 1983, NON_EON, "Fatima Blush", "Villainess / Operative", "SPECTRE Assassin", 6, "TTFTF", "SPECTRE's flamboyant assassin, who tries to kill Bond with a string of improvised devices before being killed herself."),
    ("Caroline Munro", "The Spy Who Loved Me", 1977, "Moore", "Naomi", "Villainess / Henchwoman", "Helicopter Pilot", 3, "FTFFF", "Stromberg's helicopter pilot, who hunts Bond and is killed by a missile from his submerged Lotus."),
    ("Cassandra Harris", "For Your Eyes Only", 1981, "Moore", "Countess Lisl von Schlaf", "Secondary Ally / Tragic", "Kristatos' Lover", 2, "FFFFF", "A countess and companion of the smuggler Kristatos, who is killed by his henchman Locque."),
    ("Corinne Cléry", "Moonraker", 1979, "Moore", "Corinne Dufour", "Secondary Ally / Tragic", "Drax's Personal Pilot", 2, "FTFFF", "Hugo Drax's pilot, who helps Bond and is killed by Drax's dogs."),
    ("Daliah Lavi", "Casino Royale", 1967, NON_EON, "The Detainer (007)", "Secondary Ally / Agent", "Spy Agent", 3, "FTFFT", "One of the many agents drawn into the 1967 spoof's 'multiple Bonds' plot."),
    ("Deborah Kerr", "Casino Royale", 1967, NON_EON, "Agent Mimi (Lady Fiona McTarry)", "Secondary Ally / Agent", "Spy Agent", 4, "FTFFT", "Scottish widow and secret agent in the 1967 spoof."),
    ("Fiona Fullerton", "A View to a Kill", 1985, "Moore", "Pola Ivanova", "Secondary Ally / Agent", "KGB Agent", 4, "FTFTT", "A Soviet KGB agent whose path crosses Bond's during the Zorin investigation."),
    ("Joanna Pettet", "Casino Royale", 1967, NON_EON, "Mata Bond", "Secondary Ally / Agent", "Spy (Bond's daughter)", 5, "TTTTT", "Bond's daughter in the 1967 spoof, who infiltrates the villain's organisation."),
    ("Karin Dor", "You Only Live Twice", 1967, "Connery", "Helga Brandt", "Villainess / Operative", "SPECTRE No. 11", 5, "TTFTF", "SPECTRE's senior agent in Japan, killed by piranhas after failing to kill Bond."),
    ("Kim Basinger", "Never Say Never Again", 1983, NON_EON, "Domino Petachi", "Lead Bond Girl", "Largo's Mistress", 6, "TFTFT", "Mistress of the SPECTRE agent Largo, who turns against him and helps Bond."),
    ("Kristina Wayborn", "Octopussy", 1983, "Moore", "Magda", "Secondary Ally / Double Agent", "Kamal Khan's Associate", 4, "FTTFT", "Kamal Khan's associate who seduces Bond and later fights alongside Octopussy's troupe."),
    ("Lana Wood", "Diamonds Are Forever", 1971, "Connery", "Plenty O'Toole", "Secondary Ally / Tragic", "Casino Socialite", 2, "FFFFF", "A flirtatious casino socialite, killed after being mistaken for Tiffany Case."),
    ("Linda Christian", "Casino Royale", 1954, NON_EON, "Valerie Mathis", "Lead Bond Girl", "Bond's Contact", 3, "FFFFT", "Bond's love interest and contact in the 1954 TV adaptation."),
    ("Martine Beswick", "Thunderball", 1965, "Connery", "Paula Caplan", "Secondary Ally / Tragic", "MI6 Agent in Nassau", 4, "TTFTF", "An MI6 agent in the Bahamas, captured and killed to avoid giving up information."),
    ("Molly Peters", "Thunderball", 1965, "Connery", "Patricia Fearing", "Secondary Ally / Minor", "Physiotherapist", 2, "FTFFT", "A physiotherapist at the Shrublands health clinic."),
    ("Talisa Soto", "Licence to Kill", 1989, "Dalton", "Lupe Lamora", "Lead Bond Girl", "Sanchez's Girlfriend", 4, "FFFFT", "Drug lord Sanchez's girlfriend, who becomes Bond's ally."),
    ("Tania Mallet", "Goldfinger", 1964, "Connery", "Tilly Masterson", "Secondary Ally / Tragic", "Vengeful Sister", 4, "TFFTF", "Jill Masterson's sister, who tries to kill Goldfinger and is killed by Oddjob."),
    # nconst accepted on unique match + plausible credits near Bond year
    ("Alexandra Bastedo", "Casino Royale", 1967, NON_EON, "Meg McTarry", "Secondary Ally / Minor", "Supporting Role", 2, "FFFFT", "One of the McTarry-sisters group in the 1967 spoof."),
    ("Angela Scoular", "On Her Majesty's Secret Service", 1969, "Lazenby", "Ruby Bartlett", "Secondary Ally / Minor", "Angel of Death", 3, "FFFFT", "One of Blofeld's 'Angels of Death' at the Piz Gloria clinic."),
    ("Barbara Bouchet", "Casino Royale", 1967, NON_EON, "Miss Moneypenny", "Secondary Ally / Minor", "MI6 Secretary", 3, "FFFFT", "Moneypenny in the 1967 spoof."),
    ("Carmen du Sautoy", "The Man with the Golden Gun", 1974, "Moore", "Saida", "Secondary Ally / Minor", "Belly Dancer", 2, "FFFFT", "A belly dancer in the Beirut nightclub scene."),
    ("Cecilie Thomsen", "Tomorrow Never Dies", 1997, "Brosnan", "Inga Bergstrom", "Secondary Ally / Minor", "Language Teacher", 2, "FFFFT", "A Danish language teacher and former lover of Bond."),
    ("Cherry Gillespie", "Octopussy", 1983, "Moore", "Midge", "Secondary Ally / Minor", "Octopus Cult Member", 2, "FFTFT", "A member of Octopussy's all-female troupe."),
    ("Daisy Beaumont", "The World Is Not Enough", 1999, "Brosnan", "Nina", "Secondary Ally / Minor", "Supporting Role", 1, "FFFFT", "A minor role in the film."),
    ("Elaine Taylor", "Casino Royale", 1967, NON_EON, "Peg McTarry", "Secondary Ally / Minor", "Supporting Role", 2, "FFFFT", "One of the McTarry sisters in the 1967 spoof."),
    ("Eva Rueber-Staier", "The Spy Who Loved Me", 1977, "Moore", "Rubelvitch", "Secondary Ally / Minor", "KGB Secretary", 2, "FTFFT", "The secretary to KGB head General Gogol; a former Miss World."),
    ("Gabriella Licudi", "Casino Royale", 1967, NON_EON, "Eliza McTarry", "Secondary Ally / Minor", "Supporting Role", 2, "FFFFT", "One of the McTarry sisters in the 1967 spoof."),
    ("Geraldine Chaplin", "Casino Royale", 1967, NON_EON, "Keystone Kop", "Secondary Ally / Minor", "Cameo", 1, "FFFFT", "A cameo in the 1967 spoof."),
    ("Jacqueline Bisset", "Casino Royale", 1967, NON_EON, "Giovanna Goodthighs", "Secondary Ally / Minor", "Supporting Role", 2, "FFFFT", "A supporting role in the 1967 spoof."),
    ("Jeanne Roland", "You Only Live Twice", 1967, "Connery", "Hera", "Secondary Ally / Minor", "Masseuse", 2, "FFFFT", "A Japanese masseuse who attends Bond."),
    ("Joanna Lumley", "On Her Majesty's Secret Service", 1969, "Lazenby", "Angel of Death (English)", "Secondary Ally / Minor", "Angel of Death", 2, "FFFFT", "One of Blofeld's 'Angels of Death'; her film debut."),
    ("Madeline Smith", "Live and Let Die", 1973, "Moore", "Miss Caruso", "Secondary Ally / Minor", "Italian Agent", 2, "FFFFT", "Bond's Italian companion in the pre-title sequence."),
    ("Margaret Nolan", "Goldfinger", 1964, "Connery", "Dink", "Secondary Ally / Minor", "Masseuse", 2, "FFFFT", "The masseuse seen with Bond in the Goldfinger pre-title sequence."),
    ("Mireille Darc", "Casino Royale", 1967, NON_EON, "Jag", "Secondary Ally / Minor", "Supporting Role", 2, "FFFFT", "A supporting role in the 1967 spoof."),
    ("Nadja Regin", "From Russia with Love", 1963, "Connery", "Kerim Bey's Girlfriend", "Secondary Ally / Minor", "Kerim Bey's Girlfriend", 2, "FFFFT", "The girlfriend of the Turkish MI6 contact Ali Kerim Bey."),
    ("Nina Muschallik", "The World Is Not Enough", 1999, "Brosnan", "Verushka", "Secondary Ally / Minor", "Supporting Role", 1, "FFFFT", "A minor role in the film."),
    ("Nina Young", "Tomorrow Never Dies", 1997, "Brosnan", "Tamara Steel", "Secondary Ally / Minor", "Supporting Role", 1, "FFFFT", "A minor role in the film."),
    ("Serena Scott Thomas", "The World Is Not Enough", 1999, "Brosnan", "Molly Warmflash", "Secondary Ally / Minor", "Doctor", 2, "FTFFT", "The MI6 doctor who clears Bond for duty."),
    ("Tonia Sotiropoulou", "Skyfall", 2012, "Craig", "Bond's Lover", "Secondary Ally / Minor", "Supporting Role", 1, "FFFFT", "A brief role as Bond's lover; she had auditioned for the role of Sévérine."),
    ("Tracey Crisp", "Casino Royale", 1967, NON_EON, "Heather McTarry", "Secondary Ally / Minor", "Supporting Role", 2, "FFFFT", "One of the McTarry sisters in the 1967 spoof."),
    ("Tsai Chin", "You Only Live Twice", 1967, "Connery", "Ling", "Secondary Ally / Minor", "Agent in Hong Kong", 3, "FTFFT", "The Chinese agent in the pre-title sequence; she returned as Madam Wu in 2006."),
    ("Valerie Leon", "The Spy Who Loved Me", 1977, "Moore", "Hotel Receptionist", "Secondary Ally / Minor", "Hotel Receptionist", 1, "FFFFT", "A hotel receptionist; she returned in Never Say Never Again."),
    ("Virginia Hey", "The Living Daylights", 1987, "Dalton", "Rubavitch", "Secondary Ally / Minor", "General Pushkin's Girlfriend", 2, "FFFFT", "The girlfriend of the Soviet General Pushkin."),
]


def stream(name):
    return io.TextIOWrapper(gzip.open(T / name), encoding="utf-8", newline="")


cands = {o["actress_name"]: o for o in json.load(open(T / "candidates.json", encoding="utf-8"))}
want = {}  # nconst -> row
review = []
for row in ROWS:
    c = cands.get(row[0])
    if not c or not c.get("nconst"):
        review.append({"name": row[0], "reason": "no nconst"})
        continue
    want[c["nconst"]] = (row, c["tier"])

print("streaming IMDb for", len(want), "people...", flush=True)
birth = {}
for line in stream("name.basics.tsv.gz"):
    p = line.split("\t", 3)
    if p[0] in want:
        birth[p[0]] = p[2]
cred = {n: [] for n in want}
tids = set()
for line in stream("title.principals.tsv.gz"):
    p = line.rstrip("\n").split("\t")
    if len(p) > 3 and p[2] in want:
        cred[p[2]].append(p[0]); tids.add(p[0])
titles = {}
for line in stream("title.basics.tsv.gz"):
    p = line.split("\t", 6)
    if p[0] in tids:
        titles[p[0]] = {"year": p[5]}
for line in stream("title.ratings.tsv.gz"):
    p = line.rstrip("\n").split("\t")
    if p[0] in titles:
        titles[p[0]]["rating"], titles[p[0]]["votes"] = p[1], p[2]


def credits(n):
    return [(int(titles[t]["year"]), float(titles[t]["rating"]) if "rating" in titles[t] else None,
             int(titles[t].get("votes", 0))) for t in cred[n] if t in titles and titles[t]["year"].isdigit()]


def avg_rating(rs_):
    rs = [r[1] for r in rs_ if r[1] is not None]
    return round(sum(rs) / len(rs), 2) if rs else None


def avg_score(rs_):
    vs = [r[1] * math.log10(r[2]) for r in rs_ if r[1] is not None and r[2] > 0]
    return round(sum(vs) / len(vs) / 5, 2) if vs else None


def age_group(a):
    return "Early Career (<26)" if a < 26 else "Prime (26-31)" if a < 32 else "Established (32+)"


def trajectory(n, yrs):
    if n == 0: return "No Further Screen Credits"
    if yrs >= 10 and n >= 5: return "Thriving Long-Term Career"
    if n >= 10: return "Continued Steady Activity"
    return "Short Activity Tail"


data = json.load(open(JSON_PATH, encoding="utf-8"))
have = {r["nconst"] for r in data}
added = []
for n, (row, tier) in want.items():
    name, film, by, era, char, cat, occ, depth, fl, desc = row
    if n in have:
        continue
    rows = credits(n)
    b = birth.get(n, "\\N")
    if not b.isdigit():
        review.append({"name": name, "nconst": n, "reason": "no birth year"}); continue
    if tier == "B" and not any(abs(c[0] - by) <= 5 for c in rows):
        review.append({"name": name, "nconst": n, "reason": "no IMDb credit within +/-5y of %d (possible same-name mismatch)" % by}); continue
    pre = [c for c in rows if c[0] < by]; p5 = [c for c in rows if by < c[0] <= by + 5]; post = [c for c in rows if c[0] > by]
    age = by - int(b)
    act = (max(c[0] for c in post) - by) if post else 0
    pr, pl = avg_rating(pre), avg_rating(post)
    flags = [x == "T" for x in fl]
    added.append({
        "actress_name": name, "character_name": char, "film_title": film, "release_year": by, "bond_era": era,
        "nconst": n, "role_category": cat, "occupation": occ, "character_depth_score": depth,
        "has_independent_objective": flags[0], "professional_expertise": flags[1], "participates_in_climax": flags[2],
        "intelligence_or_combat_role": flags[3], "survives_film": flags[4],
        "age_at_bond": age, "age_group": age_group(age),
        "prior_career_years": (by - min(c[0] for c in pre)) if pre else 0,
        "pre_bond_credits": len(pre), "pre_bond_avg_rating": pr, "pre_bond_avg_score": avg_score(pre),
        "post_bond_credits_5y": len(p5), "post_bond_avg_rating_5y": avg_rating(p5),
        "post_bond_credits_lifetime": len(post), "post_bond_avg_rating_lifetime": pl,
        "post_bond_avg_score_lifetime": avg_score(post), "post_bond_active_years": act,
        "rating_delta_naive": round(pl - pr, 2) if pl is not None and pr is not None else None,
        "career_trajectory": trajectory(len(post), act), "character_description": desc,
    })

data.extend(added)
data.sort(key=lambda r: (r["release_year"], r["film_title"]))  # stable: keeps existing order within a year/film
with open(JSON_PATH, "w", encoding="utf-8", newline="\n") as f:
    json.dump(data, f, indent=2, ensure_ascii=False); f.write("\n")
json.dump(review, open(T / "needs_review.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("added", len(added), "total rows", len(data))
for a in added:
    print(" +", a["actress_name"], "|", a["film_title"], a["release_year"], "| age", a["age_at_bond"], "| pre", a["pre_bond_credits"], "post", a["post_bond_credits_lifetime"], a["career_trajectory"])
print("needs review:", review)
