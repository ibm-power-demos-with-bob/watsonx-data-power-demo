#!/usr/bin/env python3
"""Test the UI's /api/wxd-query-internal endpoint from RHEL itself."""
import paramiko

HOST    = "pvm01-4r13fr3k.p604.pok-systems.techzone.ibm.com"
USER    = "UHJ907M"
KEY     = r"C:\Users\029878866\Downloads\pvm-4r13fr3k-key.pem"

try:
    key = paramiko.Ed25519Key.from_private_key_file(KEY)
except Exception:
    key = paramiko.RSAKey.from_private_key_file(KEY)

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=USER, pkey=key)

def run(cmd, timeout=30):
    _, out, err = c.exec_command(cmd, timeout=timeout)
    out.channel.recv_exit_status()
    return (out.read().decode("utf-8","replace").strip()).encode("ascii","replace").decode("ascii")

# Test all pages load (200)
for path in ["/", "/live", "/outcome", "/sources"]:
    code = run(f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost:3000{path}")
    print(f"  {path}: HTTP {code}")

# Test the live API endpoint that hits Presto
print("\n--- /api/wxd-query-internal (live Presto query) ---")
result = run(
    "curl -s 'http://localhost:3000/api/wxd-query-internal' | head -c 500",
    timeout=45
)
print(result)

# Test detect-signals 
print("\n--- /api/detect-signals ---")
result = run(
    "curl -s 'http://localhost:3000/api/detect-signals' | head -c 400",
    timeout=30
)
print(result)

c.close()
