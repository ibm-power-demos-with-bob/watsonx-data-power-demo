"""Append short, attributed passages from Lisa Funnell's Flow article to the Bond corpus (idempotent).

Source: Funnell, L. (2019) "Nomi/No Me?: Race, Gender, and Power in No Time To Die", Flow 26.1.
https://www.flowjournal.org/2019/09/nomi-no-me/   (read in full on 2026-10-29)
Passages are verbatim, short, and linked. They are copyrighted scholarly commentary (NOT CC-licensed like the
Wikipedia rows), so they are kept as brief attributed quotations and labelled as a different source type.

After running: python setup/_embed_bond_corpus.py ; python setup/9-load-bond-data-pg.py
"""
import json
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "demo-ui" / "src" / "data" / "bond" / "bond_semantic_corpus.json"
URL = "https://www.flowjournal.org/2019/09/nomi-no-me/"

# (actress, character, film, year, verbatim passage)
PASSAGES = [
    ("Lashana Lynch", "Nomi", "No Time to Die", 2021,
     "Nomi is the first black woman to hold a \u201clicense to kill\u201d in the Bond franchise. Similar to Bond, Nomi has completed the elite training program and earned her position at MI6. As such, she is more like Bond (i.e., the heroic status quo) rather than an exception to the rule, and her role in No Time to Die challenges the longstanding tradition of defining heroism as white and male in the action genre."),
    ("Lashana Lynch", "Nomi", "No Time to Die", 2021,
     "Recently, some users have embarked on campaigns aimed at inundating social media platforms and especially movie review websites with enough negative comments to diminish the appeal of films, at times even before they have been released."),
    ("Lashana Lynch", "Nomi", "No Time to Die", 2021,
     "While progressive on the casting front, No Time to Die (much like Skyfall) might be regressive in its representation of women of color."),
    ("Gloria Hendry", "Rosie Carver", "Live and Let Die", 1973,
     "From Rosie Carver (Gloria Hendry) in Live and Let Die (Hamilton 1973) to May Day (Grace Jones) in A View to A Kill (Glen, 1985), black women are frequently hypersexualized and presented as disposable figures."),
    ("Grace Jones", "May Day", "A View to a Kill", 1985,
     "The Bond franchise in particular has a long history of depicting racial minorities and especially women of color in limited and stereotypical ways."),
    ("Naomie Harris", "Eve Moneypenny", "Skyfall", 2012,
     "While Skyfall (Mendes, 2012) features Naomi Harris as Eve Moneypenny, thus adding greater diversity to Bond\u2019s inner circle at MI6, she is introduced as a defunct field agent who is demoted for botching a mission and accidentally shooting Bond"),
    ("Naomie Harris", "Eve Moneypenny", "Skyfall", 2012,
     "unlike Bond who is given a redemption narrative in Skyfall and other films after making mistakes, Moneypenny is encouraged to take a desk job (and told by Bond that \u201cfieldwork is not for everyone\u201d)."),
]

corpus = json.loads(DATA.read_text(encoding="utf-8"))
corpus = [d for d in corpus if not d["doc_id"].startswith("FLOW_")]  # idempotent
for i, (actress, char, film, year, text) in enumerate(PASSAGES, 1):
    corpus.append({
        "doc_id": f"FLOW_2019_{i}",
        "actress_name": actress,
        "character_name": char,
        "film_title": film,
        "film_year": year,
        "source_year": 2019,
        "source_type": "Scholarly commentary",
        "publication": "L. Funnell, Flow 26.1 (2019)",
        "page_title": "Nomi/No Me?: Race, Gender, and Power in No Time To Die",
        "source_url": URL,
        "revision_id": None,
        "licence": "Copyright L. Funnell (short quote)",
        "retrieved_at": "2026-10-29",
        "text": text,
    })
DATA.write_text(json.dumps(corpus, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"corpus now {len(corpus)} docs ({len(PASSAGES)} Flow)")
