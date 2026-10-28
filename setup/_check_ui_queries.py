#!/usr/bin/env python3
"""Exercise the real demo flow on RHEL: inject-signal -> POST /api/alerts (live federated Presto query)."""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paramiko
from reservation import RHEL_HOST, SSH_USER, SSH_KEY

k = paramiko.RSAKey.from_private_key_file(SSH_KEY)
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(RHEL_HOST, username=SSH_USER, pkey=k)

def sh(cmd, t=120):
    _, o, e = c.exec_command(cmd, timeout=t)
    o.channel.recv_exit_status()
    return (o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")).strip()

H = "-H 'Content-Type: application/json'"
for scenario in ("supplier-cyber-incident", "eu-wildfire"):
    t0 = time.time()
    print(f"[{scenario}] inject:", sh(f"curl -s -m 100 -X POST http://localhost:3000/api/inject-signal {H} -d '{{\"scenario\":\"{scenario}\"}}' | head -c 300"))
    print(f"[{scenario}] alerts:", sh(f"curl -s -m 100 -X POST http://localhost:3000/api/alerts {H} -d '{{\"scenario\":\"{scenario}\"}}' | head -c 500"))
    print(f"[{scenario}] elapsed {time.time()-t0:.1f}s\n")
c.close()

