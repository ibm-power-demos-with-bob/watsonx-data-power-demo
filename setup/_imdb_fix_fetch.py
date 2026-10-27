#!/usr/bin/env python3
"""
Diagnostic/fix helper: stream IMDb datasets and extract credits for specific nconsts.
Writes %TEMP%/imdb/extract.json. Used to correct mismatched nconsts in
bond_actress_career_analysis.json (Grace Jones, Denise Richards, etc.).
"""
import gzip
import io
import json
import os
import urllib.request

OUT = os.path.join(os.environ.get("TEMP", "."), "imdb", "extract.json")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

# corrected ids + calibration ids (Maud Adams 189 credits, Britt Ekland 246)
IDS = {
    "nm0005063": "Grace Jones",
    "nm0000612": "Denise Richards",
    "nm0005412": "Jane Seymour",
    "nm0000819": "Barbara Bach",
    "nm0000938": "Daniela Bianchi",
    "nm0000726": "Maud Adams (calibration)",
    "nm0001180": "Britt Ekland (calibration)",
}
BASE = "https://datasets.imdbws.com/"


def stream(name):
    req = urllib.request.Request(BASE + name, headers={"User-Agent": "Mozilla/5.0"})
    resp = urllib.request.urlopen(req, timeout=120)
    return io.TextIOWrapper(gzip.GzipFile(fileobj=resp), encoding="utf-8", newline="")


result = {"names": {}, "principals": {}, "titles": {}}

print("name.basics...", flush=True)
for line in stream("name.basics.tsv.gz"):
    nid = line[:9] if line.startswith("nm") else None
    if nid is None:
        continue
    nid = line.split("\t", 1)[0]
    if nid in IDS:
        result["names"][nid] = line.rstrip("\n").split("\t")
        if len(result["names"]) == len(IDS):
            break

print("title.principals...", flush=True)
tids = set()
for line in stream("title.principals.tsv.gz"):
    parts = line.rstrip("\n").split("\t")
    if len(parts) > 3 and parts[2] in IDS:
        result["principals"].setdefault(parts[2], []).append(parts[0:2] + parts[3:4])
        tids.add(parts[0])

print("title.basics + ratings for", len(tids), "titles", flush=True)
for line in stream("title.basics.tsv.gz"):
    parts = line.split("\t", 6)
    if parts[0] in tids:
        result["titles"][parts[0]] = {"type": parts[1], "title": parts[2], "year": parts[5]}
for line in stream("title.ratings.tsv.gz"):
    parts = line.rstrip("\n").split("\t")
    if parts[0] in result["titles"]:
        result["titles"][parts[0]]["rating"] = parts[1]
        result["titles"][parts[0]]["votes"] = parts[2]

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f)
print("DONE", OUT, flush=True)
