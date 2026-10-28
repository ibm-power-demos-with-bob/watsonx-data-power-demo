"""Embed the Bond review corpus + one fixed query with a real Hugging Face model (runs on this laptop,
NOT on IBM Power). Output is static data loaded into PostgreSQL by 9-load-bond-data-pg.py.

Model: sentence-transformers/all-MiniLM-L6-v2 (384-dim). Vectors are L2-normalised, so the dot product of
two vectors equals their cosine similarity. Re-run only if the corpus or the query text changes.
"""
import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

MODEL = "sentence-transformers/all-MiniLM-L6-v2"
QUERY_ID = "Q1"
QUERY_TEXT = "A capable, independent woman who acts as Bond's professional equal rather than a decorative love interest"

DATA_DIR = Path(__file__).resolve().parent.parent / "demo-ui" / "src" / "data" / "bond"
corpus = json.loads((DATA_DIR / "bond_semantic_corpus.json").read_text(encoding="utf-8"))

model = SentenceTransformer(MODEL)
texts = [d["text"] for d in corpus]
doc_vecs = model.encode(texts, normalize_embeddings=True)
q_vec = model.encode([QUERY_TEXT], normalize_embeddings=True)[0]


def r(v):
    return [round(float(x), 6) for x in v]


out = {
    "model": MODEL,
    "dimensions": int(doc_vecs.shape[1]),
    "normalized": True,
    "computed_on": "developer laptop (static values, not computed on IBM Power)",
    "query": {"query_id": QUERY_ID, "query_text": QUERY_TEXT, "embedding": r(q_vec)},
    "documents": [{"doc_id": d["doc_id"], "embedding": r(v)} for d, v in zip(corpus, doc_vecs)],
}
(DATA_DIR / "bond_semantic_embeddings.json").write_text(json.dumps(out), encoding="utf-8")

sims = doc_vecs @ q_vec
print(f"model={MODEL} dims={out['dimensions']} docs={len(corpus)}")
for i in np.argsort(-sims):
    print(f"{sims[i]:.3f}  {corpus[i]['doc_id']:14s} {corpus[i]['actress_name']:20s} {corpus[i]['text'][:70]}")
