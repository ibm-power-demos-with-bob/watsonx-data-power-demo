#!/usr/bin/env python3
"""Query catalog and catalog_engine tables, and check ams policies."""
import paramiko
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reservation as _r

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(_r.WXD_HOST, port=_r.WXD_SSH_PORT, username=_r.WXD_SSH_USER, password=_r.WXD_SSH_PASS)

def run(cmd, timeout=30):
    _, out, err = c.exec_command(cmd, timeout=timeout)
    out.channel.recv_exit_status()
    stdout = out.read().decode("utf-8", errors="replace").strip()
    stderr = err.read().decode("utf-8", errors="replace").strip()
    print((stdout + (" ERR:" + stderr[:300] if stderr else ""))[:1200].encode("ascii","replace").decode("ascii"))

print("--- catalog table ---")
run("sudo docker exec ibm-lh-postgres psql -U admin -d ibm_lh_repo -c 'SELECT * FROM catalog;' 2>&1")

print("\n--- catalog_engine table ---")
run("sudo docker exec ibm-lh-postgres psql -U admin -d ibm_lh_repo -c 'SELECT * FROM catalog_engine;' 2>&1")

print("\n--- engine table ---")
run("sudo docker exec ibm-lh-postgres psql -U admin -d ibm_lh_repo -c 'SELECT * FROM engine;' 2>&1")

print("\n--- ams policies ---")
run("sudo docker exec ibm-lh-postgres psql -U admin -d ibm_lh_repo -c 'SELECT * FROM ams_0000_0000_0000_0000 LIMIT 10;' 2>&1")

c.close()
