#!/bin/bash
# =============================================================================
# deploy-demo-ui.sh
#
# Deploy the watsonx.data demo UI to the RHEL/Power10 sidecar VM.
#
# Usage (from repo root):
#   bash demo-ui/deploy-demo-ui.sh [--host FQDN] [--user SSH_USER] [--key SSH_KEY]
#
# Defaults (current TechZone reservation):
#   host : pvm1-9cug2i0k.p1387.pok-systems.techzone.ibm.com
#   user : ec2-user
#   key  : ~/Downloads/user_ssh_private_key (1).user
#
# ppc64le notes (learned from Carbon-GenAI-Demos deployment):
#   - NodeSource does NOT support ppc64le. Use dnf module enable nodejs:20.
#   - fapolicyd blocks npm postinstall scripts — always use --ignore-scripts.
#   - fapolicyd also blocks next build from ~/node_modules — add home-dir rule.
#   - Use nohup + disown, not PM2, to match the proven pattern.
#   - firewall-cmd must open port 3000 explicitly.
# =============================================================================

set -euo pipefail

REMOTE_HOST="pvm1-9cug2i0k.p1387.pok-systems.techzone.ibm.com"
REMOTE_USER="ec2-user"
SSH_KEY="$HOME/Downloads/user_ssh_private_key (1).user"
REMOTE_DIR="/home/ec2-user/watsonx-data-power-demo"
UI_PORT=3000

while [[ $# -gt 0 ]]; do
  case $1 in
    --host) REMOTE_HOST="$2"; shift 2 ;;
    --user) REMOTE_USER="$2"; shift 2 ;;
    --key)  SSH_KEY="$2";     shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

SSH="ssh -i \"${SSH_KEY}\" -o StrictHostKeyChecking=no -o ConnectTimeout=15 ${REMOTE_USER}@${REMOTE_HOST}"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  watsonx.data Demo UI — Deploy to RHEL/Power10 VM"
echo "  Host : ${REMOTE_HOST}"
echo "  User : ${REMOTE_USER}"
echo "  Dir  : ${REMOTE_DIR}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── 1. Create remote directories ──────────────────────────────────────────────
echo ""
echo "▸ 1/7 Creating remote directories…"
eval "${SSH}" "mkdir -p ${REMOTE_DIR}/demo-ui ${REMOTE_DIR}/event-generators"

# ── 2. rsync files ────────────────────────────────────────────────────────────
echo "▸ 2/7 Syncing demo-ui/ and event-generators/ …"
rsync -az --delete \
  --exclude="node_modules" \
  --exclude=".next" \
  -e "ssh -i \"${SSH_KEY}\" -o StrictHostKeyChecking=no" \
  "$(pwd)/demo-ui/" \
  "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/demo-ui/"

rsync -az \
  -e "ssh -i \"${SSH_KEY}\" -o StrictHostKeyChecking=no" \
  "$(pwd)/event-generators/" \
  "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/event-generators/"

# ── 3. Node.js 20 via dnf module (correct ppc64le approach) ───────────────────
echo "▸ 3/7 Ensuring Node.js 20 (dnf module — NodeSource does not support ppc64le)…"
eval "${SSH}" << 'ENDSSH'
  set -e
  NODE_MAJOR=$(node --version 2>/dev/null | sed 's/v//;s/\..*//' || echo "0")
  if [[ "${NODE_MAJOR}" -ge 20 ]]; then
    echo "  Node $(node --version) — already at 20+, skipping"
  else
    echo "  Installing Node.js 20 via dnf module stream…"
    sudo dnf module enable -y nodejs:20
    sudo dnf install -y nodejs npm
    echo "  Node $(node --version) — installed"
  fi
ENDSSH

# ── 4. fapolicyd home-dir allow rule (required for next build on ppc64le) ─────
echo "▸ 4/7 Configuring fapolicyd to allow build from ~/node_modules…"
eval "${SSH}" << 'ENDSSH'
  set -e
  RULE_FILE="/etc/fapolicyd/rules.d/69-home-allow.rules"
  if sudo test -f "${RULE_FILE}"; then
    echo "  fapolicyd home-dir rule already present — skipping"
  else
    echo "  Writing fapolicyd allow rule for /home/ …"
    echo 'allow perm=any all : dir=/home/' | sudo tee "${RULE_FILE}"
    sudo fapolicyd-cli --update 2>/dev/null || true
    sudo systemctl restart fapolicyd 2>/dev/null || true
    echo "  fapolicyd rule applied"
  fi
ENDSSH

# ── 5. npm install + build ─────────────────────────────────────────────────────
echo "▸ 5/7 npm install (--ignore-scripts for fapolicyd) + npm run build…"
eval "${SSH}" "bash -s" << ENDSSH
  set -e
  cd ${REMOTE_DIR}/demo-ui
  echo "  Running npm install --ignore-scripts …"
  npm install --ignore-scripts 2>&1 | tail -5
  echo "  Running npm run build …"
  npm run build 2>&1 | tail -20
ENDSSH

# ── 6. Start / restart Next.js with nohup + disown ────────────────────────────
echo "▸ 6/7 Starting Next.js on port ${UI_PORT} (nohup + disown)…"
eval "${SSH}" "bash -s" << ENDSSH
  set -e
  cd ${REMOTE_DIR}/demo-ui

  # Kill any existing instance on this port
  OLDPID=\$(lsof -ti:${UI_PORT} 2>/dev/null || true)
  if [[ -n "\${OLDPID}" ]]; then
    echo "  Stopping existing process on port ${UI_PORT} (PID \${OLDPID})…"
    kill "\${OLDPID}" 2>/dev/null || true
    sleep 2
  fi

  # Start and immediately disown so it survives SSH session close
  PORT=${UI_PORT} nohup npm start > ~/demo-ui.log 2>&1 &
  NEWPID=\$!
  disown \${NEWPID}
  echo "\${NEWPID}" > ~/demo-ui.pid
  echo "  Started PID \${NEWPID} — logs at ~/demo-ui.log"
ENDSSH

# ── 7. Open firewall port ─────────────────────────────────────────────────────
echo "▸ 7/7 Opening firewall port ${UI_PORT}…"
eval "${SSH}" << ENDSSH
  set -e
  if sudo firewall-cmd --list-ports 2>/dev/null | grep -q "${UI_PORT}/tcp"; then
    echo "  Port ${UI_PORT}/tcp already open"
  else
    sudo firewall-cmd --permanent --add-port=${UI_PORT}/tcp
    sudo firewall-cmd --reload
    echo "  Port ${UI_PORT}/tcp opened"
  fi
ENDSSH

# ── Verify ─────────────────────────────────────────────────────────────────────
echo ""
echo "  Waiting 5s for server to start…"
sleep 5
HTTP_STATUS=$(eval "${SSH}" "curl -s -o /dev/null -w '%{http_code}' http://localhost:${UI_PORT}/ 2>/dev/null || echo 000")
if [[ "${HTTP_STATUS}" == "200" ]]; then
  echo "  ✓ App responding HTTP ${HTTP_STATUS} on port ${UI_PORT}"
else
  echo "  ✗ Got HTTP ${HTTP_STATUS} — check logs: ssh ... 'tail -30 ~/demo-ui.log'"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Demo UI URL:  http://${REMOTE_HOST}:${UI_PORT}"
echo ""
echo "  Useful commands:"
echo "    Logs  : ssh ... 'tail -f ~/demo-ui.log'"
echo "    Status: ssh ... 'ss -tlnp | grep :${UI_PORT}'"
echo "    Stop  : ssh ... 'kill \$(cat ~/demo-ui.pid)'"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
