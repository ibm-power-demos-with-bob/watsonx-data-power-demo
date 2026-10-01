#!/usr/bin/env python3
"""Dump ALL Satellite connector log messages for manual inspection."""
import paramiko, json, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from reservation import RHEL_HOST as HOST, SSH_USER as USER, SSH_KEY as KEY

try:
    key = paramiko.Ed25519Key.from_private_key_file(KEY)
except Exception:
    key = paramiko.RSAKey.from_private_key_file(KEY)

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=USER, pkey=key)

_, out, _ = c.exec_command("sudo podman logs --tail 80 satellite-connector 2>&1", timeout=15)
logs = out.read().decode("utf-8", errors="replace")
c.close()

for line in logs.splitlines():
    try:
        obj = json.loads(line)
        t     = obj.get("time", "")
        msg   = obj.get("msg", "")
        msgid = obj.get("msgid", "")
        lvl   = obj.get("level", 0)
        print(f"{t[11:19]} L{lvl:2d} [{msgid:8s}] {msg}".encode("ascii","replace").decode("ascii"))
    except Exception:
        if line.strip():
            print(f"RAW: {line[:120]}".encode("ascii","replace").decode("ascii"))
