#!/usr/bin/env python3
"""Full-restart PostgreSQL so listen_addresses='*' takes effect."""
import paramiko, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from reservation import RHEL_HOST as HOST, SSH_USER as USER, SSH_KEY as KEY

try:
    key = paramiko.Ed25519Key.from_private_key_file(KEY)
except Exception:
    key = paramiko.RSAKey.from_private_key_file(KEY)

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=USER, pkey=key)

def run(cmd):
    _, out, err = c.exec_command(cmd)
    rc = out.channel.recv_exit_status()
    stdout = out.read().decode("utf-8", errors="replace").strip()
    stderr = err.read().decode("utf-8", errors="replace").strip()
    combined = (stdout + " " + stderr).strip()
    print(f"  {combined[:300]}".encode("ascii","replace").decode("ascii"))
    return rc

print("Restarting PostgreSQL 16 (required for listen_addresses change)...")
run("sudo systemctl restart postgresql-16")
run("sudo systemctl is-active postgresql-16")

# Verify it's now listening on 0.0.0.0
run("sudo -u postgres psql -c \"SHOW listen_addresses;\"")
run("sudo ss -tlnp | grep 5432")
c.close()
print("Done.")
