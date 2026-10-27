import paramiko
import sys
import os
import time

sys.path.insert(0, os.path.dirname(__file__))
from reservation import RHEL_HOST, SSH_USER, SSH_KEY

try:
    key = paramiko.Ed25519Key.from_private_key_file(SSH_KEY)
except Exception:
    key = paramiko.RSAKey.from_private_key_file(SSH_KEY)

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(RHEL_HOST, username=SSH_USER, pkey=key)

print("=== TESTING REAL PRESTO QUERY EXECUTION FOR ALL 6 ACTS ===")
for act in range(1, 7):
    url = f"http://localhost:3000/api/bond-query?act={act}"
    t0 = time.time()
    _, out, _ = c.exec_command(f'curl -s "{url}"')
    raw = out.read().decode().strip()
    elapsed = time.time() - t0
    if '"act":' in raw:
        print(f"  Act {act} -> OK (HTTP 200, elapsed: {elapsed:.2f}s, response size: {len(raw):,} bytes)")
    else:
        print(f"  Act {act} -> ERROR: {raw[:300]}")

c.close()
