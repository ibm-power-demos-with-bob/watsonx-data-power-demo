#!/usr/bin/env python3
"""
Switch the Bond demo's primary data source WITHOUT rebuilding the UI.

  python setup/_set_bond_source.py ibmi   # IBM i audiences: career table read from Db2 for i
  python setup/_set_bond_source.py pg     # other audiences: PostgreSQL stands in (e.g. for Oracle on AIX)

Edits BOND_PRIMARY_SOURCE in ~/demo-ui/.env.local on the RHEL host and restarts
`next start`. ibmi mode requires setup/9b-load-bond-data-ibmi.py to have been run.
"""
import os
import sys
import time

import paramiko

sys.path.insert(0, os.path.dirname(__file__))
from reservation import RHEL_HOST, SSH_USER, SSH_KEY

mode = (sys.argv[1] if len(sys.argv) > 1 else "").lower()
if mode not in ("pg", "ibmi"):
    sys.exit(__doc__)

try:
    k = paramiko.Ed25519Key.from_private_key_file(SSH_KEY)
except Exception:
    k = paramiko.RSAKey.from_private_key_file(SSH_KEY)
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(RHEL_HOST, username=SSH_USER, pkey=k)

ENV = f"/home/{SSH_USER}/demo-ui/.env.local"
cmds = [
    f"sed -i '/^BOND_PRIMARY_SOURCE=/d' {ENV}",
    f"echo 'BOND_PRIMARY_SOURCE={mode}' >> {ENV}",
    "fuser -k 3000/tcp 2>/dev/null; sleep 2; echo stopped",
]
for cmd in cmds:
    _, o, _ = c.exec_command(cmd)
    o.channel.recv_exit_status()

# start detached so the SSH session can close
t = c.get_transport().open_session()
t.exec_command(f"cd /home/{SSH_USER}/demo-ui && nohup npm start </dev/null >/tmp/demo-ui.log 2>&1 &")
time.sleep(10)
_, o, _ = c.exec_command('curl -s -o /dev/null -w "HTTP %{http_code}" http://localhost:3000/bond-investigation')
print(f"Bond primary source = {mode}; UI restarted -> {o.read().decode().strip()}")
c.close()
