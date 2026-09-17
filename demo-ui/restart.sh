#!/bin/bash
set -e
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "Killing any process on port 3000..."
# Use ss-based kill so it catches any process name (Next.js workers show up as "MainThread" etc.)
kill -9 $(ss -tlnp | grep 3000 | grep -oP 'pid=\K[0-9]+') 2>/dev/null || true
sleep 1

echo "Starting Next.js on port 3000..."
# setsid detaches into a new session group so SSH returns immediately without CANCELED.
# nohup ... & disown works too but can leave the SSH tool in a "executing" state.
PORT=3000 setsid npm start >> ~/demo-ui.log 2>&1 &
sleep 5

echo "Checking port 3000 status..."
ss -tlnp | grep 3000 || echo "Port 3000 not listening yet!"

echo "Testing routes:"
curl -s -o /dev/null -w "Root route /: %{http_code}\n" http://localhost:3000/
curl -s -o /dev/null -w "Sources route /sources: %{http_code}\n" http://localhost:3000/sources
curl -s -o /dev/null -w "Cyber live /live?scenario=cyber: %{http_code}\n" http://localhost:3000/live?scenario=cyber
