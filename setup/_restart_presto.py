#!/usr/bin/env python3
"""Restart ibm-lh-presto on the Dev Image so new catalogs are loaded."""
import paramiko, time
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reservation as _r

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(_r.WXD_HOST, port=_r.WXD_SSH_PORT, username=_r.WXD_SSH_USER, password=_r.WXD_SSH_PASS)

def run(cmd, timeout=60):
    _, out, err = c.exec_command(cmd, timeout=timeout)
    rc = out.channel.recv_exit_status()
    stdout = out.read().decode("utf-8", errors="replace").strip()
    stderr = err.read().decode("utf-8", errors="replace").strip()
    combined = (stdout + " " + stderr).strip()
    print(f"  {combined[:400]}".encode("ascii","replace").decode("ascii"))
    return rc

print("--- Checking containers ---")
run("sudo docker ps --format '{{.Names}} {{.Status}}' | grep -E 'presto|lh'")

print("\n--- Restarting ibm-lh-presto ---")
run("sudo docker restart ibm-lh-presto", timeout=120)

print("\nWaiting 30s for Presto to come back up...")
time.sleep(30)

print("\n--- Checking Presto is up ---")
run("sudo docker ps --filter name=ibm-lh-presto --format '{{.Names}} {{.Status}}'")

c.close()
print("Done.")
