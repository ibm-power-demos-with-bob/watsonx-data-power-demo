#!/usr/bin/env python3
"""
============================================================================
watsonx.data SaaS — REST API provisioning script
============================================================================

Purpose
-------
Recreates, via the watsonx.data v3 REST API, the same infrastructure that
the Infrastructure Manager wizard configures by hand, from a completely
fresh TechZone reservation with no engine, catalog, or bucket yet:

  1. Register the COS bucket as an object store + create an Apache Iceberg
     catalog on it (one combined call)
  2. Create the Prestissimo (Presto C++) engine, with the catalog already
     associated at creation time (also one combined call)

This exists so a fresh TechZone re-provision (see _checkpoint.md, Next
Steps) can be brought to a query-ready state in one script run instead
of the manual UI wizard + several clicks — this is the automation a new
user of this Client Engineering recipe would run against their own,
brand-new reservation.

⚠️ IMPORTANT — credentials
---------------------------
Use the STUDENT App ID credentials / STUDENT service API key, not your IBM ID.
The IBM ID does not have sufficient metastore (MDS) permissions and catalog
creation will fail with `SYSTEM_ERROR 400`. See _checkpoint.md for the
rationale.

⚠️ IMPORTANT — catalog naming
-------------------------------
The metastore catalog namespace is scoped at the ACCOUNT level, not per-user.
Choose a catalog name that has not been used before on this account (see
_checkpoint.md — `iceberg_data` is already orphaned on this account from an
earlier IBM ID session and cannot be reused). Reusing an existing name causes
a `SYSTEM_ERROR 400` that looks identical to the IBM ID permissions error —
check both possibilities if you hit a 400.

Endpoints and payload shapes below were confirmed by capturing the live
Infrastructure Manager console's own network calls via Chrome DevTools
(2026-08), against a real fresh bucket + catalog + engine creation.

Required configuration (fill in below or pass as environment variables)
-------------------------------------------------------------------------
WXD_APIKEY           Student IBM Cloud service API key (used to fetch an IAM token)
WXD_INSTANCE_CRN     CRN of the watsonx.data SaaS instance
                      (visible in the console URL as ?crn=... or via
                      Resource list -> instance -> Details -> CRN)
WXD_REGION_HOST       Console/API host for the instance's region, e.g.
                      https://eu-gb.lakehouse.cloud.ibm.com  (London)
                      NOTE: no "api." prefix.
WXD_ENGINE_DISPLAY_NAME   Display name for the new Presto C++ engine, e.g. "presto-demo"

COS_BUCKET_NAME       e.g. watsonx-data-a29df4cf-abfc-4907-a79c-59223d766db9
COS_ENDPOINT          Direct COS endpoint, e.g.
                      https://s3.direct.eu-gb.cloud-object-storage.appdomain.cloud
COS_ACCESS_KEY        HMAC access key
COS_SECRET_KEY        HMAC secret key
COS_REGION            COS bucket region, e.g. eu-gb
COS_BUCKET_DISPLAY_NAME   Friendly name shown in Infrastructure manager
CATALOG_NAME          e.g. iceberg_data (see naming note above — use a name
                       not already used on this account)

Usage
-----
    pip install requests
    # set the env vars above, or edit the CONFIG block below
    python 4-provision-via-rest-api.py
"""

import os
import sys
import time
import requests

# ----------------------------------------------------------------------------
# CONFIG — fill in directly or override via environment variables
# ----------------------------------------------------------------------------
CONFIG = {
    "apikey": os.environ.get("WXD_APIKEY", ""),
    "instance_crn": os.environ.get("WXD_INSTANCE_CRN", ""),
    # NOTE: no "api." prefix — DNS only resolves "<region>.lakehouse.cloud.ibm.com"
    "region_host": os.environ.get("WXD_REGION_HOST", "https://eu-gb.lakehouse.cloud.ibm.com"),
    "engine_display_name": os.environ.get("WXD_ENGINE_DISPLAY_NAME", "presto-demo"),

    "cos_bucket_name": os.environ.get("COS_BUCKET_NAME", ""),
    "cos_endpoint": os.environ.get("COS_ENDPOINT", ""),
    "cos_access_key": os.environ.get("COS_ACCESS_KEY", ""),
    "cos_secret_key": os.environ.get("COS_SECRET_KEY", ""),
    "cos_region": os.environ.get("COS_REGION", "eu-gb"),
    "cos_bucket_display_name": os.environ.get("COS_BUCKET_DISPLAY_NAME", "wxdata-iceberg-store"),

    "catalog_name": os.environ.get("CATALOG_NAME", "iceberg_data"),
}

IAM_TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"


def get_iam_token(apikey: str) -> str:
    """Exchange the student IBM Cloud API key for a bearer token."""
    resp = requests.post(
        IAM_TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
        data={
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": apikey,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


class WxdClient:
    def __init__(self, region_host: str, token: str, instance_crn: str):
        self.base_url = f"{region_host.rstrip('/')}/lakehouse/api/v3"
        # Both storage_registrations and prestissimo_engines are scoped under
        # the instance GUID in the URL path itself — GUID is the last
        # ':'-delimited segment of the CRN before the trailing "::", e.g.
        # crn:v1:bluemix:public:lakehouse:eu-gb:a/<account>:<instance_guid>::
        self.instance_guid = instance_crn.rstrip(":").split(":")[-1]
        self.instance_url = f"{self.base_url}/{self.instance_guid}"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "AuthInstanceId": instance_crn,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def register_bucket_and_catalog(self, cfg: dict) -> dict:
        """Register the COS bucket and create an Iceberg catalog on it in one call.

        Confirmed via DevTools capture against the live console (2026-08):
        POST /lakehouse/api/v3/{instance_guid}/storage_registrations
        """
        body = {
            "associated_catalogs": [
                {
                    "base_path": f"/{cfg['catalog_name']}/",
                    "catalog_name": cfg["catalog_name"],
                    "catalog_tags": [],
                    "catalog_type": "iceberg",
                }
            ],
            "connection": {
                "auth_mode": "hmac",
                "endpoint": cfg["cos_endpoint"],
                "name": cfg["cos_bucket_name"],
                "access_key": cfg["cos_access_key"],
                "secret_key": cfg["cos_secret_key"],
            },
            "description": "Provisioned via 4-provision-via-rest-api.py",
            "display_name": cfg["cos_bucket_display_name"],
            "managed_by": "customer",
            "region": cfg["cos_region"],
            "tags": [],
            "type": "ibm_cos",
        }
        resp = requests.post(
            f"{self.instance_url}/storage_registrations",
            headers=self.headers, json=body, timeout=60,
        )
        if resp.status_code >= 400:
            print(f"ERROR: bucket/catalog registration failed: {resp.status_code} {resp.text}", file=sys.stderr)
            resp.raise_for_status()
        return resp.json()

    def create_engine_with_catalog(self, cfg: dict) -> dict:
        """Create the Prestissimo (Presto C++) engine with the catalog already
        associated at creation time — this is the real flow for a fresh
        environment; there is no separate "associate catalog" call.

        Confirmed via DevTools capture against the live console (2026-08):
        POST /lakehouse/api/v3/{instance_guid}/prestissimo_engines
        """
        body = {
            "description": "",
            "associated_catalogs": [cfg["catalog_name"]],
            "configuration": {
                "coordinator": {"node_type": "bx2.48x192", "quantity": 1},
                "worker": {"node_type": "bx2.48x192", "quantity": 1},
                "size_config": "starter",
            },
            "display_name": cfg["engine_display_name"],
            "origin": "native",
        }
        resp = requests.post(
            f"{self.instance_url}/prestissimo_engines",
            headers=self.headers, json=body, timeout=60,
        )
        if resp.status_code >= 400:
            print(f"ERROR: engine creation failed: {resp.status_code} {resp.text}", file=sys.stderr)
            resp.raise_for_status()
        return resp.json()

    def list_catalogs(self) -> dict:
        resp = requests.get(f"{self.base_url}/catalogs", headers=self.headers, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def list_prestissimo_engines(self) -> dict:
        resp = requests.get(f"{self.base_url}/prestissimo_engines", headers=self.headers, timeout=30)
        resp.raise_for_status()
        return resp.json()


def validate_config(cfg: dict) -> None:
    missing = [k for k, v in cfg.items() if not v]
    if missing:
        print("ERROR: Missing required configuration values:", ", ".join(missing), file=sys.stderr)
        print("   Set them as environment variables or edit the CONFIG block in this script.", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    validate_config(CONFIG)

    print("Fetching IAM token (student API key)...")
    token = get_iam_token(CONFIG["apikey"])

    client = WxdClient(CONFIG["region_host"], token, CONFIG["instance_crn"])

    print(f"Registering COS bucket '{CONFIG['cos_bucket_display_name']}' "
          f"and creating catalog '{CONFIG['catalog_name']}'...")
    bucket_result = client.register_bucket_and_catalog(CONFIG)
    print("   Done:", bucket_result.get("id", bucket_result))

    # Give the metastore a moment to settle before engine creation
    time.sleep(5)

    print(f"Creating engine '{CONFIG['engine_display_name']}' with catalog "
          f"'{CONFIG['catalog_name']}' associated...")
    engine_result = client.create_engine_with_catalog(CONFIG)
    print("   Done:", engine_result.get("id", engine_result), "- status:", engine_result.get("status"))

    print("Verifying via GET /catalogs...")
    catalogs = client.list_catalogs()
    names = [c.get("catalog_name") for c in catalogs.get("catalogs", [])]
    print("   Catalogs visible:", names)

    if CONFIG["catalog_name"] in names:
        print(f"\nProvisioning complete — '{CONFIG['catalog_name']}' is ready. "
              f"The engine may still show status PROVISIONING for a few minutes. "
              f"Run SHOW CATALOGS in the Query workspace to confirm once it shows RUNNING.")
    else:
        print(f"\nCatalog '{CONFIG['catalog_name']}' was not found in the list. Check the console.")


if __name__ == "__main__":
    main()
