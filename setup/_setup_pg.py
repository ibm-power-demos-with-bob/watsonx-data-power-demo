#!/usr/bin/env python3
"""Install PostgreSQL olist DB + load data on RHEL via SSH."""
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

def run(cmd, label=""):
    _, out, err = c.exec_command(cmd)
    rc = out.channel.recv_exit_status()
    stdout = out.read().decode("utf-8", errors="replace").strip()
    stderr = err.read().decode("utf-8", errors="replace").strip()
    tag = f"[{label}]" if label else ""
    if stdout:
        print(f"{tag} OUT: {stdout[:500]}")
    if stderr:
        print(f"{tag} ERR: {stderr[:300]}")
    if rc != 0:
        print(f"{tag} EXIT CODE: {rc}")
    return rc

print("--- Creating edbadmin user ---")
run("sudo -u postgres psql -c \"CREATE USER edbadmin WITH SUPERUSER PASSWORD 'edbadmin';\"", "user")

print("--- Creating olist database ---")
run("sudo -u postgres psql -c \"CREATE DATABASE olist OWNER edbadmin;\"", "db")

print("--- Testing connection ---")
run("PGPASSWORD=edbadmin psql -h localhost -U edbadmin -d olist -c '\\conninfo'", "conntest")

c.close()
print("Done.")
