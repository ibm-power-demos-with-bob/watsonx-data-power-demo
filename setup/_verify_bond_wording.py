"""Fetch all 6 Bond acts from the live UI and print row counts, summaryStats and takeaways."""
import json
import os
import sys
import time

import paramiko

sys.path.insert(0, os.path.dirname(__file__))
from reservation import RHEL_HOST, SSH_USER, SSH_KEY

try:
    key = paramiko.Ed25519Key.from_private_key_file(SSH_KEY)
except Exception:
    key = paramiko.RSAKey.from_private_key_file(SSH_KEY)

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(RHEL_HOST, username=SSH_USER, pkey=key)

for act in range(1, 7):
    t0 = time.time()
    _, out, _ = c.exec_command(f'curl -s "http://localhost:3000/api/bond-query?act={act}"')
    raw = out.read().decode()
    try:
        d = json.loads(raw)
    except Exception:
        print(f"Act {act} -> ERROR: {raw[:300]}")
        continue
    if "error" in d:
        print(f"Act {act} -> ERROR: {d['error'][:300]}")
        continue
    print(f"\n=== Act {act}: {d['title']}  rows={len(d['rows'])}  {time.time()-t0:.1f}s")
    for k, v in d["summaryStats"].items():
        print(f"  {k}: {v}")
    print(f"  takeaway: {d['businessInsight']['bondTakeaway']}")
    if act in (5, 6):
        print(f"  sample row: {json.dumps(d['rows'][0], ensure_ascii=False)[:300]}")
c.close()
