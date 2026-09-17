#!/bin/sh
# Log podman into IBM Container Registry, then start the Satellite agent.
#
# Reads credentials from setup/config.env (gitignored).
# Values come from the TechZone IBM Cloud Satellite reservation output.
# Copy setup/config.env.template -> setup/config.env and fill in before running.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG="$SCRIPT_DIR/config.env"

if [ ! -f "$CONFIG" ]; then
  echo "ERROR: $CONFIG not found."
  echo "Copy setup/config.env.template -> setup/config.env and fill in your values."
  exit 1
fi
# shellcheck source=setup/config.env
. "$CONFIG"

: "${SAT_APIKEY:?SAT_APIKEY not set in config.env}"
: "${SAT_CONNECTOR_ID:?SAT_CONNECTOR_ID not set in config.env}"

# Login to icr.io with the Satellite IAM API key
echo "$SAT_APIKEY" | sudo podman login icr.io \
  --username iamapikey \
  --password-stdin

sudo podman stop wxd-connector-agent 2>/dev/null || true
sudo podman rm   wxd-connector-agent 2>/dev/null || true

# Note: --network host discards -p port mappings; the agent listens on the
# cloud endpoint's assigned target port (29999) directly on the host.
sudo podman run -d \
  --name wxd-connector-agent \
  --restart always \
  --network host \
  --env SATELLITE_CONNECTOR_ID="$SAT_CONNECTOR_ID" \
  --env SATELLITE_CONNECTOR_IAM_APIKEY="$SAT_APIKEY" \
  icr.io/ibm/satellite-connector/satellite-connector-agent:latest

echo "Waiting 15s for agent to connect..."
sleep 15
sudo podman logs wxd-connector-agent 2>&1 | grep -E "Connected|Tunnel|ERROR|error" | tail -5
