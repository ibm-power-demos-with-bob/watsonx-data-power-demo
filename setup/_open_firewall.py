#!/usr/bin/env python3
"""Open firewall port 3000 on RHEL and verify the UI is accessible externally."""
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

def run(cmd, timeout=15):
    _, out, err = c.exec_command(cmd, timeout=timeout)
    out.channel.recv_exit_status()
    return (out.read().decode("utf-8","replace").strip() + err.read().decode("utf-8","replace").strip()).encode("ascii","replace").decode("ascii")

print("--- Opening firewall port 3000 ---")
print(run("sudo firewall-cmd --zone=public --add-port=3000/tcp --permanent 2>&1"))
print(run("sudo firewall-cmd --reload 2>&1"))
print(run("sudo firewall-cmd --list-ports 2>&1"))

print("\n--- Get RHEL public IP ---")
print(run("curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}'"))

c.close()
