#!/usr/bin/env python3
"""Derive the Bond character 'agency' flags and depth score from James Bond Wiki (Fandom) text.

Input : demo-ui/src/data/bond/bond_fandom_characters.json   (from _fetch_fandom_characters.py)
Output: updates bond_actress_career_analysis.json in place:
          character_depth_score          <- now derived from the text (formula below)
          has_independent_objective, professional_expertise, participates_in_climax,
          intelligence_or_combat_role, survives_film   <- now derived from the text
          editorial_depth_score          <- the old hand-typed score, kept once for comparison
          agency_source / agency_confidence / agency_evidence_chars / agency_evidence / fandom_page_url
        and appends Fandom passages to bond_semantic_corpus.json (idempotent: FANDOM_* rows replaced).

Method (a transparent keyword rubric, NOT a language model and NOT a gold standard):
  A sentence is "about her" if it contains she/her or her character's name.
  Flag evidence = the first such sentence matching the flag's pattern (kept so a reader can audit it).
  depth = 1 + 2*independent_objective + 2*professional_expertise + 2*climax + 2*intel_or_combat + 1*survives  (1..10)
  Confidence is the amount of text found: High >= 3000 chars, Medium >= 1000, Low < 1000.
  Rows with no wiki page keep their editorial values and are labelled "Editorial only".

After running: python setup/_embed_bond_corpus.py ; python setup/9-load-bond-data-pg.py ; python setup/9b-load-bond-data-ibmi.py
"""
import json, re, sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "demo-ui" / "src" / "data" / "bond"
CAREER, FANDOM, CORPUS = (DATA / n for n in
                          ("bond_actress_career_analysis.json", "bond_fandom_characters.json", "bond_semantic_corpus.json"))

# Rubric: the character must be the grammatical SUBJECT of the action (subject = she / her first name / surname,
# followed within ~25 characters, no comma or full stop between, by the verb). This stops "Bond fought off the men"
# from counting for her. Sentences are taken from the Biography and Personality sections only.
OBJ_VERBS = (r"(?:seeks?|sought|plans?|planned|intends?|vows?|vowed|swears?|swore|sets? out|investigat\w+|infiltrat\w+|"
             r"tracks? down|tracked down|hunts?|hunted|avenges?|avenged|wants? to|wanted to|decides? to|decided to|"
             r"tries to|tried to|attempts? to|attempted to|steals?|stole|smuggl\w+|defects?|defected|betrays?|betrayed|"
             r"manipulat\w+|orchestrat\w+|kidnaps?|kidnapped|blackmails?|poisons?|murders?|murdered|lures?|lured|"
             r"takes? over|took over|is determined|was determined|is out to|works? to|worked to|insists?|insisted|"
             r"refuses?|refused|volunteers?|volunteered|leads?|led|organi[sz]\w+|devises?|devised|schemes?|plots?|plotted)")
COMBAT_VERBS = (r"(?:kills?|killed|shoots?|shot|fights?|fought|stabs?|stabbed|strangl\w+|assassinat\w+|attacks?|attacked|"
                r"ambush\w*|wrestl\w+|punch\w*|overpower\w*|fires|fired|blows? up|detonat\w+|duels?|dueled|battles?|"
                r"disarms?|disarmed|knocks? out|knocked out|slices|slashes|crushes|hijack\w*|fends? off|beats?)")
CLIMAX_VERBS = (r"(?:rescues?|rescued|saves?|saved|destroys?|destroyed|defeats?|defeated|stops?|stopped|deactivat\w+|"
                r"disarms?|disarmed|confronts?|confronted|captures?|captured|escapes?|escaped|kills?|killed|shoots?|shot|"
                r"fights?|fought|flees?|fled|sabotag\w+|triggers?|triggered|launch\w+|sacrific\w+|fires|fired|"
                r"helps?|helped|joins?|joined|blows? up|infiltrat\w+|takes? down|took down|pilots?|piloted|flies|flew)")
# Expertise = how the page introduces her (infobox occupation + first 3 lead sentences), NOT every mention in the plot.
EXPERT_WORDS = re.compile(r"\b(archaeolog\w+|physicist|scientist|nuclear|geolog\w+|doctor|dr\.|pilot|agent|operative|assassin|"
                          r"officer|colonel|major|captain|analyst|programmer|astronaut|journalist|lawyer|psychiatrist|"
                          r"surgeon|expert|specialist|trained|KGB|CIA|MI6|NSA|secret service|intelligence|commander|"
                          r"cryptographer|engineer|diver|ornithologist|bodyguard|hitwoman|enforcer|hacker|detective|"
                          r"inspector|chemist|professor|spy|henchwoman|killer)\b", re.I)
DEATH_PASSIVE = (r"\b(?:killed|murdered|shot|stabbed|strangled|drowned|executed|poisoned|suffocated|crushed|eaten|"
                 r"eviscerated|slain|gunned down|run over|dies|died|perishes|is dead|dead)")

TITLES = {"dr", "dr.", "major", "colonel", "miss", "lady", "countess", "agent", "the", "of", "von", "di", "de"}


def name_tokens(character):
    base = re.sub(r"\(.*?\)", "", character)
    toks = [t.strip("'\"") for t in re.split(r"[\s/]+", base) if t and t.lower().strip(".") not in TITLES and len(t) > 2]
    return toks[:1] + toks[-1:] if len(toks) > 1 else toks


def sentences(text):
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\"'])", text.replace("\n", " "))
    return [p.strip() for p in parts if len(p.strip()) > 20]


def trim(s, n=240):
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[: n - 1].rsplit(" ", 1)[0] + "…"


def subj_pattern(toks):
    names = "|".join(re.escape(t) for t in toks)
    return r"(?:\bshe\b|\b(?:" + names + r")\b(?!'s|’s))" if names else r"\bshe\b"


def subject_verb(verbs, toks, sents):
    """First sentence where the character is the subject of one of `verbs` (not a negated or passive form)."""
    pat = re.compile(subj_pattern(toks) + r"(?:\s+(?:then|also|later|soon|eventually|finally|quickly|successfully|"
                     r"secretly|brutally|angrily|and))*\s+" + verbs + r"\b", re.I)
    pat2 = re.compile(subj_pattern(toks) + r"[^.;,'’]{0,25}?\b" + verbs + r"\b", re.I)
    for s in sents:
        m = pat.search(s) or pat2.search(s)
        if m and not re.search(r"\b(?:not|never|unable to|fails? to)\s+\w*\s*$", s[: m.start()][-25:], re.I):
            return s
    return None


def analyse(rec):
    toks = name_tokens(rec["character_name"])
    bio = rec["biography"]
    sents = sentences(bio) or sentences(rec["lead"])
    pers = sentences(rec["personality"])
    pool = sents + pers
    ev = {}
    ev["independent_objective"] = subject_verb(OBJ_VERBS, toks, pool)
    intro = sentences(rec["lead"])[:3]
    intro_txt = " ".join(intro)
    occ = rec["infobox"].get("occupation", "")
    m = EXPERT_WORDS.search(occ) or EXPERT_WORDS.search(intro_txt)
    ev["professional_expertise"] = (("Infobox occupation: " + occ) if EXPERT_WORDS.search(occ)
                                    else (next((s for s in intro if EXPERT_WORDS.search(s)), None)))
    ev["intel_or_combat"] = subject_verb(COMBAT_VERBS, toks, pool)
    tail = sents[int(len(sents) * 0.7):] if len(sents) >= 4 else []
    ev["climax"] = subject_verb(CLIMAX_VERBS, toks, tail)
    death_pat = re.compile(subj_pattern(toks) + r"[^.;]{0,40}?\b(?:is|was|gets|then|are)\b[^.;]{0,25}?\b" + DEATH_PASSIVE + r"\b|"
                           + subj_pattern(toks) + r"\s+(?:dies|died|perishes|perished|drowns|drowned|is dead|commits suicide|resigns (?:herself|himself) to death)\b|\b(?:her|their) (?:death|murder)\b|\bdeath of (?:" + "|".join(re.escape(t) for t in (toks or ["she"])) + r")\b|\b(?:kills?|killing|killed|murders?) (?:her(?!\s+(?:family|father|mother|parents|sister|brother|husband|lover|friend|boyfriend|son|daughter))|"
                           + "|".join(re.escape(t) for t in (toks or ["she"])) + r")\b", re.I)
    death = next((s for s in pool if death_pat.search(s)), None)
    flags = {
        "has_independent_objective": bool(ev["independent_objective"]),
        "professional_expertise": bool(ev["professional_expertise"]),
        "participates_in_climax": bool(ev["climax"]),
        "intelligence_or_combat_role": bool(ev["intel_or_combat"]),
        "survives_film": not death,
    }
    ev["dies"] = death
    return flags, ev, len(bio) + len(rec["personality"])

def depth(f):
    return 1 + 2 * f["has_independent_objective"] + 2 * f["professional_expertise"] + 2 * f["participates_in_climax"] \
        + 2 * f["intelligence_or_combat_role"] + 1 * f["survives_film"]


def confidence(chars):
    return "High" if chars >= 3000 else "Medium" if chars >= 1000 else "Low"


def best_passage(rec):
    """One short passage per character for the Act 5 corpus: Personality if present, else the most agency-dense paragraph."""
    if len(rec["personality"]) >= 200:
        text = rec["personality"]
    else:
        paras = [p for p in re.split(r"\n\s*\n", rec["biography"]) if len(p) > 120]
        if not paras:
            return None
        toks = name_tokens(rec["character_name"])
        who = r"\b(?:she|her|" + "|".join(re.escape(t) for t in toks) + r")\b" if toks else r"\bshe\b"
        paras.sort(key=lambda p: -(len(re.findall(who, p, re.I)) + 2 * len(re.findall(OBJ_VERBS, p, re.I)) + len(re.findall(COMBAT_VERBS, p, re.I))))
        text = paras[0]
    out, total = [], 0
    for s in sentences(text.replace("\n\n", " ")):
        if total + len(s) > 700:
            break
        out.append(s)
        total += len(s) + 1
    return " ".join(out) if total > 120 else None


def main():
    career = json.loads(CAREER.read_text(encoding="utf-8"))
    fandom = {(r["nconst"], r["film_title"], r["character_name"]): r for r in json.loads(FANDOM.read_text(encoding="utf-8"))}
    corpus = [d for d in json.loads(CORPUS.read_text(encoding="utf-8")) if not d["doc_id"].startswith("FANDOM_")]
    added = 0
    for row in career:
        rec = fandom[(row["nconst"], row["film_title"], row["character_name"])]
        row.setdefault("editorial_depth_score", row["character_depth_score"])  # keep the original hand-typed score once
        if not rec["biography"] or not rec["page_title"]:
            row.update(agency_source="Editorial only", agency_confidence="Editorial only", agency_evidence_chars=0,
                       agency_evidence="", fandom_page_url=rec["page_url"] or "")
            continue
        flags, ev, chars = analyse(rec)
        row.update(flags)
        row["character_depth_score"] = depth(flags)
        row.update(agency_source="James Bond Wiki (Fandom) text", agency_confidence=confidence(chars),
                   agency_evidence_chars=chars, fandom_page_url=rec["page_url"],
                   agency_evidence=" | ".join(f"{k}: {trim(v)}" for k, v in ev.items() if v))
        passage = best_passage(rec)
        if passage:
            added += 1
            corpus.append({
                "doc_id": f"FANDOM_{row['nconst']}_{row['release_year']}_{added}",
                "actress_name": row["actress_name"], "character_name": row["character_name"],
                "film_title": row["film_title"], "film_year": row["release_year"], "source_year": 2026,
                "source_type": "Fandom character page", "publication": f"James Bond Wiki: {rec['page_title']}",
                "page_title": rec["page_title"], "source_url": rec["page_url"], "revision_id": rec["revision_id"],
                "licence": "CC BY-SA 3.0", "retrieved_at": rec["retrieved_at"], "text": passage})
    CAREER.write_text(json.dumps(career, ensure_ascii=False, indent=2), encoding="utf-8")
    CORPUS.write_text(json.dumps(corpus, ensure_ascii=False, indent=2), encoding="utf-8")

    from collections import Counter
    print("rows", len(career), "| confidence", dict(Counter(r["agency_confidence"] for r in career)))
    print("corpus now", len(corpus), "docs (+", added, "Fandom )")
    print("score distribution new:", sorted(Counter(r["character_depth_score"] for r in career).items()))
    print("score distribution old:", sorted(Counter(r["editorial_depth_score"] for r in career).items()))
    d = [r["character_depth_score"] - r["editorial_depth_score"] for r in career]
    print("mean diff (new-old): %.2f, abs diff >=4: %d" % (sum(d) / len(d), sum(1 for x in d if abs(x) >= 4)))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()

