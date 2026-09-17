#!/usr/bin/env python3
"""
============================================================================
watsonx.data SaaS — Complete federation setup (connectors + access control)
============================================================================

Purpose
-------
Fully automated replacement for the GUI-based federation setup.  Covers
every step that previously required the watsonx.data console:

  Step 1.  Register ibmi_olist and pg_olist database connectors
           POST /lakehouse/api/v3/database_registrations
           (uses student App ID token — the catalog owner)

  Step 2.  Associate connectors with the Prestissimo engine
           POST /lakehouse/api/v3/{guid}/prestissimo_engines/{id}/catalogs
           (same student token — 409 Conflict = already associated, OK)

  Step 3.  Grant DataAccess to the service ID on both catalogs
           POST /lakehouse/api/v3/{guid}/catalogs/{name}/access
           This is the step we previously had to do manually in the GUI.
           Without it, the service API key gets HTTP 403 "USE catalog …
           permission check failed" from Presto C++.

  Step 4.  Resolve and print the Presto engine host:port
           GET /lakehouse/api/v3/prestissimo_engines
           Returns host_name and port — needed for WXD_PRESTO_HOST env var.

Authentication notes
--------------------
Two identities are in play:

  student_token   — from the student App ID API key (same key as
                    WXD_APIKEY / --wxd-apikey).  This identity OWNS the
                    catalogs and must be used for registration and access
                    grants.  Obtained via IAM apikey→token exchange.

  service_id      -- the TechZone Service ID (itz-110000sg2k-<env_key>).
                    This is the identity whose token is used at runtime by
                    the demo UI Presto queries.  It needs DataAccess on each
                    catalog, granted in Step 3.

The same API key covers both — the student App ID key IS the service key
on TechZone watsonx.data reservations.  The service ID name is the value
of WXD_SERVICE_ID (defaults to the environment ID, which equals the service
ID).

Usage
-----
    # Minimal — all required values via env vars:
    WXD_APIKEY=<student_key> \\
    WXD_INSTANCE_CRN=<crn> \\
    WXD_SERVICE_ID=itz-110000sg2k-limql82k \\
    IBMI_HOST=c-01.private.eu-gb.link.satellite.cloud.ibm.com \\
    IBMI_PORT=33180 \\
    IBMI_USERNAME=U5VZFHW \\
    IBMI_PASSWORD=<ibmi_password> \\
    PG_HOST=c-01.private.eu-gb.link.satellite.cloud.ibm.com \\
    PG_PORT=33156 \\
    python setup/5-add-federation-connectors.py

    # Dry-run (prints payloads, no API calls):
    python setup/5-add-federation-connectors.py --dry-run

    # Skip steps you've already done:
    python setup/5-add-federation-connectors.py --skip-register --skip-associate

    # Print the Presto host for use in .env.local:
    python setup/5-add-federation-connectors.py --print-presto-host

Obtaining the API key from TechZone automatically
-------------------------------------------------
If you have a TechZone API token, the key can be fetched programmatically:

    import requests
    resp = requests.get(
        f"https://api.techzone.ibm.com/v2/requests/{REQUEST_ID}",
        headers={"Authorization": f"Bearer {TECHZONE_TOKEN}"}
    )
    key = next(o["value"] for o in resp.json()["output"]
               if o["name"] == "service_api_key")
"""

import argparse
import json
import os
import sys
import time

import requests

IAM_TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"

CONFIG = {
    # --- watsonx.data SaaS ---
    "apikey":        os.environ.get("WXD_APIKEY", ""),
    "instance_crn":  os.environ.get("WXD_INSTANCE_CRN", ""),
    "region_host":   os.environ.get("WXD_REGION_HOST", "https://eu-gb.lakehouse.cloud.ibm.com"),
    "engine_id":     os.environ.get("WXD_ENGINE_ID", ""),   # auto-resolved if blank

    # Service ID that needs DataAccess grants (= TechZone environment ID)
    "service_id":    os.environ.get("WXD_SERVICE_ID", ""),

    # --- IBM i connector ---
    "ibmi_host":         os.environ.get("IBMI_HOST", ""),
    "ibmi_port":         os.environ.get("IBMI_PORT", ""),
    "ibmi_database":     os.environ.get("IBMI_DATABASE", "PVM02XE9"),
    "ibmi_username":     os.environ.get("IBMI_USERNAME", ""),
    "ibmi_password":     os.environ.get("IBMI_PASSWORD", ""),
    "ibmi_catalog_name": os.environ.get("IBMI_CATALOG_NAME", "ibmi_olist"),

    # --- PostgreSQL connector ---
    "pg_host":         os.environ.get("PG_HOST", ""),
    "pg_port":         os.environ.get("PG_PORT", ""),
    "pg_database":     os.environ.get("PG_DATABASE", "olist"),
    "pg_username":     os.environ.get("PG_USERNAME", "edbadmin"),
    "pg_password":     os.environ.get("PG_PASSWORD", "edbadmin1"),
    "pg_catalog_name": os.environ.get("PG_CATALOG_NAME", "pg_olist"),
}


def get_iam_token(apikey: str) -> str:
    resp = requests.post(
        IAM_TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
        data={"grant_type": "urn:ibm:params:oauth:grant-type:apikey", "apikey": apikey},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


class WxdClient:
    def __init__(self, region_host: str, token: str, instance_crn: str):
        self.base_url = f"{region_host.rstrip('/')}/lakehouse/api/v3"
        self.instance_guid = instance_crn.rstrip(":").split(":")[-1]
        self.instance_url = f"{self.base_url}/{self.instance_guid}"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "AuthInstanceId": instance_crn,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    # ------------------------------------------------------------------
    # Step 1 — connector registration
    # ------------------------------------------------------------------

    def list_database_registrations(self) -> list:
        resp = requests.get(
            f"{self.base_url}/database_registrations",
            headers=self.headers, timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("database_registrations", [])

    def add_database(self, payload: dict, dry_run: bool = False) -> dict:
        url = f"{self.base_url}/database_registrations"
        if dry_run:
            print(f"  [DRY RUN] POST {url}")
            print(f"  Payload: {json.dumps(payload, indent=4)}")
            return {"database_id": "dry-run", "display_name": payload.get("display_name")}
        resp = requests.post(url, headers=self.headers, json=payload, timeout=60)
        if resp.status_code >= 400:
            print(f"  ERROR {resp.status_code}: {resp.text}", file=sys.stderr)
            resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------
    # Step 2 — engine association
    # ------------------------------------------------------------------

    def list_prestissimo_engines(self) -> list:
        resp = requests.get(
            f"{self.base_url}/prestissimo_engines",
            headers=self.headers, timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("prestissimo_engines", [])

    def associate_database_with_engine(self, engine_id: str, catalog_name: str,
                                       dry_run: bool = False) -> dict:
        url = f"{self.instance_url}/prestissimo_engines/{engine_id}/catalogs"
        payload = {"catalog_names": [catalog_name]}
        if dry_run:
            print(f"  [DRY RUN] POST {url}  payload={payload}")
            return {}
        resp = requests.post(url, headers=self.headers, json=payload, timeout=30)
        if resp.status_code == 409:
            print(f"  Already associated (409 — OK).")
            return {}
        if resp.status_code >= 400:
            print(f"  ERROR {resp.status_code}: {resp.text}", file=sys.stderr)
            resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------
    # Step 3 — catalog access grants (the step that previously required the GUI)
    # ------------------------------------------------------------------

    def grant_catalog_access(self, catalog_name: str, service_id: str,
                             dry_run: bool = False) -> None:
        """Grant DataAccess on a catalog to the service ID (the runtime query identity).

        Endpoint: POST /lakehouse/api/v3/{guid}/catalogs/{catalog}/access
        Body:      { "groups": [], "users": [{"user_name": "<service_id>", "access": "can_use"}] }

        The "can_use" access level maps to Presto's USE CATALOG + SELECT permissions,
        which is what the demo UI needs to run federated queries.

        Without this, the service ID token gets:
            HTTP 403  "Access denied: USE catalog <name> - permission check failed"
        even though the catalog is registered and associated with the engine.
        """
        url = f"{self.instance_url}/catalogs/{catalog_name}/access"
        payload = {
            "groups": [],
            "users": [{"user_name": service_id, "access": "can_use"}],
        }
        if dry_run:
            print(f"  [DRY RUN] POST {url}")
            print(f"  Payload: {json.dumps(payload, indent=2)}")
            return
        resp = requests.post(url, headers=self.headers, json=payload, timeout=30)
        if resp.status_code == 409:
            print(f"  Access already granted (409 — OK).")
            return
        if resp.status_code == 404:
            # Endpoint may vary — try alternate path
            alt_url = f"{self.base_url}/catalogs/{catalog_name}/access"
            print(f"  404 on instance-scoped path, trying base path: {alt_url}")
            resp = requests.post(alt_url, headers=self.headers, json=payload, timeout=30)
        if resp.status_code >= 400:
            print(f"  WARN {resp.status_code}: {resp.text}", file=sys.stderr)
            print(f"  Access grant may need to be done manually in the console:", file=sys.stderr)
            print(f"    Access Control → Catalogs → {catalog_name} → Add access → {service_id} → DataAccess", file=sys.stderr)
            return   # non-fatal — connector still works, just the service key can't USE it
        print(f"  Access granted: {service_id} → {catalog_name} (can_use).")

    # ------------------------------------------------------------------
    # Step 4 — resolve Presto host:port for .env.local
    # ------------------------------------------------------------------

    def get_presto_host(self, engine_id: str) -> str:
        """Return the Presto engine's external host:port string for WXD_PRESTO_HOST."""
        engines = self.list_prestissimo_engines()
        for eng in engines:
            if eng.get("id") == engine_id or eng.get("engine_id") == engine_id:
                host = eng.get("host_name", "")
                port = eng.get("port", 443)
                if host:
                    return f"{host}:{port}"
        return ""


# ------------------------------------------------------------------
# Connector payload builders
# ------------------------------------------------------------------

def build_ibmi_payload(cfg: dict) -> dict:
    return {
        "display_name": cfg["ibmi_catalog_name"],
        "type": "db2fori",
        "associated_catalog": {
            "catalog_name": cfg["ibmi_catalog_name"],
            "catalog_type": "hive",
        },
        "description": "IBM i Db2 OLIST core ERP",
        "tags": ["ibm-i", "source-1", "olist"],
        "connection": {
            "name":     cfg["ibmi_database"],
            "hostname": cfg["ibmi_host"],
            "port":     int(cfg["ibmi_port"]),
            "username": cfg["ibmi_username"],
            "password": cfg["ibmi_password"],
            "ssl":      False,
        },
    }


def build_pg_payload(cfg: dict) -> dict:
    return {
        "display_name": cfg["pg_catalog_name"],
        "type": "postgresql",
        "associated_catalog": {
            "catalog_name": cfg["pg_catalog_name"],
            "catalog_type": "hive",
        },
        "description": "PostgreSQL 16 OLIST supplier DB",
        "tags": ["postgresql", "source-2", "olist"],
        "connection": {
            "name":     cfg["pg_database"],
            "hostname": cfg["pg_host"],
            "port":     int(cfg["pg_port"]),
            "username": cfg["pg_username"],
            "password": cfg["pg_password"],
            "ssl":      False,
        },
    }


# ------------------------------------------------------------------
# Per-connector orchestration
# ------------------------------------------------------------------

def setup_connector(client: WxdClient, catalog_name: str, payload: dict,
                    engine_id: str, service_id: str,
                    existing_names: list, args) -> None:
    # Step 1 — register
    if args.skip_register:
        print(f"  --skip-register: skipping registration of '{catalog_name}'.")
    elif catalog_name in existing_names:
        print(f"  Connector '{catalog_name}' already registered — skipping.")
    else:
        print(f"  Registering '{catalog_name}' ...")
        result = client.add_database(payload, dry_run=args.dry_run)
        print(f"  Registered: id={result.get('database_id', '?')}")
        time.sleep(2)

    # Step 2 — associate with engine
    if args.skip_associate:
        print(f"  --skip-associate: skipping engine association for '{catalog_name}'.")
    elif engine_id:
        print(f"  Associating '{catalog_name}' with engine '{engine_id}' ...")
        client.associate_database_with_engine(engine_id, catalog_name, dry_run=args.dry_run)
        print(f"  Association done.")
    else:
        print(f"  No engine found — skipping association.")

    # Step 3 — grant access to service ID
    if args.skip_grant:
        print(f"  --skip-grant: skipping access grant for '{catalog_name}'.")
    elif service_id:
        print(f"  Granting DataAccess: {service_id} → '{catalog_name}' ...")
        client.grant_catalog_access(catalog_name, service_id, dry_run=args.dry_run)
    else:
        print(f"  No WXD_SERVICE_ID set — skipping access grant.")
        print(f"  ⚠  Grant manually: Access Control → Catalogs → {catalog_name} → Add access → <service_id> → DataAccess")


# ------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Register federation connectors and grant catalog access in watsonx.data.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Key environment variables:
  WXD_APIKEY         Student App ID service API key (from TechZone reservation output)
  WXD_INSTANCE_CRN   watsonx.data instance CRN
  WXD_SERVICE_ID     TechZone service ID (= environment ID, e.g. itz-110000sg2k-limql82k)
                     This identity needs DataAccess on each catalog to run Presto queries.
  IBMI_HOST/PORT     Satellite Link endpoint for IBM i (Db2 port 8471)
  IBMI_USERNAME/PASSWORD  IBM i OS credentials
  PG_HOST/PORT       Satellite Link endpoint for PostgreSQL

Obtaining WXD_APIKEY automatically from TechZone:
  The key is at: techzone-get-request(REQUEST_ID).output[service_api_key].value
  Use the TechZone MCP tool or REST API rather than pasting it manually.
""",
    )
    parser.add_argument("--dry-run",        action="store_true", help="Print payloads, no API calls.")
    parser.add_argument("--ibmi-only",      action="store_true", help="Only configure the IBM i connector.")
    parser.add_argument("--pg-only",        action="store_true", help="Only configure the PostgreSQL connector.")
    parser.add_argument("--skip-register",  action="store_true", help="Skip Step 1 (connector registration).")
    parser.add_argument("--skip-associate", action="store_true", help="Skip Step 2 (engine association).")
    parser.add_argument("--skip-grant",     action="store_true", help="Skip Step 3 (catalog access grant).")
    parser.add_argument("--print-presto-host", action="store_true",
                        help="After setup, print WXD_PRESTO_HOST value for .env.local.")

    # Per-reservation overrides
    parser.add_argument("--ibmi-host",     default=None)
    parser.add_argument("--ibmi-port",     default=None)
    parser.add_argument("--ibmi-database", default=None)
    parser.add_argument("--ibmi-username", default=None)
    parser.add_argument("--ibmi-password", default=None)
    parser.add_argument("--pg-host",       default=None)
    parser.add_argument("--pg-port",       default=None)
    parser.add_argument("--wxd-apikey",    default=None)
    parser.add_argument("--wxd-crn",       default=None)
    parser.add_argument("--wxd-service-id", default=None,
                        help="TechZone service ID (e.g. itz-110000sg2k-limql82k)")

    args = parser.parse_args()

    # Apply CLI overrides
    if args.ibmi_host:      CONFIG["ibmi_host"]     = args.ibmi_host
    if args.ibmi_port:      CONFIG["ibmi_port"]     = args.ibmi_port
    if args.ibmi_database:  CONFIG["ibmi_database"] = args.ibmi_database
    if args.ibmi_username:  CONFIG["ibmi_username"] = args.ibmi_username
    if args.ibmi_password:  CONFIG["ibmi_password"] = args.ibmi_password
    if args.pg_host:        CONFIG["pg_host"]       = args.pg_host
    if args.pg_port:        CONFIG["pg_port"]       = args.pg_port
    if args.wxd_apikey:     CONFIG["apikey"]        = args.wxd_apikey
    if args.wxd_crn:        CONFIG["instance_crn"]  = args.wxd_crn
    if args.wxd_service_id: CONFIG["service_id"]    = args.wxd_service_id

    # Validate required values
    if not args.dry_run:
        missing = []
        for key, label in [("apikey", "WXD_APIKEY"), ("instance_crn", "WXD_INSTANCE_CRN")]:
            if not CONFIG[key]:
                missing.append(label)
        if not args.pg_only and not args.skip_register:
            for key, label in [
                ("ibmi_host",     "IBMI_HOST"),
                ("ibmi_port",     "IBMI_PORT"),
                ("ibmi_username", "IBMI_USERNAME"),
                ("ibmi_password", "IBMI_PASSWORD"),
            ]:
                if not CONFIG[key]:
                    missing.append(label)
        if not args.ibmi_only and not args.skip_register:
            for key, label in [("pg_host", "PG_HOST"), ("pg_port", "PG_PORT")]:
                if not CONFIG[key]:
                    missing.append(label)
        if missing:
            print("ERROR: missing required values:", file=sys.stderr)
            for m in missing:
                print(f"  {m}", file=sys.stderr)
            sys.exit(1)

    print("Fetching IAM token ...")
    if args.dry_run:
        token = "dry-run-token"
        print("  [DRY RUN] Skipping IAM call.")
    else:
        token = get_iam_token(CONFIG["apikey"])
    print("  Token obtained.")

    client = WxdClient(CONFIG["region_host"], token, CONFIG["instance_crn"])

    # Resolve engine ID
    engine_id = CONFIG["engine_id"]
    if not engine_id and not args.dry_run:
        print("Resolving engine ID ...")
        engines = client.list_prestissimo_engines()
        running = [e for e in engines if e.get("status", "").upper() in ("RUNNING", "ACTIVE", "READY")]
        if running:
            engine_id = running[0].get("engine_id") or running[0].get("id")
            print(f"  Engine: {running[0].get('display_name', engine_id)}  id={engine_id}")
        else:
            print("  WARNING: no running engine found.")

    # List existing connectors (idempotency)
    existing_names = []
    if not args.dry_run:
        print("Checking existing database registrations ...")
        existing = client.list_database_registrations()
        existing_names = [
            db.get("database_display_name") or db.get("database_id", "")
            for db in existing
        ]
        print(f"  Existing: {existing_names or '(none)'}")

    service_id = CONFIG["service_id"]
    if not service_id:
        print("⚠  WXD_SERVICE_ID not set — Step 3 (access grant) will be skipped.")
        print("   Set it to the TechZone environment ID, e.g. itz-110000sg2k-limql82k")
    print()

    # IBM i connector
    if not args.pg_only:
        print(f"=== IBM i connector ({CONFIG['ibmi_catalog_name']}) ===")
        setup_connector(client, CONFIG["ibmi_catalog_name"], build_ibmi_payload(CONFIG),
                        engine_id, service_id, existing_names, args)
        print()

    # PostgreSQL connector
    if not args.ibmi_only:
        print(f"=== PostgreSQL connector ({CONFIG['pg_catalog_name']}) ===")
        setup_connector(client, CONFIG["pg_catalog_name"], build_pg_payload(CONFIG),
                        engine_id, service_id, existing_names, args)
        print()

    # Step 4 — print Presto host for .env.local
    if args.print_presto_host and engine_id and not args.dry_run:
        print("=== Presto engine endpoint ===")
        presto_host = client.get_presto_host(engine_id)
        if presto_host:
            print(f"  WXD_PRESTO_HOST={presto_host}")
            print(f"  Add this to demo-ui/.env.local on the RHEL VM.")
        else:
            print("  Could not resolve Presto host — check engine status.")

    print("Done.")
    print(f"  Verify: SHOW SCHEMAS IN {CONFIG['pg_catalog_name']};")
    if not args.pg_only:
        print(f"  Verify: SHOW SCHEMAS IN {CONFIG['ibmi_catalog_name']};")


if __name__ == "__main__":
    main()
