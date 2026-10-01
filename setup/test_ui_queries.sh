#!/bin/bash
echo "=== Test 1: wxd-query API (pg_olist via Satellite tunnel) ==="
curl -s -X POST http://localhost:3000/api/wxd-query \
  -H 'Content-Type: application/json' \
  -d '{"sql":"SELECT COUNT(*) FROM pg_olist_tqj6kn2k.olist.tier2_suppliers"}' \
  | python3 -m json.tool 2>/dev/null || echo "(raw)"

echo ""
echo "=== Test 2: wxd-query API (ibmi_olist via Satellite tunnel) ==="
curl -s -X POST http://localhost:3000/api/wxd-query \
  -H 'Content-Type: application/json' \
  -d '{"sql":"SHOW SCHEMAS IN ibmi_olist_tqj6kn2k"}' \
  | python3 -m json.tool 2>/dev/null || echo "(raw)"

echo ""
echo "=== Test 3: detect-signals (cyber) ==="
curl -s -X POST http://localhost:3000/api/detect-signals \
  -H 'Content-Type: application/json' \
  -d '{"scenario":"cyber"}' \
  | python3 -m json.tool 2>/dev/null || echo "(raw)"
