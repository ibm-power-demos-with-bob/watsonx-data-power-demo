#!/usr/bin/env python3
"""
Deploy the demo-ui Next.js app to RHEL.

Steps:
  1. Check / install Node.js 20 LTS
  2. rsync demo-ui/ source to RHEL (excluding node_modules/.next)
  3. Write .env.local with current session credentials
  4. npm install (if needed)
  5. Kill any existing process on port 3000
  6. Start `npm run build && npm start` in background
  7. Smoke-test HTTP 200 on :3000
"""
import paramiko, time, stat, sys, os
from pathlib import Path
from io import StringIO

sys.path.insert(0, os.path.dirname(__file__))
from reservation import (RHEL_HOST as HOST, SSH_USER as USER, SSH_KEY as KEY,
                         WXD_HOST, WXD_PRESTO_PORT, WXD_API_USER, WXD_API_PASS)

REMOTE = f"/home/{USER}/demo-ui"

ENV_CONTENT = f"""\
WXD_PRESTO_HOST={WXD_HOST}
WXD_PRESTO_PORT={WXD_PRESTO_PORT}
WXD_PRESTO_SCHEME=https
WXD_PRESTO_USER={WXD_API_USER}
WXD_PRESTO_PASSWORD={WXD_API_PASS}
WXD_PG_CATALOG=pg_olist
WXD_IBMI_CATALOG=ibmi_olist
"""

try:
    key = paramiko.Ed25519Key.from_private_key_file(KEY)
except Exception:
    key = paramiko.RSAKey.from_private_key_file(KEY)

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=USER, pkey=key)

def run(cmd, timeout=120, label=""):
    _, out, err = c.exec_command(cmd, timeout=timeout)
    rc = out.channel.recv_exit_status()
    stdout = out.read().decode("utf-8", errors="replace").strip()
    stderr = err.read().decode("utf-8", errors="replace").strip()
    tag = f"[{label}] " if label else ""
    if stdout: print(f"  {tag}{stdout[:600]}".encode("ascii","replace").decode("ascii"))
    if stderr and rc != 0: print(f"  {tag}ERR: {stderr[:400]}".encode("ascii","replace").decode("ascii"))
    return rc, stdout

# ── 1. Check / install Node.js ──────────────────────────────────────────────
# NodeSource does NOT support ppc64le — use RHEL AppStream repo (Node 16).
# Node 16 works fine with Next.js 14 on ppc64le Power10/11.
print("=== Step 1: Node.js ===")
rc, ver = run("node --version 2>/dev/null || echo MISSING", label="node")
if "MISSING" in ver or rc != 0:
    print("  Node not found — installing from RHEL AppStream repo (ppc64le)...")
    run("sudo dnf install -y nodejs npm 2>&1 | tail -5", timeout=180, label="node-install")
    run("node --version", label="node-ver")
else:
    print(f"  Node already installed: {ver}")

# ── 2. Upload demo-ui source via SFTP ────────────────────────────────────────
print("\n=== Step 2: Upload demo-ui source ===")
run(f"mkdir -p {REMOTE}", label="mkdir")

LOCAL_UI = Path("demo-ui")
sftp = c.open_sftp()

def sftp_mkdir_p(sftp, remote_path):
    """Create remote_path recursively, skipping parts that already exist or are root."""
    # Only create from the REMOTE base dir onwards — never try to create /home or /
    parts = remote_path.rstrip("/").split("/")
    current = ""
    for part in parts:
        if not part:
            current = "/"
            continue
        current = current.rstrip("/") + "/" + part
        # Skip anything above our deploy root to avoid permission errors
        if len(current.rstrip("/")) <= len(f"/home/{USER}"):
            continue
        try:
            sftp.stat(current)
        except (FileNotFoundError, IOError):
            try:
                sftp.mkdir(current)
            except IOError:
                pass  # already exists or we don't need to create it

SKIP_DIRS  = {".next", "node_modules", ".git", "__pycache__"}
SKIP_EXTS  = {".pyc", ".log"}

uploaded = 0
for local_path in LOCAL_UI.rglob("*"):
    # Skip unwanted dirs/files
    if any(part in SKIP_DIRS for part in local_path.parts):
        continue
    if local_path.suffix in SKIP_EXTS:
        continue
    if local_path.name.startswith(".env.local"):
        continue  # we write this ourselves below

    rel = local_path.relative_to(LOCAL_UI)
    remote_path = f"{REMOTE}/{rel.as_posix()}"

    if local_path.is_dir():
        sftp_mkdir_p(sftp, remote_path)
    elif local_path.is_file():
        sftp_mkdir_p(sftp, str(Path(remote_path).parent))
        sftp.put(str(local_path), remote_path)
        uploaded += 1

print(f"  Uploaded {uploaded} files to {REMOTE}")

# ── 3. Write .env.local ───────────────────────────────────────────────────────
print("\n=== Step 3: Write .env.local ===")
env_remote = f"{REMOTE}/.env.local"
with sftp.file(env_remote, "w") as f:
    f.write(ENV_CONTENT)
print(f"  Written: {env_remote}")
sftp.close()

# ── 4. npm install ────────────────────────────────────────────────────────────
print("\n=== Step 4: npm install ===")
rc, _ = run(f"cd {REMOTE} && npm install --prefer-offline 2>&1 | tail -8", timeout=270, label="npm-install")
if rc != 0:
    print("  npm install failed — check output above")
    c.close(); exit(1)

# ── 5. Build ──────────────────────────────────────────────────────────────────
print("\n=== Step 5: npm run build ===")
rc, _ = run(f"cd {REMOTE} && npm run build 2>&1 | tail -15", timeout=270, label="build")
if rc != 0:
    print("  Build failed — check output above")
    c.close(); exit(1)

# ── 6. Kill old instance + start ─────────────────────────────────────────────
print("\n=== Step 6: Start UI on port 3000 ===")
run("fuser -k 3000/tcp 2>/dev/null; sleep 2; echo ok", label="kill-old")
start_cmd = (
    f"cd {REMOTE} && "
    f"setsid sh -c 'PORT=3000 npm start >> /tmp/demo-ui.log 2>&1' </dev/null &"
)
run(start_cmd, label="start")
print("  Waiting 15s for server to bind...")
time.sleep(15)

# ── 7. Smoke test ─────────────────────────────────────────────────────────────
print("\n=== Step 7: Smoke test ===")
run("curl -s -o /dev/null -w 'HTTP %{http_code}' http://localhost:3000/ 2>&1", label="smoke")
run("tail -20 /tmp/demo-ui.log 2>/dev/null", label="log-tail")

c.close()
print(f"\nDone. UI should be running at http://{HOST}:3000")
