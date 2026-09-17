#!/usr/bin/env python3
"""
setup/satellite-endpoints.py
============================
Automates creation and management of IBM Cloud Satellite Link Endpoints for the demo.

Features:
- Queries the Satellite Connector via IBM Cloud Satellite Link REST API.
- Idempotently creates the two required Link endpoints:
    1. pg-olist:  destination -> 127.0.0.1:5432 (PostgreSQL on RHEL)
    2. ibmi-db2:  destination -> <IBMI_IP>:8471 (Db2 for IBM i)
- Outputs cloud endpoint hostnames and ports in human-readable, shell-sourceable,
  or JSON format for chaining into the federation connector step.

Usage:
  # Human-readable summary (default):
  python setup/satellite-endpoints.py \\
    --api-key "<IBM_CLOUD_API_KEY>" \\
    --account-id "<ACCOUNT_ID>" \\
    --connector-id "<CONNECTOR_ID>" \\
    --ibmi-ip "129.40.94.90"

  # Emit shell export lines — source directly into the federation step:
  python setup/satellite-endpoints.py ... --output-env

  # Emit JSON — for scripted consumption:
  python setup/satellite-endpoints.py ... --output-json

  # Chain into the federation connector script in one line:
  eval $(python setup/satellite-endpoints.py ... --output-env) && \\
    IBMI_PASSWORD="<password>" python setup/5-add-federation-connectors.py

Output variables (--output-env / --output-json):
  PG_SAT_HOST    cloud hostname for the pg-olist endpoint
  PG_SAT_PORT    cloud port for the pg-olist endpoint
  IBMI_SAT_HOST  cloud hostname for the ibmi-db2 endpoint
  IBMI_SAT_PORT  cloud port for the ibmi-db2 endpoint
"""

import argparse
import json
import sys
import urllib.parse
import urllib.request

IAM_TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"
LINK_API_BASE = "https://api.link.satellite.cloud.ibm.com/v1/connectors"


def get_iam_token(api_key: str) -> str:
    """Exchange IBM Cloud API key for an IAM Bearer token."""
    data = urllib.parse.urlencode({
        "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
        "apikey": api_key
    }).encode("utf-8")
    req = urllib.request.Request(
        IAM_TOKEN_URL,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))["access_token"]


def list_endpoints(token: str, account_id: str, connector_id: str) -> list:
    """List all link endpoints configured on the connector."""
    url = f"{LINK_API_BASE}/{connector_id}/endpoints"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "X-Auth-Resource-Account": account_id
    })
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("endpoints", [])
    except urllib.error.HTTPError as e:
        print(f"❌ Error listing endpoints: {e.code} - {e.read().decode('utf-8')}")
        sys.exit(1)


def create_endpoint(token: str, account_id: str, connector_id: str, name: str, dest_host: str, dest_port: int) -> dict:
    """Create a new TCP link endpoint."""
    url = f"{LINK_API_BASE}/{connector_id}/endpoints"
    payload = {
        "display_name": name,
        "server_host": dest_host,
        "server_port": dest_port,
        "conn_type": "location",
        "client_protocol": "tcp",
        "server_protocol": "tcp",
        "client_mutual_auth": False
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "X-Auth-Resource-Account": account_id,
            "Content-Type": "application/json"
        }
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"❌ Error creating endpoint '{name}': {e.code} - {e.read().decode('utf-8')}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Manage Satellite Link Endpoints for watsonx.data Power demo.")
    parser.add_argument("--api-key", required=True, help="IBM Cloud IAM API Key")
    parser.add_argument("--account-id", required=True, help="IBM Cloud Account ID (BSS / Account GUID)")
    parser.add_argument("--connector-id", required=True, help="Satellite Connector ID")
    parser.add_argument("--ibmi-ip", required=True,
                        help="IBM i IP address on the on-prem network (from TechZone reservation details)")
    parser.add_argument("--rhel-ip", default="127.0.0.1",
                        help="RHEL / Postgres IP as seen from the Satellite agent (default: 127.0.0.1 — agent runs on RHEL)")
    parser.add_argument("--pg-port", type=int, default=5432, help="PostgreSQL port (default: 5432)")
    parser.add_argument("--ibmi-port", type=int, default=8471, help="Db2 for i port (default: 8471)")

    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument("--output-env", action="store_true",
                              help="Emit shell export lines (PG_SAT_HOST, PG_SAT_PORT, IBMI_SAT_HOST, IBMI_SAT_PORT) for eval/sourcing")
    output_group.add_argument("--output-json", action="store_true",
                              help="Emit a JSON object with the same four keys")

    args = parser.parse_args()

    # When emitting structured output, route all status messages to stderr
    # so that eval $(...) / JSON parsing only sees the structured lines on stdout.
    structured_output = args.output_env or args.output_json
    def log(*a, **kw):
        if structured_output:
            print(*a, **kw, file=sys.stderr)
        else:
            print(*a, **kw)

    log("🔑 Authenticating against IBM Cloud IAM...")
    token = get_iam_token(args.api_key)
    log("✅ IAM Token acquired.")

    log(f"\n📡 Querying existing endpoints on connector {args.connector_id}...")
    existing_endpoints = list_endpoints(token, args.account_id, args.connector_id)
    existing_map = {ep.get("display_name"): ep for ep in existing_endpoints}

    endpoints_to_create = [
        ("pg-olist", args.rhel_ip, args.pg_port),
        ("ibmi-db2", args.ibmi_ip, args.ibmi_port),
    ]

    for name, host, port in endpoints_to_create:
        if name in existing_map:
            ep = existing_map[name]
            log(f"ℹ️  Endpoint '{name}' already exists: {ep.get('client_host')}:{ep.get('client_port')} -> {ep.get('server_host')}:{ep.get('server_port')}")
        else:
            log(f"⚙️  Creating endpoint '{name}' -> {host}:{port} ...")
            created = create_endpoint(token, args.account_id, args.connector_id, name, host, port)
            if created:
                log(f"✅ Created '{name}': {created.get('client_host')}:{created.get('client_port')}")

    log("\n📋 Final Satellite Link Endpoints Summary:")
    log("=" * 70)
    final_endpoints = list_endpoints(token, args.account_id, args.connector_id)

    # Build lookup: endpoint name -> (client_host, client_port)
    endpoint_map = {}
    for ep in final_endpoints:
        name = ep.get("display_name")
        endpoint_map[name] = {
            "host": ep.get("client_host"),
            "port": ep.get("client_port"),
        }
        log(f"Name:        {name}")
        log(f"Cloud Host:  {ep.get('client_host')}:{ep.get('client_port')}")
        log(f"Target:      {ep.get('server_host')}:{ep.get('server_port')} ({ep.get('server_protocol')})")
        log(f"Status:      {ep.get('status')}")
        log("-" * 70)

    # Resolve the two endpoints we care about
    pg   = endpoint_map.get("pg-olist",   {})
    ibmi = endpoint_map.get("ibmi-db2",   {})

    if args.output_env:
        # Only the export lines go to stdout — everything else went to stderr via log()
        print(f"export PG_SAT_HOST={pg.get('host', '')}")
        print(f"export PG_SAT_PORT={pg.get('port', '')}")
        print(f"export IBMI_SAT_HOST={ibmi.get('host', '')}")
        print(f"export IBMI_SAT_PORT={ibmi.get('port', '')}")
    elif args.output_json:
        result = {
            "PG_SAT_HOST":   pg.get("host", ""),
            "PG_SAT_PORT":   pg.get("port", ""),
            "IBMI_SAT_HOST": ibmi.get("host", ""),
            "IBMI_SAT_PORT": ibmi.get("port", ""),
        }
        print(json.dumps(result, indent=2))
    else:
        # Human-readable hint for the next step
        if pg.get("host") and ibmi.get("host"):
            print()
            print("▶  Next step — run the federation connector script with these values:")
            print(f"   PG_HOST={pg['host']} PG_PORT={pg['port']} \\")
            print(f"   IBMI_HOST={ibmi['host']} IBMI_PORT={ibmi['port']} \\")
            print(f"   IBMI_PASSWORD='<ibmi_os_password>' \\")
            print(f"   python setup/5-add-federation-connectors.py")


if __name__ == "__main__":
    main()
