#!/usr/bin/env python3
"""Configure PostgreSQL 16 on RHEL for remote access (Satellite connector)."""
import paramiko, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from reservation import RHEL_HOST as HOST, SSH_USER as USER, SSH_KEY as KEY
PGDATA = "/var/lib/pgsql/16/data"

try:
    key = paramiko.Ed25519Key.from_private_key_file(KEY)
except Exception:
    key = paramiko.RSAKey.from_private_key_file(KEY)

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=USER, pkey=key)

def run(cmd, label=""):
    _, out, err = c.exec_command(cmd)
    rc = out.channel.recv_exit_status()
    stdout = out.read().decode("utf-8", errors="replace").strip()
    stderr = err.read().decode("utf-8", errors="replace").strip()
    if stdout: print(f"  [{label}] {stdout[:400]}".encode("ascii", "replace").decode("ascii"))
    if stderr: print(f"  [{label} ERR] {stderr[:300]}".encode("ascii", "replace").decode("ascii"))
    return rc

# 1. Set listen_addresses = '*'
print("Setting listen_addresses = '*' ...")
run(f"sudo sed -i \"s/#listen_addresses = 'localhost'/listen_addresses = '*'/\" {PGDATA}/postgresql.conf", "listen")
run(f"sudo grep listen_addresses {PGDATA}/postgresql.conf", "verify")

# 2. Add md5 auth line for all IPs in pg_hba.conf (if not already there)
print("Updating pg_hba.conf for md5 auth ...")
hba_line = "host    all             all             0.0.0.0/0               md5"
check_cmd = f"sudo grep -c '0.0.0.0/0' {PGDATA}/pg_hba.conf"
_, out, _ = c.exec_command(check_cmd)
count = out.read().decode().strip()
if count == "0":
    run(f"echo '{hba_line}' | sudo tee -a {PGDATA}/pg_hba.conf", "hba")
else:
    print("  [hba] md5 line already present, skipping.")

# 3. Reload PostgreSQL
print("Reloading PostgreSQL ...")
run("sudo systemctl reload postgresql-16", "reload")
run("sudo systemctl is-active postgresql-16", "status")

c.close()
print("Done.")
