import paramiko
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from reservation import RHEL_HOST, SSH_USER, SSH_KEY

try:
    key = paramiko.Ed25519Key.from_private_key_file(SSH_KEY)
except Exception:
    key = paramiko.RSAKey.from_private_key_file(SSH_KEY)

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(RHEL_HOST, username=SSH_USER, pkey=key)

endpoints = [
    "http://localhost:3000/",
    "http://localhost:3000/live?scenario=cyber",
    "http://localhost:3000/sources",
    "http://localhost:3000/bond-investigation",
    "http://localhost:3000/api/bond-query?act=1",
    "http://localhost:3000/api/bond-query?act=4",
    "http://localhost:3000/api/bond-query?act=6",
]

print("=== SMOKE TESTING UI ON RHEL INSTANCE ===")
for ep in endpoints:
    _, out, _ = c.exec_command(f'curl -s -o /dev/null -w "HTTP %{{http_code}}" {ep}')
    code = out.read().decode().strip()
    print(f"  {ep} -> {code}")

c.close()
