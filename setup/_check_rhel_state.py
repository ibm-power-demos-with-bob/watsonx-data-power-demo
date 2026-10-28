#!/usr/bin/env python3
"""Check RHEL state: PostgreSQL installed/running? podman? olist DB? Satellite agent?"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paramiko
from reservation import RHEL_HOST, SSH_USER, SSH_KEY

k = paramiko.RSAKey.from_private_key_file(SSH_KEY)
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(RHEL_HOST, username=SSH_USER, pkey=k, timeout=30)
print("Connected to", RHEL_HOST)

for label, cmd in [
    ("os", "cat /etc/redhat-release; uname -m"),
    ("postgres pkg", "rpm -qa | grep -i postgresql | head -5"),
    ("postgres svc", "systemctl is-active postgresql-16 2>&1; systemctl is-active postgresql 2>&1"),
    ("olist db", "sudo -u postgres psql -lqt 2>&1 | grep -i olist"),
    ("podman", "sudo podman ps 2>&1 | head -5"),
    ("data dir", "ls -la ~ /tmp | head -30"),
    ("disk", "df -h / /tmp | cat"),
]:
    _, so, se = c.exec_command(cmd)
    so.channel.recv_exit_status()
    print(f"\n[{label}]\n" + (so.read().decode("utf-8", "replace") + se.read().decode("utf-8", "replace")).strip()[:800])
c.close()
