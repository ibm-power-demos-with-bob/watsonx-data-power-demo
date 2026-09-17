#!/usr/bin/env python3
"""
Diagnose which identity the API key belongs to, and what it can see.
Run on RHEL after sourcing .env.local
"""
import os
import requests

APIKEY       = os.environ.get("WXD_APIKEY", "")
INSTANCE_CRN = os.environ.get("WXD_INSTANCE_CRN", "")
INSTANCE_GUID = INSTANCE_CRN.rstrip(":").split(":")[-1]
BASE_URL = "https://eu-gb.lakehouse.cloud.ibm.com/lakehouse/api/v3"

# Get IAM token and decode it
r = requests.post(
    "https://iam.cloud.ibm.com/identity/token",
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    data={"grant_type": "urn:ibm:params:oauth:grant-type:apikey", "apikey": APIKEY},
    timeout=30,
)
r.raise_for_status()
tok_resp = r.json()
token = tok_resp["access_token"]
print(f"Token OK, expires_in={tok_resp.get('expires_in')}s")

# Decode JWT payload (base64, no verify)
import base64, json
parts = token.split(".")
if len(parts) >= 2:
    pad = parts[1] + "=" * (4 - len(parts[1]) % 4)
    try:
        payload = json.loads(base64.b64decode(pad))
        print(f"\nJWT identity:")
        for k in ("sub", "iam_id", "id", "email", "name", "account", "iat", "exp"):
            if k in payload:
                print(f"  {k}: {payload[k]}")
    except Exception as e:
        print(f"  Could not decode JWT: {e}")

HEADERS = {
    "Authorization": f"Bearer {token}",
    "AuthInstanceId": INSTANCE_CRN,
    "Content-Type": "application/json",
    "Accept": "application/json",
}

# IAM introspect
print("\n=== IAM token introspect ===")
intr = requests.post(
    "https://iam.cloud.ibm.com/identity/introspect",
    headers={"Content-Type": "application/x-www-form-urlencoded",
             "Authorization": f"Basic Yng6Yng="},
    data={"token": token},
    timeout=20,
)
print(f"Status: {intr.status_code}")
if intr.status_code == 200:
    d = intr.json()
    for k in ("sub", "iam_id", "id", "email", "name", "client_id"):
        if k in d:
            print(f"  {k}: {d[k]}")

# Try listing catalogs with this identity
print("\n=== Catalogs visible to this key ===")
r2 = requests.get(f"{BASE_URL}/catalogs", headers=HEADERS, timeout=20)
print(f"GET /catalogs -> {r2.status_code}: {r2.text[:400]}")

# Try listing database registrations
print("\n=== Database registrations ===")
r3 = requests.get(f"{BASE_URL}/database_registrations", headers=HEADERS, timeout=20)
print(f"GET /database_registrations -> {r3.status_code}")
if r3.status_code == 200:
    dbs = r3.json().get("database_registrations", [])
    print(f"  count={len(dbs)}")
    for db in dbs:
        print(f"  {db.get('database_display_name')} / {db.get('associated_catalog',{}).get('catalog_name')}")

# Try the student App ID key directly using IBM Cloud App ID token exchange
# The student password e53b16is2bclf0q is the App ID credential, not an IAM API key
# The TECHZONE service API key is: we need to confirm what iam_id it resolves to
print("\nDone.")
