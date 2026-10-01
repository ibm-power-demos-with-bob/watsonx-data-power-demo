#!/usr/bin/env python3
"""Check UI status and smoke test on RHEL."""
import paramiko, time, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from reservation import RHEL_HOST as HOST, SSH_USER as USER, SSH_KEY as KEY

REMOTE  = f"/home/{USER}/demo-ui"

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

# Check if port 3000 is in use
print("--- Port 3000 ---")
print(run("fuser 3000/tcp 2>&1 || echo 'NOT LISTENING'"))

# Check process
print("\n--- npm/node processes ---")
print(run("pgrep -af 'node|next' 2>&1 | head -5"))

# Tail the log
print("\n--- /tmp/demo-ui.log (last 20 lines) ---")
print(run("tail -20 /tmp/demo-ui.log 2>/dev/null || echo 'no log yet'"))

# If not running, start it now (fire-and-forget, no output wait)
not_running = "NOT LISTENING" in run("fuser 3000/tcp 2>&1 || echo 'NOT LISTENING'")
if not_running:
    print("\n--- Starting UI ---")
    # Use a here-doc approach so the channel closes immediately
    c.exec_command(f"cd {REMOTE} && nohup npm start > /tmp/demo-ui.log 2>&1 & echo started")
    time.sleep(20)
    print(run("tail -10 /tmp/demo-ui.log 2>/dev/null"))

# Smoke test
print("\n--- Smoke test ---")
print(run("curl -s -o /dev/null -w 'HTTP %{http_code}' http://localhost:3000/"))

c.close()
