#!/usr/bin/env python3
"""
Explore watsonx.data v3 API endpoints for access control.
Run on RHEL: python3 /tmp/explore-api.py
Credentials come from .env.local sourced before running.
"""
import os
import requests

APIKEY       = os.environ.get("WXD_APIKEY", "")
INSTANCE_CRN = os.environ.get("WXD_INSTANCE_CRN", "")
INSTANCE_GUID = INSTANCE_CRN.rstrip(":").split(":")[-1]
BASE_URL = "https://eu-gb.lakehouse.cloud.ibm.com/lakehouse/api/v3"

r = requests.post(
    "https://iam.cloud.ibm.com/identity/token",
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    data={"grant_type": "urn:ibm:params:oauth:grant-type:apikey", "apikey": APIKEY},
    timeout=30,
)
r.raise_for_status()
token = r.json()["access_token"]
print(f"Token OK")

HEADERS = {
    "Authorization": f"Bearer {token}",
    "AuthInstanceId": INSTANCE_CRN,
    "Content-Type": "application/json",
    "Accept": "application/json",
}

# Probe known and plausible access control endpoint paths
probe_paths = [
    f"/policies",
    f"/{INSTANCE_GUID}/policies",
    f"/access_control",
    f"/{INSTANCE_GUID}/access_control",
    f"/catalogs",
    f"/{INSTANCE_GUID}/catalogs",
    f"/{INSTANCE_GUID}/data_policy_manager",
    f"/{INSTANCE_GUID}/access_management",
    f"/authorization",
    f"/{INSTANCE_GUID}/authorization",
]

print("\n=== Probing access-control endpoints ===")
for path in probe_paths:
    url = BASE_URL + path
    resp = requests.get(url, headers=HEADERS, timeout=20)
    print(f"GET {path} -> {resp.status_code}: {resp.text[:300]}")

# Check what database_registrations look like (to get catalog IDs)
print("\n=== Database registrations ===")
resp = requests.get(f"{BASE_URL}/database_registrations", headers=HEADERS, timeout=20)
print(f"GET /database_registrations -> {resp.status_code}")
if resp.status_code == 200:
    dbs = resp.json().get("database_registrations", [])
    for db in dbs:
        print(f"  id={db.get('database_id')} display={db.get('database_display_name')} catalog={db.get('associated_catalog', {}).get('catalog_name')}")

# Check engine catalogs
print("\n=== Engine catalog list ===")
resp = requests.get(f"{BASE_URL}/prestissimo_engines", headers=HEADERS, timeout=20)
if resp.status_code == 200:
    engines = resp.json().get("prestissimo_engines", [])
    for eng in engines:
        eid = eng.get("engine_id") or eng.get("id")
        print(f"  engine={eid} status={eng.get('status')}")
        # Try instance-scoped catalogs for this engine
        cat_resp = requests.get(f"{BASE_URL}/{INSTANCE_GUID}/prestissimo_engines/{eid}/catalogs",
                                headers=HEADERS, timeout=20)
        print(f"    GET /{INSTANCE_GUID}/prestissimo_engines/{eid}/catalogs -> {cat_resp.status_code}: {cat_resp.text[:300]}")

print("\nDone.")
