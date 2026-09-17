#!/usr/bin/env python3
"""
test_wxd_from_laptop.py
-----------------------
Tests watsonx.data API and Presto connectivity directly from this machine,
through IBM Satellite to the watsonx.data SaaS instance.

Tests (in order):
  1. IAM token exchange — confirms the API key is valid
  2. GET /prestissimo_engines — confirms IAM access to the watsonx.data API
  3. Presto: SHOW CATALOGS — confirms Presto auth (no MetaStore DataAccess needed)
  4. Presto: SELECT COUNT(*) FROM pg_olist.olist.tier2_suppliers — needs MetaStore DataAccess

Usage:
  python3 setup/test_wxd_from_laptop.py
  python3 setup/test_wxd_from_laptop.py --key <api_key>   # override key
"""

import urllib.request
import urllib.parse
import urllib.error
import json
import time
import sys
import argparse

# ---------------------------------------------------------------------------
# Config — watsonx.data instance (eu-gb, expires 2026-09-18)
# ---------------------------------------------------------------------------
INSTANCE_GUID = "e4ec7696-6363-4ad9-a21f-41eba7b7a663"
INSTANCE_CRN  = "crn:v1:bluemix:public:lakehouse:eu-gb:a/9f8f95eee4714473a87fa319d964063c:e4ec7696-6363-4ad9-a21f-41eba7b7a663::"
WXD_API_HOST  = "eu-gb.lakehouse.cloud.ibm.com"
PRESTO_HOST   = "70733fc8-2b02-4683-ba01-628f66e07284.d4mn75il0dt1ob8mmlug.lakehouse.ibmappdomain.cloud"
PRESTO_PORT   = 31618

# API keys to test — label : key
API_KEYS = {
    "wxd-demo-query (service ID, added to access group)":
        "ZaX8fUqkwmU6wkeXDTLbL0XKbnalBG7JWeriyPFE7C-Y",
    "itz-110000sg2k-limql82k (TechZone-provisioned service ID)":
        "cCJ82TpKwibZubhEgq7dHcPgsU96kEBOfs3G53DKC2I1",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def separator(title=""):
    width = 70
    if title:
        pad = (width - len(title) - 2) // 2
        print(f"\n{'─' * pad} {title} {'─' * pad}")
    else:
        print("─" * width)


def get_iam_token(api_key: str) -> str | None:
    """Exchange an IBM Cloud API key for a Bearer IAM token."""
    data = urllib.parse.urlencode({
        "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
        "apikey": api_key,
    }).encode()
    req = urllib.request.Request(
        "https://iam.cloud.ibm.com/identity/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read())
            token = body.get("access_token")
            if token:
                print(f"  ✅ IAM token obtained (expires in {body.get('expires_in', '?')}s)")
                return token
            else:
                print(f"  ❌ IAM response had no access_token: {body}")
                return None
    except urllib.error.HTTPError as e:
        print(f"  ❌ IAM HTTP {e.code}: {e.read().decode()[:200]}")
        return None
    except Exception as e:
        print(f"  ❌ IAM error: {e}")
        return None


def wxd_api_get(path: str, token: str) -> tuple[int, dict | str]:
    """GET from the watsonx.data v3 REST API."""
    url = f"https://{WXD_API_HOST}{path}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "AuthInstanceId": INSTANCE_CRN,
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:400]
    except Exception as e:
        return -1, str(e)


def presto_query(sql: str, token: str, poll_interval: int = 3, max_polls: int = 20) -> str:
    """
    Submit a Presto HTTP query and poll until done.
    Returns a short result summary string.
    """
    submit_url = f"http://{PRESTO_HOST}:{PRESTO_PORT}/v1/statement"
    req = urllib.request.Request(
        submit_url,
        data=sql.encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "X-Presto-User": "ibmlhapikey",
            "X-Presto-Catalog": "tpch",
            "Content-Type": "text/plain",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            state = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return f"❌ HTTP {e.code}: {e.read().decode()[:300]}"
    except Exception as e:
        return f"❌ Submit error: {e}"

    next_uri = state.get("nextUri")
    for _ in range(max_polls):
        if not next_uri:
            break
        time.sleep(poll_interval)
        try:
            poll_req = urllib.request.Request(next_uri, headers={
                "Authorization": f"Bearer {token}",
                "X-Presto-User": "ibmlhapikey",
            })
            with urllib.request.urlopen(poll_req, timeout=20) as resp:
                state = json.loads(resp.read())
        except Exception as e:
            return f"❌ Poll error: {e}"
        next_uri = state.get("nextUri")
        status = state.get("stats", {}).get("state", "?")
        if status in ("FAILED", "FINISHED"):
            break

    stats = state.get("stats", {})
    status = stats.get("state", "?")

    if status == "FAILED":
        err = state.get("error", {})
        return f"❌ FAILED — {err.get('errorName', '?')}: {err.get('message', '?')[:250]}"

    if status == "FINISHED":
        cols = [c["name"] for c in state.get("columns", [])]
        rows = state.get("data", [])
        if rows:
            lines = [" | ".join(str(v) for v in row) for row in rows[:5]]
            return f"✅ FINISHED — cols: {cols}\n    rows: " + "\n    ".join(lines)
        return f"✅ FINISHED — no rows returned"

    return f"⚠️  Timed out in state {status}"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_tests(api_key: str, label: str):
    separator(label[:60])

    # 1. IAM token
    print("\n[1] Exchanging API key for IAM token...")
    token = get_iam_token(api_key)
    if not token:
        print("  ⛔ Cannot proceed — no IAM token.")
        return

    # 2. watsonx.data REST API — list engines
    print("\n[2] GET /prestissimo_engines (watsonx.data API reachability)...")
    code, body = wxd_api_get(
        f"/lakehouse/api/v3/{INSTANCE_GUID}/prestissimo_engines", token
    )
    if code == 200 and isinstance(body, dict):
        engines = body.get("prestissimo_engines", [])
        names = [(e.get("engine_id"), e.get("status")) for e in engines]
        print(f"  ✅ HTTP 200 — engines: {names}")
    else:
        print(f"  ❌ HTTP {code}: {str(body)[:300]}")
        if code == 403:
            print("  ℹ️  403 here = IAM access to watsonx.data API denied.")
            print("     Check: access group policy grants Viewer/Manager on the watsonx.data service instance.")
        return  # No point trying Presto if we can't even hit the API

    # 3. Presto: SHOW CATALOGS
    print("\n[3] Presto: SHOW CATALOGS...")
    result = presto_query("SHOW CATALOGS", token)
    print(f"  {result}")

    # 4. Presto: count tier2_suppliers in pg_olist
    print("\n[4] Presto: SELECT COUNT(*) FROM pg_olist.olist.tier2_suppliers...")
    result = presto_query(
        "SELECT COUNT(*) FROM pg_olist.olist.tier2_suppliers", token
    )
    print(f"  {result}")

    # 5. Presto: count with IBM i catalog
    print("\n[5] Presto: SHOW SCHEMAS IN ibmi_olist...")
    result = presto_query("SHOW SCHEMAS IN ibmi_olist", token)
    print(f"  {result}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", help="Override: test a single API key")
    parser.add_argument("--label", default="custom key", help="Label for override key")
    args = parser.parse_args()

    print("watsonx.data connectivity test — from laptop")
    print(f"Instance: {INSTANCE_GUID}  ({WXD_API_HOST})")
    print(f"Presto:   {PRESTO_HOST}:{PRESTO_PORT}")

    if args.key:
        run_tests(args.key, args.label)
    else:
        for label, key in API_KEYS.items():
            run_tests(key, label)

    separator()
    print("Done.")


if __name__ == "__main__":
    main()
