#!/bin/bash
# Fire a cyber signal, run detection (hits Presto), then read alerts
BASE=http://129.40.125.69:3000

echo "=== Clearing alerts ==="
curl -s -X DELETE $BASE/api/alerts

echo ""
echo "=== Injecting cyber signal ==="
curl -s -X POST $BASE/api/inject-signal \
  -H "Content-Type: application/json" \
  -d '{"scenario":"supplier-cyber-incident"}'

echo ""
echo "=== Running detection (POST /api/alerts — queries Presto, may take 30-60s) ==="
curl -s --max-time 120 -X POST $BASE/api/alerts
echo ""

echo ""
echo "=== Reading alert store ==="
curl -s $BASE/api/alerts
echo ""
