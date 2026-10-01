#!/usr/bin/env python3
"""Check what's actually listening and reachable on the RHEL VM."""
import paramiko

HOST = "pvm01-4r13fr3k.p604.pok-systems.techzone.ibm.com"
USER = "UHJ907M"
KEY  = r"C:\Users\029878866\Downloads\pvm-4r13fr3k-key.pem"

try:
    key = paramiko.Ed25519Key.from_private_key_file(KEY)
except Exception:
    key = paramiko.RSAKey.from_private_key_file(KEY)

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=USER, pkey=key)

def run(cmd, timeout=10):
    _, out, err = c.exec_command(cmd, timeout=timeout)
    out.channel.recv_exit_status()
    return (out.read().decode("utf-8","replace").strip()).encode("ascii","replace").decode("ascii")

# What is the VM's actual IP and FQDN?
print("--- Network interfaces ---")
print(run("ip addr show | grep 'inet ' | grep -v 127"))

print("\n--- Hostname / FQDN ---")
print(run("hostname -f 2>/dev/null || hostname"))

print("\n--- All listening TCP ports ---")
print(run("sudo ss -tlnp | grep LISTEN"))

print("\n--- Firewall status ---")
print(run("sudo firewall-cmd --state 2>&1"))
print(run("sudo iptables -L INPUT --line-numbers -n 2>&1 | head -20"))

print("\n--- SELinux ---")
print(run("getenforce 2>/dev/null"))

# Can the VM reach itself on 3000 via its own FQDN (tests external routing)?
print("\n--- Curl via FQDN (tests external routing) ---")
print(run(f"curl -s -o /dev/null -w 'HTTP %{{http_code}}' http://{HOST}:3000/ --connect-timeout 5 2>&1"))

c.close()
