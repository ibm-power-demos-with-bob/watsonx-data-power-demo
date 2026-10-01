#!/usr/bin/env python3
"""
===========================================================================
IBM Cloud Satellite — configure connector endpoints for watsonx.data demo
===========================================================================

Idempotent: run this on every new reservation.

What this script does
---------------------
1. Gets an IAM token from the IBM Cloud API key.
2. Using the connector ID you provide, lists existing endpoints.
3. For each required endpoint (ibmi-db2, pg-olist):
   - If it already exists  → PATCH server_host/server_port to current VM IPs.
   - If it does not exist  → POST to create it from scratch.
4. Prints the final client_host:client_port values — these go into
   IBMI_HOST / IBMI_PORT and PG_HOST / PG_PORT in 7-register-catalogs.py.

How to find your Satellite connector ID
-----------------------------------------
The connector ID is NOT shown on the TechZone reservation page. Get it from
the IBM Cloud console:

  1. Go to https://cloud.ibm.com/satellite/connectors
     (make sure you have switched to the ITZ-V2 account using the account
     switcher dropdown — account ID ead8711ba2cc4d08a16fd37427f4f01a)
  2. Click on the connector named 'wxd-power-connector'
  3. The ID is shown in the connector details page, or in the URL:
     .../satellite/connectors/<CONNECTOR_ID>/...
  4. Pass it as SAT_CONNECTOR_ID or --connector-id below.

Usage
-----
    # Minimal:
    SAT_APIKEY=<ibm-cloud-api-key> \\
    SAT_CONNECTOR_ID=<connector-id> \\
    IBMI_IP=<ibmi-vm-ip> \\
    RHEL_IP=<rhel-vm-ip> \\
    python3 setup/2-configure-satellite.py

    # Current session 16 values (already set as defaults in CONFIG below):
    python3 setup/2-configure-satellite.py

    # Dry run — prints what would happen, no changes:
    python3 setup/2-configure-satellite.py --dry-run

Endpoint definitions
--------------------
  ibmi-db2  : TCP tunnel → IBM i DRDA port 8471
  pg-olist  : TCP tunnel → PostgreSQL port 5432 on RHEL VM

The client_host / client_port (what watsonx.data connects to) are assigned
by IBM Cloud and do not change when you update server_host.
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


# ---------------------------------------------------------------------------
# Configuration — reads from reservation.py; override with env vars if needed
# ---------------------------------------------------------------------------

try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import reservation as _r
    import socket
    # Resolve FQDNs to IPs — Satellite endpoints need bare IPs
    def _resolve(fqdn):
        try:
            return socket.gethostbyname(fqdn)
        except Exception:
            return fqdn
    _ibmi_ip = _resolve(_r.IBMI_HOST)
    _rhel_ip  = _resolve(_r.RHEL_HOST)
    _defaults = {
        "sat_apikey":       _r.SATELLITE_IAM_APIKEY,
        "sat_connector_id": _r.SATELLITE_CONNECTOR_ID,
        "ibmi_ip":          _ibmi_ip,
        "rhel_ip":          _rhel_ip,
    }
except Exception as _e:
    print(f"Warning: could not load reservation.py defaults: {_e}", file=sys.stderr)
    _defaults = {"sat_apikey": "", "sat_connector_id": "", "ibmi_ip": "", "rhel_ip": ""}

CONFIG = {
    "sat_apikey":       os.environ.get("SAT_APIKEY",       _defaults["sat_apikey"]),
    "sat_connector_id": os.environ.get("SAT_CONNECTOR_ID", _defaults["sat_connector_id"]),
    "ibmi_ip":          os.environ.get("IBMI_IP",          _defaults["ibmi_ip"]),
    "rhel_ip":          os.environ.get("RHEL_IP",          _defaults["rhel_ip"]),
}

SAT_LINK_BASE = "https://api.link.satellite.cloud.ibm.com/v1"

# Desired endpoint definitions
ENDPOINTS = [
    {
        "display_name":    "ibmi-db2",
        "server_port":     8471,
        "server_protocol": "tcp",
        "client_protocol": "tcp",
        "conn_type":       "location",
        "ip_key":          "ibmi_ip",
    },
    {
        "display_name":    "pg-olist",
        "server_port":     5432,
        "server_protocol": "tcp",
        "client_protocol": "tcp",
        "conn_type":       "location",
        "ip_key":          "rhel_ip",
    },
]


# ---------------------------------------------------------------------------
# IAM token
# ---------------------------------------------------------------------------

def get_iam_token(api_key: str) -> str:
    data = urllib.parse.urlencode({
        "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
        "apikey": api_key,
    }).encode()
    req = urllib.request.Request(
        "https://iam.cloud.ibm.com/identity/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())["access_token"]


# ---------------------------------------------------------------------------
# Satellite Link API helpers
# ---------------------------------------------------------------------------

def _sat_request(token: str, method: str, path: str, body: dict = None) -> dict:
    url = f"{SAT_LINK_BASE}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type":  "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {url} HTTP {e.code}: {e.read().decode('utf-8', errors='replace')[:400]}")


def list_endpoints(token: str, connector_id: str) -> list:
    result = _sat_request(token, "GET", f"/connectors/{connector_id}/endpoints")
    return result if isinstance(result, list) else result.get("endpoints", [])


def create_endpoint(token: str, connector_id: str, defn: dict, server_host: str, dry_run: bool) -> dict:
    payload = {
        "display_name":    defn["display_name"],
        "server_host":     server_host,
        "server_port":     defn["server_port"],
        "server_protocol": defn["server_protocol"],
        "client_protocol": defn["client_protocol"],
        "conn_type":       defn["conn_type"],
    }
    if dry_run:
        print(f"    [DRY RUN] Would POST: {json.dumps(payload)}")
        return {}
    return _sat_request(token, "POST", f"/connectors/{connector_id}/endpoints", payload)


def update_endpoint(token: str, connector_id: str, endpoint_id: str, server_host: str, dry_run: bool) -> dict:
    if dry_run:
        print(f"    [DRY RUN] Would PATCH endpoint {endpoint_id}: server_host={server_host}")
        return {}
    return _sat_request(token, "PATCH",
                        f"/connectors/{connector_id}/endpoints/{endpoint_id}",
                        {"server_host": server_host})


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Configure IBM Cloud Satellite connector endpoints for watsonx.data demo.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--dry-run",      action="store_true", help="Print actions without making changes.")
    parser.add_argument("--connector-id", default=None,        help="Satellite connector ID (overrides SAT_CONNECTOR_ID).")
    parser.add_argument("--ibmi-ip",      default=None,        help="IBM i VM IP (overrides IBMI_IP).")
    parser.add_argument("--rhel-ip",      default=None,        help="RHEL VM IP (overrides RHEL_IP).")
    args = parser.parse_args()

    if args.connector_id: CONFIG["sat_connector_id"] = args.connector_id
    if args.ibmi_ip:      CONFIG["ibmi_ip"]          = args.ibmi_ip
    if args.rhel_ip:      CONFIG["rhel_ip"]           = args.rhel_ip

    missing = []
    for k, label in [("sat_apikey", "SAT_APIKEY"), ("sat_connector_id", "SAT_CONNECTOR_ID"),
                     ("ibmi_ip", "IBMI_IP"), ("rhel_ip", "RHEL_IP")]:
        if not CONFIG[k]:
            missing.append(label)
    if missing:
        print("ERROR: missing required values:", file=sys.stderr)
        for m in missing:
            print(f"  {m}", file=sys.stderr)
        print("\nSee script header for how to find your Satellite connector ID.", file=sys.stderr)
        sys.exit(1)

    connector_id = CONFIG["sat_connector_id"]
    print(f"IBM Cloud Satellite endpoint configuration")
    print(f"  Connector ID : {connector_id}")
    print(f"  IBM i IP     : {CONFIG['ibmi_ip']}:8471")
    print(f"  RHEL IP      : {CONFIG['rhel_ip']}:5432")
    print()

    print("=== Step 1: Get IAM token ===")
    token = get_iam_token(CONFIG["sat_apikey"])
    print("  IAM token obtained.")
    print()

    print("=== Step 2: List existing endpoints ===")
    existing = {ep["display_name"]: ep for ep in list_endpoints(token, connector_id)}
    if existing:
        for name, ep in existing.items():
            print(f"  Found: {name:12s}  -> {ep['server_host']}:{ep['server_port']}  (client port {ep['client_port']})")
    else:
        print("  No endpoints found — will create from scratch.")
    print()

    print("=== Step 3: Create or update endpoints ===")
    for defn in ENDPOINTS:
        name = defn["display_name"]
        server_host = CONFIG[defn["ip_key"]]
        print(f"  {name}  (target: {server_host}:{defn['server_port']})")

        if name in existing:
            ep = existing[name]
            if ep["server_host"] == server_host:
                print(f"    Already correct — no change needed.")
            else:
                print(f"    Updating: {ep['server_host']} -> {server_host}")
                update_endpoint(token, connector_id, ep["endpoint_id"], server_host, args.dry_run)
        else:
            print(f"    Creating new endpoint...")
            result = create_endpoint(token, connector_id, defn, server_host, args.dry_run)
            if result:
                print(f"    Created: client port = {result.get('client_port', '?')}")
        print()

    print("=== Step 4: Final endpoint state ===")
    final = list_endpoints(token, connector_id)
    ep_map = {}
    for ep in final:
        ep_map[ep["display_name"]] = ep
        status = "[OK]" if ep["status"] == "enabled" else "[!!]"
        print(f"  {status} {ep['display_name']:12s}  {ep['client_host']}:{ep['client_port']}  -> {ep['server_host']}:{ep['server_port']}")
    print()

    ibmi_ep = ep_map.get("ibmi-db2", {})
    pg_ep   = ep_map.get("pg-olist", {})
    print("=== Values for 7-register-catalogs.py ===")
    print(f"  IBMI_HOST={ibmi_ep.get('client_host', 'c-01.private.eu-gb.link.satellite.cloud.ibm.com')}")
    print(f"  IBMI_PORT={ibmi_ep.get('client_port', '?')}")
    print(f"  PG_HOST={pg_ep.get('client_host', 'c-01.private.eu-gb.link.satellite.cloud.ibm.com')}")
    print(f"  PG_PORT={pg_ep.get('client_port', '?')}")
    print()
    print("Done. Run setup/7-register-catalogs.py next.")


if __name__ == "__main__":
    main()
