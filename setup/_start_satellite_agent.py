#!/usr/bin/env python3
"""Log in to ICR and start the IBM Cloud Satellite connector agent via podman.

Before starting the agent, prints the IAM Service ID associated with the
SATELLITE_IAM_APIKEY. Every new user must authorise this Service ID on the
wxd-power-connector ACL (Step 8b in RUNBOOK.md) before the agent can connect.
"""
import base64, json, paramiko, requests, time, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from reservation import (RHEL_HOST as HOST, SSH_USER as USER, SSH_KEY as KEY,
                         SATELLITE_CONNECTOR_ID as CONNECTOR_ID,
                         SATELLITE_IAM_APIKEY as IAM_APIKEY,
                         SATELLITE_REGION as REGION)
IMAGE = "icr.io/ibm/satellite-connector/satellite-connector-agent:latest"

# ── Resolve and print the Service ID from the IAM API key ──────────────────
# This helps the user authorise their agent on the connector ACL (Step 8b).
print("--- Resolving IAM Service ID for this API key ---")
try:
    token_resp = requests.post(
        "https://iam.cloud.ibm.com/identity/token",
        data={"grant_type": "urn:ibm:params:oauth:grant-type:apikey", "apikey": IAM_APIKEY},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    token_resp.raise_for_status()
    access_token = token_resp.json()["access_token"]
    # JWT payload is the second segment; add padding so base64 doesn't fail
    payload_b64 = access_token.split(".")[1] + "=="
    payload = json.loads(base64.urlsafe_b64decode(payload_b64))
    service_id = payload.get("iam_id", "unknown")
    print(f"\n  ✅ Your IAM Service ID is: {service_id}")
    print(
        "\n  ⚠️  If this is your first time running this recipe, you MUST authorise\n"
        "     this Service ID on the wxd-power-connector before the agent will connect.\n"
        "     See RUNBOOK.md Step 8b for instructions.\n"
    )
except Exception as exc:
    print(f"  WARNING: Could not resolve Service ID — {exc}")
    print("  The agent will still start; check Step 8b in RUNBOOK.md if WSR04 doesn't appear.\n")

try:
    key = paramiko.Ed25519Key.from_private_key_file(KEY)
except Exception:
    key = paramiko.RSAKey.from_private_key_file(KEY)

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=USER, pkey=key)

def run(cmd, label="", timeout=120):
    _, out, err = c.exec_command(cmd, timeout=timeout)
    rc = out.channel.recv_exit_status()
    stdout = out.read().decode("utf-8", errors="replace").strip()
    stderr = err.read().decode("utf-8", errors="replace").strip()
    combined = (stdout + " " + stderr).strip()
    print(f"  [{label}] {combined[:600]}".encode("ascii","replace").decode("ascii"))
    return rc, stdout, stderr

# 1. Ensure podman is installed (RHEL 9 ppc64le — not always pre-installed)
print("--- Ensuring podman is installed ---")
rc, out, _ = run("which podman 2>/dev/null || echo missing", "podman-check", timeout=15)
if "missing" in out or rc != 0:
    print("  podman not found — installing via dnf...")
    rc2, _, err2 = run("sudo dnf install -y podman", "podman-install", timeout=180)
    if rc2 != 0:
        print(f"  podman install failed: {err2[:200]}")
        c.close()
        exit(1)
    print("  podman installed.")
else:
    print("  podman already present.")

# 2. Log in to ICR using the IAM API key
# ICR login: username is "iamapikey", password is the API key
print("\n--- Logging in to ICR (icr.io) ---")
rc, _, _ = run(f"echo '{IAM_APIKEY}' | sudo podman login icr.io -u iamapikey --password-stdin", "icr-login", timeout=60)
if rc != 0:
    print("ICR login failed — check API key. Exiting.")
    c.close()
    exit(1)

# 3. Remove old container if present
print("\n--- Removing old satellite-connector (if any) ---")
run("sudo podman rm -f satellite-connector 2>/dev/null; echo done", "cleanup")

# 4. Start the Satellite connector agent
print("\n--- Starting Satellite connector agent ---")
podman_cmd = (
    f"sudo podman run -d --name satellite-connector "
    f"--restart always "
    f"-e SATELLITE_CONNECTOR_ID={CONNECTOR_ID} "
    f"-e SATELLITE_CONNECTOR_IAM_APIKEY={IAM_APIKEY} "
    f"-e SATELLITE_CONNECTOR_REGION={REGION} "
    f"{IMAGE}"
)
rc, out, _ = run(podman_cmd, "podman-run", timeout=180)
if rc != 0:
    print("Container failed to start — check logs above.")
    c.close()
    exit(1)

# 5. Wait then check logs for connection status
print("\n--- Waiting 20s then checking logs ---")
time.sleep(20)
run("sudo podman logs --tail 30 satellite-connector 2>&1", "logs", timeout=30)

c.close()
print("\nDone. Verify connector shows 'Connected' in IBM Cloud UI before continuing.")
