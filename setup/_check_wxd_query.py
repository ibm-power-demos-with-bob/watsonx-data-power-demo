#!/usr/bin/env python3
"""Test detect-signals with a POST body to trigger the federated query."""
import paramiko
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reservation as _r

try:
    key = paramiko.Ed25519Key.from_private_key_file(_r.SSH_KEY)
except Exception:
    key = paramiko.RSAKey.from_private_key_file(_r.SSH_KEY)

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(_r.RHEL_HOST, username=_r.SSH_USER, pkey=key)

_, out, _ = c.exec_command(
    """curl -s -X POST http://localhost:3000/api/detect-signals \
       -H 'Content-Type: application/json' \
       -d '{"scenario":"cyber"}' 2>&1 | python3 -c "import sys,json; d=json.load(sys.stdin); print('ok:', d.get('ok')); [print(' -', a.get('title','?'), '|', str(a.get('value','?'))[:60]) for a in d.get('detections',[])]" 2>&1""",
    timeout=60
)
out.channel.recv_exit_status()
result = out.read().decode("utf-8","replace").strip()
print(result.encode("ascii","replace").decode("ascii"))
c.close()
