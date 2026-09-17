#!/bin/bash
# =============================================================================
# remote-deploy-demo-ui.sh
# Uploaded to the RHEL VM and executed remotely.
# Installs Node 20, handles fapolicyd, builds + starts the demo UI.
# Idempotent — safe to re-run.
# =============================================================================

set -euo pipefail

REPO_DIR="$HOME/watsonx-data-power-demo"
UI_DIR="$REPO_DIR/demo-ui"
LOG="$HOME/demo-ui-deploy.log"
UI_PORT=3000

echo "=== watsonx.data Demo UI — Remote Deploy ===" | tee "$LOG"
date | tee -a "$LOG"

# 1. Node.js 20 via dnf module (NodeSource does not support ppc64le)
echo "" | tee -a "$LOG"
echo "▸ 1/6 Node.js 20..." | tee -a "$LOG"
NODE_MAJOR=$(node --version 2>/dev/null | sed 's/v//;s/\..*//' || echo "0")
if [[ "${NODE_MAJOR}" -ge 20 ]]; then
  echo "  Node $(node --version) already at 20+" | tee -a "$LOG"
else
  echo "  Enabling nodejs:20 module stream..." | tee -a "$LOG"
  sudo dnf module enable -y nodejs:20 >> "$LOG" 2>&1
  sudo dnf install -y nodejs npm >> "$LOG" 2>&1
  echo "  Installed: $(node --version)" | tee -a "$LOG"
fi

# 2. fapolicyd home-dir allow rule (needed for next build)
echo "▸ 2/6 fapolicyd rule..." | tee -a "$LOG"
RULE="/etc/fapolicyd/rules.d/69-home-allow.rules"
if sudo test -f "$RULE" 2>/dev/null; then
  echo "  Rule already present" | tee -a "$LOG"
elif systemctl is-active --quiet fapolicyd 2>/dev/null; then
  echo "  Writing allow rule for /home/..." | tee -a "$LOG"
  echo 'allow perm=any all : dir=/home/' | sudo tee "$RULE" >> "$LOG"
  sudo fapolicyd-cli --update >> "$LOG" 2>&1 || true
  sudo systemctl restart fapolicyd >> "$LOG" 2>&1 || true
  echo "  fapolicyd rule applied" | tee -a "$LOG"
else
  echo "  fapolicyd not active — skipping" | tee -a "$LOG"
fi

# 3. npm install
echo "▸ 3/6 npm install --ignore-scripts..." | tee -a "$LOG"
cd "$UI_DIR"
npm install --ignore-scripts >> "$LOG" 2>&1
echo "  Done" | tee -a "$LOG"

# 4. npm run build
echo "▸ 4/6 npm run build..." | tee -a "$LOG"
npm run build >> "$LOG" 2>&1
echo "  Build complete" | tee -a "$LOG"

# 5. Start the server (kill any existing instance first)
echo "▸ 5/6 Starting server on port $UI_PORT..." | tee -a "$LOG"
OLDPID=$(lsof -ti:$UI_PORT 2>/dev/null || true)
if [[ -n "$OLDPID" ]]; then
  echo "  Killing existing process $OLDPID" | tee -a "$LOG"
  kill "$OLDPID" 2>/dev/null || true
  sleep 2
fi
cd "$UI_DIR"
PORT=$UI_PORT nohup npm start >> "$HOME/demo-ui.log" 2>&1 &
NEWPID=$!
disown $NEWPID
echo "$NEWPID" > "$HOME/demo-ui.pid"
echo "  Started PID $NEWPID — logs at ~/demo-ui.log" | tee -a "$LOG"

# 6. Open firewall port
echo "▸ 6/6 Firewall port $UI_PORT..." | tee -a "$LOG"
if sudo firewall-cmd --list-ports 2>/dev/null | grep -q "${UI_PORT}/tcp"; then
  echo "  Already open" | tee -a "$LOG"
else
  sudo firewall-cmd --permanent --add-port=${UI_PORT}/tcp >> "$LOG" 2>&1
  sudo firewall-cmd --reload >> "$LOG" 2>&1
  echo "  Opened ${UI_PORT}/tcp" | tee -a "$LOG"
fi

# Verify
sleep 4
HTTP=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:$UI_PORT/ 2>/dev/null || echo "000")
echo "" | tee -a "$LOG"
if [[ "$HTTP" == "200" ]]; then
  echo "✓ DEPLOY OK — http://$(hostname -f):$UI_PORT  (HTTP $HTTP)" | tee -a "$LOG"
else
  echo "✗ HTTP $HTTP — check ~/demo-ui.log" | tee -a "$LOG"
fi
echo "DEPLOY_COMPLETE" | tee -a "$LOG"
