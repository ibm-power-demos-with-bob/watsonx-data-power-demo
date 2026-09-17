#!/usr/bin/env python3
"""
Grant DataAccess on pg_olist and ibmi_olist to the TechZone service ID.
Run on the RHEL VM where the API key is already available in .env.local.

Usage:
    WXD_APIKEY=<key> WXD_INSTANCE_CRN=<crn> WXD_SERVICE_ID=<id> python3 grant-catalog-access.py

Or source .env.local first:
    set -a; . ~/watsonx-data-power-demo/demo-ui/.env.local; set +a
    python3 ~/watsonx-data-power-demo/setup/grant-catalog-access.py
"""
import json
import os
import sys
import requests

APIKEY       = os.environ.get("WXD_APIKEY", "")
INSTANCE_CRN = os.environ.get("WXD_INSTANCE_CRN", "")
SERVICE_ID   = os.environ.get("WXD_SERVICE_ID", "itz-110000sg2k-limql82k")
REGION_HOST  = os.environ.get("WXD_REGION_HOST", "https://eu-gb.lakehouse.cloud.ibm.com")
CATALOGS     = ["pg_olist", "ibmi_olist"]

if not APIKEY or not INSTANCE_CRN:
    print("ERROR: WXD_APIKEY and WXD_INSTANCE_CRN must be set.", file=sys.stderr)
    sys.exit(1)

# Extract instance GUID from CRN (last non-empty segment before trailing ::)
INSTANCE_GUID = INSTANCE_CRN.rstrip(":").split(":")[-1]
BASE_URL = f"{REGION_HOST.rstrip('/')}/lakehouse/api/v3"

print("Getting IAM token ...")
r = requests.post(
    "https://iam.cloud.ibm.com/identity/token",
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    data={"grant_type": "urn:ibm:params:oauth:grant-type:apikey", "apikey": APIKEY},
    timeout=30,
)
r.raise_for_status()
token = r.json()["access_token"]
print(f"  Token OK (expires_in={r.json().get('expires_in')}s)")

HEADERS = {
    "Authorization": f"Bearer {token}",
    "AuthInstanceId": INSTANCE_CRN,
    "Content-Type": "application/json",
    "Accept": "application/json",
}

payload = {"groups": [], "users": [{"user_name": SERVICE_ID, "access": "can_use"}]}

for catalog in CATALOGS:
    print(f"\n--- Granting access: {SERVICE_ID} -> {catalog} ---")
    tried = []
    for url in [
        f"{BASE_URL}/{INSTANCE_GUID}/catalogs/{catalog}/access",
        f"{BASE_URL}/catalogs/{catalog}/access",
    ]:
        tried.append(url)
        print(f"  POST {url}")
        resp = requests.post(url, headers=HEADERS, json=payload, timeout=30)
        print(f"  Status: {resp.status_code}")
        if resp.text.strip():
            print(f"  Body:   {resp.text[:600]}")
        if resp.status_code in (200, 201, 204):
            print(f"  SUCCESS: access granted.")
            break
        if resp.status_code == 409:
            print(f"  ALREADY GRANTED (409 — OK).")
            break
        if resp.status_code == 404:
            print(f"  404 — trying next URL ...")
            continue
        # Any other error
        print(f"  WARN: unexpected status — check body above.", file=sys.stderr)
        break
    else:
        print(f"  ERROR: all URL patterns returned 404 for {catalog}.", file=sys.stderr)
        print(f"  Manual fallback: Access Control -> Catalogs -> {catalog} -> Add access -> {SERVICE_ID} -> DataAccess")

print("\n=== Verification: list current access on each catalog ===")
for catalog in CATALOGS:
    print(f"\n{catalog}:")
    for url in [
        f"{BASE_URL}/{INSTANCE_GUID}/catalogs/{catalog}/access",
        f"{BASE_URL}/catalogs/{catalog}/access",
    ]:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        if resp.status_code == 200:
            print(f"  GET {url} -> {resp.status_code}")
            data = resp.json()
            print(f"  {json.dumps(data, indent=2)[:800]}")
            break
        elif resp.status_code != 404:
            print(f"  GET {url} -> {resp.status_code}: {resp.text[:200]}")

print("\nDone.")
