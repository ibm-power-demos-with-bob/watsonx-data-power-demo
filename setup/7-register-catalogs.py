#!/usr/bin/env python3
"""
===========================================================================
watsonx.data Developer Base Image — catalog registration + access control
===========================================================================

Registers pg_olist and ibmi_olist via the lhconsole-api v2 endpoint,
using the same authentication path the GUI uses:
  - secret: <LH_INSTANCE_SECRET>  (obtained from Presto container env)
  - Authorization: Bearer <JWT>   (obtained from /v3/auth/authenticate
                                   using ibmlhadmin/password — tip from
                                   Rehan Shahid, IBM Power AI Solutions)

Using both headers causes lhconsole-api to register the catalog with a
proper owner identity, which activates the Access Control tab and makes
the catalog visible in SHOW CATALOGS via Presto.

Compared to previous attempts that used only the secret: header, this
approach replicates what the GUI sends and avoids the "orphan catalog"
problem where the catalog registered but AMS would not serve it.

Dev Image SSH credentials are fixed for this environment type:
  Host:     eu-de.services.cloud.techzone.ibm.com  (does not change)
  Port:     (changes per reservation — pass via WXD_SSH_PORT)
  User:     watsonx                                 (does not change)
  Password: watsonx.data                            (does not change)

The only per-reservation values are:
  WXD_SSH_PORT   — SSH port from TechZone reservation page
  IBMI_PASSWORD  — IBM i OS password (changes every reservation)
  IBMI_USERNAME  — IBM i OS username (changes every reservation)
  IBMI_DATABASE  — IBM i RDB name   (changes every reservation)
  IBMI_PORT      — Satellite endpoint port for IBM i
  PG_PORT        — Satellite endpoint port for PostgreSQL

Usage
-----
    # Preferred: just run the script — it reads from setup/reservation.py
    python3 setup/7-register-catalogs.py

    # Override specific values via environment variables if needed:
    WXD_SSH_PORT=XXXXX \
    IBMI_PASSWORD='YOUR_PASSWORD' \
    python3 setup/7-register-catalogs.py

    # Dry run (prints payloads and commands, no changes):
    python3 setup/7-register-catalogs.py --dry-run

    # Skip catalog registration if already done, just bump policy version:
    WXD_SSH_PORT=28699 IBMI_PASSWORD=... python3 setup/7-register-catalogs.py --skip-register

After this script completes successfully, run:
    python3 setup/test_cross_catalog_join.py
to confirm end-to-end federation is working.
"""

import argparse
import json
import os
import sys
import time

import paramiko
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ---------------------------------------------------------------------------
# Configuration — reads from reservation.py; override with env vars if needed
# ---------------------------------------------------------------------------
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import reservation as _r
    _d = {
        "wxd_host":     _r.WXD_HOST,
        "wxd_ssh_port": _r.WXD_SSH_PORT,
        "wxd_ssh_user": _r.WXD_SSH_USER,
        "wxd_ssh_pass": _r.WXD_SSH_PASS,
        "ibmi_username": _r.SSH_USER,
        "ibmi_password": _r.IBMI_PASSWORD,
        "ibmi_database": _r.IBMI_RDB,
        "pg_password":   _r.PG_PASSWORD,
    }
except Exception as _e:
    print(f"Warning: could not load reservation.py: {_e}", file=sys.stderr)
    _d = {}

CONFIG = {
    # Dev Image SSH — port changes every reservation
    "wxd_host":     os.environ.get("WXD_HOST",     _d.get("wxd_host",     "eu-de.services.cloud.techzone.ibm.com")),
    "wxd_ssh_port": int(os.environ.get("WXD_SSH_PORT", str(_d.get("wxd_ssh_port", "22")))),
    "wxd_ssh_user": os.environ.get("WXD_SSH_USER", _d.get("wxd_ssh_user", "watsonx")),
    "wxd_ssh_pass": os.environ.get("WXD_SSH_PASS", _d.get("wxd_ssh_pass", "watsonx.data")),

    # Internal API — fixed inside the Dev Image container network
    "lh_api_ip":      os.environ.get("LH_API_IP",      "172.18.0.4"),
    "lh_api_port":    os.environ.get("LH_API_PORT",     "3333"),
    "lh_instance_id": os.environ.get("LH_INSTANCE_ID",  "0000-0000-0000-0000"),
    "lh_secret":      os.environ.get("LH_SECRET",       ""),  # auto-discovered if blank

    # IBM i connector — all values change every reservation
    "ibmi_host":         os.environ.get("IBMI_HOST",         "c-01.private.eu-gb.link.satellite.cloud.ibm.com"),
    "ibmi_port":         int(os.environ.get("IBMI_PORT",     "33180")),
    "ibmi_database":     os.environ.get("IBMI_DATABASE",     _d.get("ibmi_database", "")),
    "ibmi_username":     os.environ.get("IBMI_USERNAME",     _d.get("ibmi_username", "")),
    "ibmi_password":     os.environ.get("IBMI_PASSWORD",     _d.get("ibmi_password", "")),
    "ibmi_catalog_name": os.environ.get("IBMI_CATALOG_NAME", "ibmi_olist"),

    # PostgreSQL connector — credentials fixed by _setup_pg.py / 8-load-edb-olist.py
    "pg_host":         os.environ.get("PG_HOST",         "c-01.private.eu-gb.link.satellite.cloud.ibm.com"),
    "pg_port":         int(os.environ.get("PG_PORT",     "33156")),
    "pg_database":     os.environ.get("PG_DATABASE",     "olist"),
    "pg_username":     os.environ.get("PG_USERNAME",     "edbadmin"),
    "pg_password":     os.environ.get("PG_PASSWORD",     _d.get("pg_password", "edbadmin")),
    "pg_catalog_name": os.environ.get("PG_CATALOG_NAME", "pg_olist"),

    # Presto engine ID — fixed in Dev Image
    "engine_id": os.environ.get("ENGINE_ID", "presto-01"),
}


# ---------------------------------------------------------------------------
# SSH helpers
# ---------------------------------------------------------------------------

def _ssh_connect(cfg) -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        cfg["wxd_host"], port=cfg["wxd_ssh_port"],
        username=cfg["wxd_ssh_user"], password=cfg["wxd_ssh_pass"],
        timeout=30,
    )
    return client


def ssh_exec(cfg, command: str) -> tuple[str, str]:
    """Run a single command on the Dev Image VM. Returns (stdout, stderr)."""
    client = _ssh_connect(cfg)
    _, stdout, stderr = client.exec_command(command)
    out = stdout.read().decode()
    err = stderr.read().decode()
    client.close()
    return out, err


def ssh_psql(cfg, sql: str, label: str = "") -> str:
    """Run SQL inside the ibm-lh-postgres container. Returns stdout."""
    client = _ssh_connect(cfg)
    sftp = client.open_sftp()
    remote_file = "/tmp/_wxd_setup.sql"
    with sftp.file(remote_file, "w") as f:
        f.write(sql)
    sftp.close()
    cmd = (
        f"sudo docker cp {remote_file} ibm-lh-postgres:{remote_file} && "
        f"sudo docker exec ibm-lh-postgres psql -U admin -d ibm_lh_repo -f {remote_file}"
    )
    _, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode()
    err = stderr.read().decode()
    client.close()
    if err.strip():
        print(f"  [stderr{' ' + label if label else ''}] {err.strip()[:300]}", file=sys.stderr)
    return out


def ssh_run_script(cfg, script: str) -> str:
    """Upload and run a shell script on the Dev Image VM. Returns stdout."""
    client = _ssh_connect(cfg)
    sftp = client.open_sftp()
    with sftp.file("/tmp/_wxd_script.sh", "w") as f:
        f.write(script)
    sftp.close()
    _, stdout, stderr = client.exec_command("bash /tmp/_wxd_script.sh")
    out = stdout.read().decode()
    err = stderr.read().decode()
    client.close()
    if err.strip():
        print(f"  [stderr] {err.strip()[:300]}", file=sys.stderr)
    return out


# ---------------------------------------------------------------------------
# Step 1 — Obtain a watsonx.data JWT via /v2/auth/authenticate
# ---------------------------------------------------------------------------
# Dev Image v2.2.0 (lhconsole-api:2.2.0) exposes the authenticate endpoint at:
#   POST https://localhost:9443/lakehouse/api/v2/auth/authenticate
# Body: { "username": "ibmlhadmin", "password": "password",
#         "instance_id": "0000-0000-0000-0000", "instance_name": "lh-default" }
# Returns: { "accessToken": "<JWT>", ... }
#
# The instance_name value is arbitrary — the API validates it is present but
# does not check it against any stored value.  We use the value from
# LH_INSTANCE_NAME in the container env ("lh-default") for clarity.
#
# Port 9443 is the external HTTPS port of lhconsole-ui (nginx), which proxies
# /lakehouse/api/v2/* through to lhconsole-api:3333.  This is the same port
# that the browser UI uses, so it is always available.
# ---------------------------------------------------------------------------

def get_lh_token(cfg, dry_run: bool = False) -> str:
    """Obtain a JWT from the Dev Image authenticate endpoint (called from inside the VM)."""
    if dry_run:
        print("  [DRY RUN] Would call /v2/auth/authenticate — returning placeholder token.")
        return "dry-run-jwt-token"

    print("  Obtaining JWT from /lakehouse/api/v2/auth/authenticate ...")
    script = """#!/bin/sh
curl -sk -X POST \\
  -H "Content-Type: application/json" \\
  -d '{"username":"ibmlhadmin","password":"password","instance_id":"0000-0000-0000-0000","instance_name":"lh-default"}' \\
  https://localhost:9443/lakehouse/api/v2/auth/authenticate
echo ""
"""
    out = ssh_run_script(cfg, script)
    out = out.strip()
    if not out:
        raise RuntimeError(
            "Empty response from /v2/auth/authenticate — "
            "check that port 9443 is reachable on the Dev Image VM."
        )
    try:
        data = json.loads(out)
    except Exception:
        raise RuntimeError(f"Non-JSON response from authenticate endpoint: {out[:300]}")

    # v2.2 response key is "accessToken"
    token = (
        data.get("accessToken") or
        data.get("access_token") or
        data.get("token") or
        data.get("LHToken") or
        data.get("lhToken")
    )
    if not token:
        raise RuntimeError(
            f"Authenticate response did not contain a token. "
            f"Full response: {out[:400]}\n"
            "Expected key: accessToken (v2.2+) or token/access_token (older versions)."
        )
    print(f"  JWT obtained ({len(token)} chars).")
    return token


# ---------------------------------------------------------------------------
# Step 2 — Discover LH_INSTANCE_SECRET (needed for policy version bump)
# ---------------------------------------------------------------------------

def discover_secret(cfg) -> str:
    print("  Discovering LH_INSTANCE_SECRET from Presto container...")
    out, _ = ssh_exec(cfg, "sudo docker exec ibm-lh-presto env | grep LH_INSTANCE_SECRET")
    for line in out.splitlines():
        if "LH_INSTANCE_SECRET=" in line:
            secret = line.split("=", 1)[1].strip()
            print(f"  Secret: {secret[:8]}...")
            return secret
    raise RuntimeError("Could not discover LH_INSTANCE_SECRET from Presto container.")


# ---------------------------------------------------------------------------
# Step 3 — Register catalogs via lhconsole-api v2 (same path as the GUI)
# ---------------------------------------------------------------------------
# Dev Image v2.2.0 API path (confirmed from nginx proxy_pass.conf):
#   POST https://localhost:9443/lakehouse/api/v2/0000-0000-0000-0000/database_registrations
#   nginx rewrites this to → lhconsole-api:3333/lakehouse/api/v2/database_registrations
#
#   Headers:
#     Authorization: Bearer <JWT from /v2/auth/authenticate>
#     LhInstanceId: 0000-0000-0000-0000
#     AuthInstanceId: 0000-0000-0000-0000
#     Content-Type: application/json
#
# The Bearer JWT (obtained via get_lh_token) gives the request full owner
# identity — this is what activates the Access Control tab and makes
# SHOW CATALOGS work without manual GUI intervention.
# ---------------------------------------------------------------------------

def _api_register_one(cfg, secret: str, jwt: str, payload: dict, dry_run: bool) -> dict:
    """POST one database_registration payload via SSH → lhconsole-api (v2.2 path)."""
    iid  = cfg["lh_instance_id"]
    # Use port 9443 (external nginx) — always available. nginx strips the instance_id
    # from the URL before forwarding to lhconsole-api:3333.
    url  = f"https://localhost:9443/lakehouse/api/v2/{iid}/database_registrations"

    payload_json = json.dumps(payload).replace("'", "'\\''")  # escape for shell

    script = f"""#!/bin/sh
JWT="{jwt}"
IID="{iid}"
curl -sk -X POST \\
  -H "Authorization: Bearer $JWT" \\
  -H "LhInstanceId: $IID" \\
  -H "AuthInstanceId: $IID" \\
  -H "Content-Type: application/json" \\
  -d '{payload_json}' \\
  "https://localhost:9443/lakehouse/api/v2/$IID/database_registrations"
echo ""
"""
    if dry_run:
        print(f"  [DRY RUN] Would POST to {url}")
        print(f"  Payload: {json.dumps(payload, indent=4)}")
        return {}

    out = ssh_run_script(cfg, script)
    try:
        result = json.loads(out)
        if "database_registrations" in result:
            reg = result["database_registrations"][0]
            print(f"  Registered: id={reg.get('database_id','?')}  catalog={reg.get('associated_catalog',{}).get('catalog_name','?')}")
            return reg
        elif result.get("status_code", 0) >= 400:
            msg = result.get("message", out)
            if "already exists" in str(msg).lower() or "duplicate" in str(msg).lower():
                print(f"  Already registered (conflict) — skipping.")
                return {}
            print(f"  ERROR {result.get('status_code')}: {msg}")
            return {}
        else:
            print(f"  Response: {str(result)[:200]}")
            return result
    except Exception:
        print(f"  Raw response: {out.strip()[:300]}")
        return {}


def register_catalogs(cfg, secret: str, jwt: str, dry_run: bool) -> None:
    """Register pg_olist and ibmi_olist via the lhconsole-api v2 endpoint."""
    pg   = cfg["pg_catalog_name"]
    ibmi = cfg["ibmi_catalog_name"]

    # v2.2: username/password go inside database_details, not at the top level
    pg_payload = {
        "database_display_name": pg,
        "database_type": "postgresql",
        "database_details": {
            "database_name": cfg["pg_database"],
            "hostname":      cfg["pg_host"],
            "port":          cfg["pg_port"],
            "username":      cfg["pg_username"],
            "password":      cfg["pg_password"],
        },
        "associated_catalog": {"catalog_name": pg},
        "tags": [],
        "description": "PostgreSQL 16 Operational DB",
    }

    ibmi_payload = {
        "database_display_name": ibmi,
        "database_type": "db2fori",
        "database_details": {
            "database_name": cfg["ibmi_database"],
            "hostname":      cfg["ibmi_host"],
            "port":          cfg["ibmi_port"],
            "username":      cfg["ibmi_username"],
            "password":      cfg["ibmi_password"],
        },
        "associated_catalog": {"catalog_name": ibmi},
        "tags": [],
        "description": "IBM i Db2 Core ERP",
    }

    print(f"  Registering {pg} ...")
    _api_register_one(cfg, secret, jwt, pg_payload, dry_run)

    print(f"  Registering {ibmi} ...")
    _api_register_one(cfg, secret, jwt, ibmi_payload, dry_run)


# ---------------------------------------------------------------------------
# Step 3 — Insert AMS policy rows (access control)
# ---------------------------------------------------------------------------

def insert_ams_policies(cfg, dry_run: bool) -> None:
    """
    Insert grant (g) rows into ams_0000_0000_0000_0000 using the exact same
    pattern the GUI writes when it registers a catalog via Infrastructure Manager.

    Observed from hive_data (a GUI-registered catalog that shows correctly in
    the Access Control view and has an active Access control tab):

      g | Administrator | can_administer | catalogs/hive_data
      g | User          | can_use        | catalogs/hive_data

    The GUI does NOT write per-catalog 'p' rows — those are covered by the
    global wildcard 'p' rows already present (catalogs/*, buckets/*, etc.).
    Writing our own 'p' rows was incorrect and caused the Access control tab
    to be greyed out (catalog appeared unowned by lhconsole-api).

    The 'g' rows here follow the role-hierarchy pattern:
      - Administrator role gets can_administer on the catalog
      - User role gets can_use on the catalog
    This makes the catalog appear in the Access Control list and allows
    ibmlhadmin (who has the Administrator role globally) to administer it.
    """
    pg = cfg["pg_catalog_name"]
    ibmi = cfg["ibmi_catalog_name"]

    sql = f"""
-- Grant rows matching the exact pattern the GUI writes for catalog registration
-- (role → permission_level → resource, NOT user → role → resource)
INSERT INTO ams_0000_0000_0000_0000 (ptype, v0, v1, v2)
VALUES
  ('g', 'Administrator', 'can_administer', 'catalogs/{pg}'),
  ('g', 'User',          'can_use',        'catalogs/{pg}'),
  ('g', 'Administrator', 'can_administer', 'catalogs/{ibmi}'),
  ('g', 'User',          'can_use',        'catalogs/{ibmi}')
ON CONFLICT DO NOTHING;
"""

    if dry_run:
        print("  [DRY RUN] Would insert AMS rows:")
        print(sql)
        return

    out = ssh_psql(cfg, sql, "AMS policy insert")
    print(f"  Result: {out.strip()[:200]}")


# ---------------------------------------------------------------------------
# Step 4 — Bump policy version so Presto picks up the grants immediately
# ---------------------------------------------------------------------------

def bump_policy_version(cfg, secret: str, dry_run: bool) -> None:
    """
    POST to /access/policy_versions forces lhconsole-api to increment the
    policy cache version. Presto's PolicySyncMgr sees the version change on
    its next poll (~5s) and reloads from the DB — making the grants live
    without a full Presto restart.
    Uses port 9443 (nginx external) which proxies to lhconsole-api:3333.
    """
    iid = cfg["lh_instance_id"]
    pg = cfg["pg_catalog_name"]
    ibmi = cfg["ibmi_catalog_name"]
    base = f"https://localhost:9443/lakehouse/api/v2"

    script = f"""#!/bin/sh
BASE="{base}"
SECRET="{secret}"
IID="{iid}"

echo "=== Bumping policy version ==="
curl -sk -X POST \\
  -H "secret: $SECRET" -H "LhInstanceId: $IID" -H "AuthInstanceId: $IID" \\
  -H "Content-Type: application/json" \\
  "$BASE/access/policy_versions"
echo ""

echo "=== Verifying policies for {pg} and {ibmi} ==="
curl -sk \\
  -H "secret: $SECRET" -H "LhInstanceId: $IID" -H "AuthInstanceId: $IID" \\
  "$BASE/access/policies?catalog_list={pg},{ibmi}&engine_list=presto-01"
echo ""
"""

    if dry_run:
        print("  [DRY RUN] Would run policy bump script.")
        return

    out = ssh_run_script(cfg, script)
    print(f"  Policy bump response: {out.strip()[:300]}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Register federation catalogs via lhconsole-api in watsonx.data Dev Image.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--dry-run",        action="store_true", help="Print payloads/commands, no changes.")
    parser.add_argument("--skip-register",  action="store_true", help="Skip catalog registration (already done).")
    parser.add_argument("--skip-bump",      action="store_true", help="Skip policy version bump.")
    parser.add_argument("--ibmi-password",  default=None, help="IBM i OS password (overrides IBMI_PASSWORD env var).")
    parser.add_argument("--ibmi-username",  default=None, help="IBM i OS username (overrides IBMI_USERNAME env var).")
    parser.add_argument("--ibmi-database",  default=None, help="IBM i RDB name (overrides IBMI_DATABASE env var).")
    parser.add_argument("--ibmi-port",      default=None, type=int, help="Satellite endpoint port for IBM i.")
    parser.add_argument("--pg-port",        default=None, type=int, help="Satellite endpoint port for PostgreSQL.")
    args = parser.parse_args()

    if args.ibmi_password: CONFIG["ibmi_password"] = args.ibmi_password
    if args.ibmi_username: CONFIG["ibmi_username"] = args.ibmi_username
    if args.ibmi_database: CONFIG["ibmi_database"] = args.ibmi_database
    if args.ibmi_port:     CONFIG["ibmi_port"]     = args.ibmi_port
    if args.pg_port:       CONFIG["pg_port"]       = args.pg_port

    if not CONFIG["ibmi_password"] and not args.dry_run:
        print("ERROR: IBMI_PASSWORD must be set — it is the IBM i OS password and changes per reservation.", file=sys.stderr)
        print("  Set it via: IBMI_PASSWORD='<password>' python3 setup/7-register-catalogs.py", file=sys.stderr)
        print("  The password is on the TechZone reservation details page.", file=sys.stderr)
        sys.exit(1)

    print(f"watsonx.data Dev Image catalog registration")
    print(f"  Host: {CONFIG['wxd_host']}:{CONFIG['wxd_ssh_port']}")
    print(f"  IBM i: {CONFIG['ibmi_username']}@{CONFIG['ibmi_host']}:{CONFIG['ibmi_port']}  db={CONFIG['ibmi_database']}")
    print(f"  PostgreSQL: {CONFIG['pg_host']}:{CONFIG['pg_port']}  db={CONFIG['pg_database']}")
    print()

    # Step 0 — obtain JWT (needed for owner-identity registration)
    print("=== Step 0: Obtain JWT from authenticate endpoint ===")
    jwt = get_lh_token(CONFIG, dry_run=args.dry_run)
    print()

    # Step 1 — obtain secret (needed for policy bump)
    print("=== Step 1: Discover LH_INSTANCE_SECRET ===")
    secret = CONFIG["lh_secret"] or discover_secret(CONFIG)
    CONFIG["lh_secret"] = secret
    print()

    # Step 2 — register catalogs via lhconsole-api (same path as GUI, with JWT)
    if not args.skip_register:
        print("=== Step 2: Register catalogs via lhconsole-api v2 ===")
        register_catalogs(CONFIG, secret, jwt, dry_run=args.dry_run)
        print()

    # Step 3 — policy version bump (makes Presto pick up new catalogs immediately)
    if not args.skip_bump:
        print("=== Step 3: Bump policy version ===")
        bump_policy_version(CONFIG, secret, dry_run=args.dry_run)
        print()
        if not args.dry_run:
            print("  Waiting 10s for Presto PolicySyncMgr to reload...")
            time.sleep(10)

    # Step 4 — insert catalog_engine rows so Presto knows about the new catalogs,
    # then restart Presto to load them (policy bump alone is not sufficient in v2.2).
    if not args.skip_register and not args.dry_run:
        print("=== Step 4: Link catalogs to Presto engine in catalog_engine table ===")
        pg   = CONFIG["pg_catalog_name"]
        ibmi = CONFIG["ibmi_catalog_name"]
        iid  = CONFIG["lh_instance_id"]
        sql = f"""
INSERT INTO catalog_engine (engine_id, engine_name, catalog_name, instance_id)
VALUES
  ('presto-01', 'presto-01', '{pg}',   '{iid}'),
  ('presto-01', 'presto-01', '{ibmi}', '{iid}')
ON CONFLICT DO NOTHING;
"""
        out = ssh_psql(CONFIG, sql, "catalog_engine insert")
        print(f"  {out.strip()[:200]}")
        print()

        print("=== Step 5: Restart Presto to pick up new catalog_engine rows ===")
        print("  Sending restart command...")
        ssh_exec(CONFIG, "sudo docker restart ibm-lh-presto")
        print("  Waiting 75s for Presto to fully initialise (authenticator load)...")
        time.sleep(75)
        presto_status, _ = ssh_exec(CONFIG, "sudo docker ps --filter name=ibm-lh-presto --format '{{.Names}} {{.Status}}'")
        print(f"  Presto: {presto_status.strip()}")
        print()

    print("Done.")
    print()
    print("Verify with:")
    print("  python3 setup/test_federation_live.py")
    print("  python3 setup/test_cross_catalog_join.py")


if __name__ == "__main__":
    main()
