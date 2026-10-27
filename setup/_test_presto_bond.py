import sys
import os
import requests
import json
import base64

sys.path.insert(0, os.path.dirname(__file__))
from reservation import (
    WXD_HOST,
    WXD_PRESTO_PORT,
    WXD_API_USER,
    WXD_API_PASS,
)

url = f"https://{WXD_HOST}:{WXD_PRESTO_PORT}/v1/statement"
creds = base64.b64encode(f"{WXD_API_USER}:{WXD_API_PASS}".encode()).decode()
headers = {
    "Authorization": f"Basic {creds}",
    "X-Presto-User": WXD_API_USER,
    "X-Presto-Source": "bond-test",
    "Content-Type": "text/plain",
}

sql = "SELECT actress_name, film_title, release_year, character_depth_score, career_trajectory FROM pg_olist.public.bond_career_analysis LIMIT 5"
print(f"Submitting query to Presto: {sql}")

resp = requests.post(url, headers=headers, data=sql, verify=False, timeout=30)
state = resp.json()
columns = []
all_rows = []

next_uri = state.get("nextUri")

while next_uri:
    if "columns" in state and not columns:
        columns = [c["name"] for c in state["columns"]]
    if "data" in state:
        all_rows.extend(state["data"])

    poll_resp = requests.get(next_uri, headers=headers, verify=False, timeout=30)
    state = poll_resp.json()
    if state.get("stats", {}).get("state") in ("FINISHED", "FAILED"):
        if "data" in state:
            all_rows.extend(state["data"])
        break
    next_uri = state.get("nextUri")

print(f"Columns: {columns}")
print(f"Retrieved {len(all_rows)} rows from Presto live:")
for r in all_rows:
    print(" ", r)
