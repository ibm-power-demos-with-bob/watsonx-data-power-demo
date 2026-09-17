#!/usr/bin/env python3
"""
setup/8-load-edb-olist.py
=========================
Repeatable Olist → EDB Postgres data loader (supplier/operational layer).

Loads four tables into the `olist` schema on EDB Postgres:
  - olist.tier2_suppliers — fully synthetic fictional logistics sub-contractors
                            (the "victim" in the cyber incident demo scenario)
  - olist.suppliers       — from olist_sellers_dataset.csv, each FK'd to a tier2
  - olist.warehouses      — synthetic, one per distinct seller state
  - olist.purchase_orders — synthetic POs linking ORDER_ITEMS → suppliers

Localisation
------------
  --currency-code  Default currency code written to all rows (default: GBP)
  --country-code   Default ISO-3166-1 alpha-2 country code (default: GB)
  --region-map     Optional JSON file mapping Olist state codes to human-readable
                   region labels (e.g. {"SP": "South East England", ...}).
                   If omitted, region_label is left as the state code itself.
                   A ready-made GB map (fake, for demo) is generated automatically
                   when --region-map is not supplied and --country-code is GB.

English category names are joined from product_category_name_translation.csv
(already in data/olist/ from the Kaggle download) so query output is readable
without knowing Portuguese.

Prerequisites
-------------
  pip install kaggle pandas paramiko psycopg2-binary
  ~/.kaggle/kaggle.json  →  {"username":"…","key":"…"}

EDB Postgres is installed on the RHEL VM by this script (via SSH) when
--install-edb is passed.  If EDB is already installed, omit that flag.

Usage — first run (install EDB, create schema, load data)
----------------------------------------------------------
  python setup/8-load-edb-olist.py \\
    --host pvm1-9cug2i0k.p1387.pok-systems.techzone.ibm.com \\
    --ssh-user ec2-user \\
    --ssh-key "C:/Users/029878866/Downloads/user_ssh_private_key (1).user" \\
    --db-user edbadmin --db-password <pwd> \\
    --install-edb --create-schema

Usage — re-run (schema exists, reload data only)
-------------------------------------------------
  python setup/8-load-edb-olist.py \\
    --host pvm1-9cug2i0k.p1387.pok-systems.techzone.ibm.com \\
    --ssh-user ec2-user \\
    --ssh-key "C:/Users/029878866/Downloads/user_ssh_private_key (1).user" \\
    --db-user edbadmin --db-password <pwd> \\
    --skip-download

Usage — UK audience (GBP, GB region labels auto-generated)
----------------------------------------------------------
  python setup/8-load-edb-olist.py ... --currency-code GBP --country-code GB

Usage — Eurozone audience
--------------------------
  python setup/8-load-edb-olist.py ... --currency-code EUR --country-code DE \\
    --region-map data/region-maps/de.json
"""

import argparse
import io
import json
import os
import shlex
import sys
import time
from pathlib import Path

import pandas as pd
import paramiko

# ---------------------------------------------------------------------------
# Kaggle dataset slug (CSVs already cached in data/olist/ from IBM i load)
# ---------------------------------------------------------------------------
KAGGLE_DATASET = "olistbr/brazilian-ecommerce"

# ---------------------------------------------------------------------------
# Built-in demo region map for GB — maps the 27 Brazilian state codes to
# plausible UK regions.  Used when --country-code GB and no --region-map given.
# Completely fictional mapping — just makes query output feel localised.
# ---------------------------------------------------------------------------
GB_REGION_MAP = {
    "SP": "South East England",
    "RJ": "Greater London",
    "MG": "West Midlands",
    "RS": "Yorkshire and the Humber",
    "PR": "North West England",
    "SC": "Scotland",
    "BA": "East of England",
    "GO": "East Midlands",
    "DF": "Wales",
    "ES": "South West England",
    "PE": "North East England",
    "CE": "Northern Ireland",
    "PA": "South Yorkshire",
    "MA": "Merseyside",
    "MT": "Lincolnshire",
    "MS": "Cambridgeshire",
    "PB": "Oxfordshire",
    "PI": "Buckinghamshire",
    "RN": "Hertfordshire",
    "AL": "Kent",
    "SE": "Surrey",
    "TO": "Hampshire",
    "RO": "Dorset",
    "AM": "Somerset",
    "AC": "Devon",
    "AP": "Cornwall",
    "RR": "Cumbria",
}

# Matching EU (DE) region map for reference
DE_REGION_MAP = {
    "SP": "Bayern", "RJ": "Berlin", "MG": "Nordrhein-Westfalen",
    "RS": "Hamburg", "PR": "Baden-Württemberg", "SC": "Sachsen",
    "BA": "Hessen", "GO": "Thüringen", "DF": "Brandenburg",
    "ES": "Niedersachsen", "PE": "Rheinland-Pfalz", "CE": "Schleswig-Holstein",
    "PA": "Sachsen-Anhalt", "MA": "Mecklenburg-Vorpommern", "MT": "Saarland",
    "MS": "Bremen",
}

BUILTIN_MAPS = {"GB": GB_REGION_MAP, "DE": DE_REGION_MAP}

# ---------------------------------------------------------------------------
# EDB installation helpers (run on RHEL via SSH)
# ---------------------------------------------------------------------------

EDB_INSTALL_SCRIPT = """\
#!/bin/bash
set -e

# ── EDB Advanced Server 18 on RHEL / ppc64le (Power10/11) ──────────────────
# Uses the official EDB RPM repository.
# Approach validated at:
#   https://community.ibm.com/community/user/blogs/kemparaju/2026/05/30/building-pgvector-on-ibm-power
# Works on RHEL 10 (no dnf module streams needed).
# EDB AS defaults: port 5444, service edb-as-18, OS user enterprisedb,
#   binary prefix /usr/edb/as18/bin/, data dir /var/lib/edb/as18/data/
# Falls back to community PostgreSQL 16 if EDB repo is unreachable.

EDB_VER=18
PGBIN="/usr/edb/as${EDB_VER}/bin"
PGDATA="/var/lib/edb/as${EDB_VER}/data"
EDB_SVC="edb-as-${EDB_VER}"
EDB_USER="enterprisedb"
RHEL_VER=$(rpm -E '%{rhel}' 2>/dev/null || echo 9)

# 1. Install EDB AS if not already present
if ! rpm -q "edb-as${EDB_VER}-server" &>/dev/null && [ ! -d "/usr/edb/as${EDB_VER}" ]; then
    # Try EDB public repo first
    curl -1sLf "https://downloads.enterprisedb.com/repos/edb/rpm/el/${RHEL_VER}/ppc64le/repodata/repomd.xml" \
        -o /dev/null 2>&1 && EDB_REPO=1 || EDB_REPO=0
    if [ "${EDB_REPO}" = "1" ]; then
        dnf install -y "https://downloads.enterprisedb.com/repos/edb/rpm/el/${RHEL_VER}/ppc64le/edb-repo-latest.noarch.rpm" 2>/dev/null || true
        dnf install -y "edb-as${EDB_VER}-server" "edb-as${EDB_VER}-server-contrib" 2>&1 || EDB_REPO=0
    fi
    if [ "${EDB_REPO}" = "0" ]; then
        # Fallback: PostgreSQL.org community PostgreSQL 16
        echo "EDB AS repo unavailable -- falling back to PostgreSQL 16"
        dnf install -y "https://download.postgresql.org/pub/repos/yum/reporpms/EL-${RHEL_VER}-ppc64le/pgdg-redhat-repo-latest.noarch.rpm" || true
        dnf module disable -y postgresql 2>/dev/null || true
        dnf install -y postgresql16 postgresql16-server postgresql16-contrib
        PGBIN="/usr/pgsql-16/bin"
        PGDATA="/var/lib/pgsql/16/data"
        EDB_SVC="postgresql-16"
        EDB_USER="postgres"
    fi
fi

# Re-detect layout (handles idempotent re-runs and fallback case)
if [ -d "/usr/edb/as${EDB_VER}/bin" ]; then
    PGBIN="/usr/edb/as${EDB_VER}/bin"
    PGDATA="/var/lib/edb/as${EDB_VER}/data"
    EDB_SVC="edb-as-${EDB_VER}"
    EDB_USER="enterprisedb"
elif [ -d "/usr/pgsql-16/bin" ]; then
    PGBIN="/usr/pgsql-16/bin"
    PGDATA="/var/lib/pgsql/16/data"
    EDB_SVC="postgresql-16"
    EDB_USER="postgres"
fi

# 2. Initialise cluster (idempotent)
if [ ! -f "${PGDATA}/PG_VERSION" ]; then
    SETUP_BIN="${PGBIN}/${EDB_SVC}-setup"
    if [ -x "${SETUP_BIN}" ]; then
        "${SETUP_BIN}" initdb
    else
        sudo -u "${EDB_USER}" "${PGBIN}/initdb" -D "${PGDATA}"
    fi
fi

# 3. Configure: listen on all interfaces + scram-sha-256 from anywhere
sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" "${PGDATA}/postgresql.conf"
grep -q "0.0.0.0/0" "${PGDATA}/pg_hba.conf" || \
    echo "host all all 0.0.0.0/0 scram-sha-256" >> "${PGDATA}/pg_hba.conf"

# 4. Enable + start
systemctl enable "${EDB_SVC}"
systemctl restart "${EDB_SVC}"
sleep 2

# 5. Detect actual listening port
PG_PORT=$(sudo -u "${EDB_USER}" "${PGBIN}/psql" -At -c "SHOW port;" 2>/dev/null | tr -d '[:space:]' || echo "5444")

# 6. Create edbadmin role + olist database
sudo -u "${EDB_USER}" "${PGBIN}/psql" -c "
    DO \\$\\$
    BEGIN
      IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'edbadmin') THEN
        CREATE ROLE edbadmin LOGIN PASSWORD 'edbadmin1' SUPERUSER;
      END IF;
    END
    \\$\\$;
"
sudo -u "${EDB_USER}" "${PGBIN}/psql" -tc \
    "SELECT 'CREATE DATABASE olist OWNER edbadmin' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'olist')" \
    | grep -q "CREATE DATABASE" && \
    sudo -u "${EDB_USER}" "${PGBIN}/psql" -c "CREATE DATABASE olist OWNER edbadmin;" || true

# 7. Open firewall port if firewalld is active
if systemctl is-active firewalld &>/dev/null; then
    firewall-cmd --permanent --add-port="${PG_PORT}/tcp"
    firewall-cmd --reload
fi

# Emit summary for the Python caller to parse
echo "EDB_PORT=${PG_PORT}"
echo "EDB_BIN=${PGBIN}"
echo "EDB_DATA=${PGDATA}"
echo "EDB_SVC=${EDB_SVC}"
echo "EDB_INSTALL_OK"
"""


# ---------------------------------------------------------------------------
# SSH helpers (same pattern as 6-load-ibmi-olist.py)
# ---------------------------------------------------------------------------

def ssh_connect(host, user, key_path):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, key_filename=str(key_path), timeout=30)
    print(f"  SSH connected to {host} as {user}")
    return client


def ssh_run(client, cmd, check=True, timeout=300):
    # Always run via bash -c so that shell features (redirects, pipes, &&) work
    _, stdout, stderr = client.exec_command(f"bash -c {shlex.quote(cmd)}", timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace").strip()
    err = stderr.read().decode("utf-8", errors="replace").strip()
    rc  = stdout.channel.recv_exit_status()
    if check and rc != 0:
        raise RuntimeError(f"Command failed (rc={rc}):\n  CMD: {cmd}\n  ERR: {err}\n  OUT: {out}")
    return out, err, rc


def sftp_put_text(client, content: str, remote_path: str):
    """Upload a string as a UTF-8 file via SFTP (no temp file on disk)."""
    sftp = client.open_sftp()
    with sftp.open(remote_path, "w") as f:
        f.write(content)
    sftp.close()


# ---------------------------------------------------------------------------
# EDB installation
# ---------------------------------------------------------------------------

def install_edb(client) -> dict:
    """Install EDB AS on the RHEL VM.  Returns a dict with port, bin, data, svc."""
    print("\n  Installing EDB Advanced Server on RHEL VM ...")
    sftp_put_text(client, EDB_INSTALL_SCRIPT, "/tmp/install_edb.sh")
    ssh_run(client, "chmod +x /tmp/install_edb.sh")
    out, err, rc = ssh_run(client, "sudo /tmp/install_edb.sh", check=False, timeout=600)
    if "EDB_INSTALL_OK" not in out:
        raise RuntimeError(f"EDB install did not complete cleanly:\n{out}\n{err}")
    # Parse summary vars emitted by the install script
    info = {}
    for line in out.splitlines():
        for key in ("EDB_PORT", "EDB_BIN", "EDB_DATA", "EDB_SVC"):
            if line.startswith(f"{key}="):
                info[key] = line.split("=", 1)[1].strip()
    port = info.get("EDB_PORT", "5444")
    svc  = info.get("EDB_SVC", "edb-as-18")
    print(f"  EDB installed and running.  port={port}  service={svc}")
    return info


# ---------------------------------------------------------------------------
# DDL execution via psql
# ---------------------------------------------------------------------------

def run_ddl(client, ddl_path: Path, db_host: str, db_user: str, db_password: str,
            db_name: str = "olist", port: str = "5444"):
    print("\n  Creating olist schema and tables ...")
    ddl_content = ddl_path.read_text(encoding="utf-8")
    sftp_put_text(client, ddl_content, "/tmp/edb_olist_ddl.sql")
    # Write a .pgpass file to avoid quoting special chars in the password
    pgpass_line = f"localhost:{port}:{db_name}:{db_user}:{db_password}"
    sftp_put_text(client, pgpass_line + "\n", "/tmp/.pgpass_edb")
    # Detect psql binary path
    cmd = (
        f"chmod 600 /tmp/.pgpass_edb && "
        f"PGPASSFILE=/tmp/.pgpass_edb "
        f"$(ls /usr/edb/as*/bin/psql /usr/pgsql-16/bin/psql 2>/dev/null | head -1) "
        f"-h {db_host} -p {port} -U {db_user} -d {db_name} "
        f"-f /tmp/edb_olist_ddl.sql"
    )
    ssh_run(client, cmd, timeout=60)
    print("  Schema creation complete.")


# ---------------------------------------------------------------------------
# Data transforms
# ---------------------------------------------------------------------------

def load_region_map(country_code: str, region_map_path: str | None) -> dict:
    if region_map_path:
        with open(region_map_path, encoding="utf-8") as f:
            return json.load(f)
    return BUILTIN_MAPS.get(country_code.upper(), {})


def load_translations(data_dir: Path) -> dict:
    path = data_dir / "product_category_name_translation.csv"
    if not path.exists():
        return {}
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    return dict(zip(df["product_category_name"], df["product_category_name_english"]))


# ---------------------------------------------------------------------------
# Tier-2 supplier generation
# 50 entirely fictional logistics/MFT sub-contractors.
# 3-4 are pre-seeded as COMPROMISED to represent the breach at demo time.
# Suppliers are assigned to tier-2 companies deterministically by state hash
# so the mapping is stable across re-runs.
# ---------------------------------------------------------------------------

# Fictional company roster — deliberately generic European logistics names.
# None of these are real companies.
TIER2_COMPANIES = [
    ("Nexaflow Logistics Ltd",        "Managed File Transfer", "South East England"),
    ("Crestline Freight Solutions",   "Road Freight",          "West Midlands"),
    ("Alderton Supply Chain Services","MFT & EDI",             "Greater London"),
    ("Veritas Cargo Networks",        "Freight Forwarding",    "Yorkshire and the Humber"),
    ("Holloway Distribution Group",   "Warehousing & MFT",     "North West England"),
    ("Severn Bridge Logistics",       "Road Freight",          "Wales"),
    ("Caledonian Freight Partners",   "Air & Road Freight",    "Scotland"),
    ("Castleton Supply Technologies",  "Managed File Transfer", "East of England"),
    ("Thornbury Logistics Services",  "EDI & MFT",             "East Midlands"),
    ("Avalon Transport Networks",     "Road Freight",          "South West England"),
    ("Castlepoint Cargo Ltd",         "Freight Forwarding",    "North East England"),
    ("Redwood Supply Chain",          "Warehousing & Road",    "South East England"),
    ("Pennine Freight Group",         "Road Freight",          "Yorkshire and the Humber"),
    ("Sterling Logistics Europe",     "MFT & Compliance",      "Greater London"),
    ("Bramblewood Distribution",      "Last-Mile Logistics",   "West Midlands"),
    ("Corsair Cargo Solutions",       "Air Freight & MFT",     "South East England"),
    ("Langford Supply Networks",      "Road Freight",          "East of England"),
    ("Blackwater Logistics",          "Managed File Transfer", "North West England"),
    ("Ironbridge Freight",            "Road & Rail",           "West Midlands"),
    ("Northgate Cargo Services",      "Warehousing & EDI",     "Scotland"),
    ("Vantage Supply Chain Ltd",      "MFT & Road Freight",    "Greater London"),
    ("Clearwater Distribution",       "Last-Mile Logistics",   "South West England"),
    ("Chiltern Freight Solutions",    "Road Freight",          "East Midlands"),
    ("Oakfield Logistics Group",      "Managed File Transfer", "East of England"),
    ("Westbrook Supply Partners",     "Freight Forwarding",    "Wales"),
    ("Hartley Transport Networks",    "Road Freight",          "North East England"),
    ("Sable Cargo Technologies",      "EDI & MFT",             "South East England"),
    ("Dunmore Logistics Ltd",         "Road & Sea Freight",    "Scotland"),
    ("Fenland Distribution Group",    "Warehousing & Road",    "East of England"),
    ("Greystone Supply Chain",        "Managed File Transfer", "Greater London"),
    ("Altus Freight Services",        "Air & Road Freight",    "North West England"),
    ("Cedarwood Cargo Networks",      "Last-Mile Logistics",   "West Midlands"),
    ("Marlowe Logistics Europe",      "Freight Forwarding",    "South East England"),
    ("Solway Distribution",           "Road Freight",          "Scotland"),
    ("Pennant Supply Technologies",   "MFT & Compliance",      "Wales"),
    ("Ashford Freight Group",         "Warehousing & MFT",     "South East England"),
    ("Kestrel Cargo Solutions",       "Air Freight",           "East Midlands"),
    ("Whitmore Transport Ltd",        "Road Freight",          "North West England"),
    ("Glencross Logistics",           "Road & Rail",           "Scotland"),
    ("Birchwood Supply Chain",        "Managed File Transfer", "Yorkshire and the Humber"),
    ("Trentside Freight Services",    "EDI & MFT",             "East Midlands"),
    ("Craven Distribution Partners",  "Last-Mile Logistics",   "North East England"),
    ("Foxglove Cargo Ltd",            "Freight Forwarding",    "South West England"),
    ("Moorfield Supply Networks",     "Road Freight",          "North West England"),
    ("Clifton Logistics Group",       "Warehousing & Road",    "Greater London"),
    ("Saltire Cargo Technologies",    "MFT & Compliance",      "Scotland"),
    ("Eastbury Distribution",         "Last-Mile Logistics",   "East of England"),
    ("Hayward Transport Networks",    "Road Freight",          "South East England"),
    ("Pennine Supply Solutions",      "Managed File Transfer", "Yorkshire and the Humber"),
    ("Wychwood Freight Partners",     "Freight Forwarding",    "West Midlands"),
]

# These 4 are pre-seeded as COMPROMISED — the breach victims in the demo.
# Nexaflow is the headline victim (MOVEit-style MFT breach).
# The others add realistic blast-radius (multiple MFT providers affected).
COMPROMISED_COMPANIES = {
    "Nexaflow Logistics Ltd",
    "Alderton Supply Chain Services",
    "Castleton Supply Technologies",
    "Greystone Supply Chain",
}
BREACH_TIMESTAMP = "2024-06-06 09:14:00"
CVE_REF          = "CVE-2023-34362"


def build_tier2_suppliers(country_code: str) -> pd.DataFrame:
    """Generate the 50 fictional tier-2 logistics sub-contractors."""
    rows = []
    for i, (name, service, region) in enumerate(TIER2_COMPANIES, start=1):
        is_compromised = name in COMPROMISED_COMPANIES
        rows.append({
            "company_name":    name,
            "company_code":    f"T2-{name.split()[0][:3].upper()}-{i:03d}",
            "service_type":    service,
            "region_label":    region,
            "country_code":    country_code,
            "breach_status":   "COMPROMISED" if is_compromised else "CLEAN",
            "breach_notified": BREACH_TIMESTAMP if is_compromised else None,
            "cve_reference":   CVE_REF if is_compromised else None,
        })
    return pd.DataFrame(rows)


def build_suppliers(data_dir: Path, region_map: dict,
                    currency_code: str, country_code: str,
                    tier2_id_map: dict) -> pd.DataFrame:
    """
    tier2_id_map: {tier2_id: company_name} — re-keyed after insert so we
    can assign each supplier a deterministic subcontracted_to_id by hashing
    their state to a tier-2 company index.
    """
    df = pd.read_csv(data_dir / "olist_sellers_dataset.csv",
                     dtype=str, keep_default_na=False)
    df.rename(columns={
        "seller_id":              "supplier_id",
        "seller_zip_code_prefix": "zip_code",
        "seller_city":            "city",
        "seller_state":           "state",
    }, inplace=True)
    df["city"]          = df["city"].str.strip().str.title().str[:80]
    df["zip_code"]      = df["zip_code"].str.strip().str[:10]
    df["region_label"]  = df["state"].map(lambda s: region_map.get(s, s))
    df["currency_code"] = currency_code
    df["country_code"]  = country_code

    # Assign each supplier to a tier-2 company deterministically.
    # Use hash(supplier_id) % len(tier2_ids) so the mapping is stable.
    tier2_ids = list(tier2_id_map.keys())
    n = len(tier2_ids)
    df["subcontracted_to_id"] = df["supplier_id"].map(
        lambda sid: tier2_ids[hash(sid) % n]
    )

    return df[["supplier_id", "zip_code", "city", "state",
               "region_label", "currency_code", "country_code",
               "subcontracted_to_id"]]


def build_warehouses(suppliers: pd.DataFrame, region_map: dict,
                     currency_code: str, country_code: str) -> pd.DataFrame:
    """One warehouse per distinct seller state — synthetic but realistic."""
    states = suppliers["state"].dropna().unique()
    rows = []
    for i, state in enumerate(sorted(states), start=1):
        region = region_map.get(state, state)
        # Deterministic warehouse city: use most common seller city in that state
        city_series = suppliers.loc[suppliers["state"] == state, "city"]
        city = city_series.mode().iloc[0] if not city_series.empty else region
        rows.append({
            "warehouse_code": f"WH-{state}-{i:03d}",
            "region_label":   region,
            "city":           city[:80],
            "state":          state,
            "capacity_sqm":   2000 + (i * 137) % 8000,   # pseudo-random but stable
            "currency_code":  currency_code,
            "country_code":   country_code,
        })
    return pd.DataFrame(rows)


def build_purchase_orders(data_dir: Path, suppliers: pd.DataFrame,
                          warehouses: pd.DataFrame, translations: dict,
                          currency_code: str) -> pd.DataFrame:
    """
    Synthetic POs: one PO row per row in olist_order_items_dataset.csv
    that has a known seller_id.  Links order_id + item_id → supplier.
    """
    items = pd.read_csv(data_dir / "olist_order_items_dataset.csv",
                        dtype=str, keep_default_na=False)
    products = pd.read_csv(data_dir / "olist_products_dataset.csv",
                           dtype=str, keep_default_na=False)

    # Only items with a valid seller
    known_sellers = set(suppliers["supplier_id"])
    items = items[items["seller_id"].isin(known_sellers)].copy()

    # Join product category for English label
    items = items.merge(
        products[["product_id", "product_category_name"]],
        on="product_id", how="left"
    )
    items["category_en"] = (
        items["product_category_name"]
        .map(lambda c: translations.get(c, c) if pd.notna(c) else "")
        .str[:80]
    )

    # Assign warehouse_id based on supplier's state
    supplier_state = suppliers.set_index("supplier_id")["state"].to_dict()
    state_wh = warehouses.reset_index().set_index("state")["index"].add(1).to_dict()

    def get_wh_id(seller_id):
        state = supplier_state.get(seller_id)
        return state_wh.get(state) if state else None

    items["warehouse_id"] = items["seller_id"].map(get_wh_id)

    # Generate stable PO numbers
    items = items.reset_index(drop=True)
    items["po_number"] = items.index.map(lambda i: f"PO-{2017 + (i // 50000):04d}-{(i % 50000) + 1:05d}")

    # Normalise numeric columns
    def to_num(s):
        try:
            return round(float(s), 2) if s else None
        except (ValueError, TypeError):
            return None

    def to_ts(s):
        s = str(s).strip()[:19] if s else None
        return s if s else None

    items["unit_price"]     = items["price"].map(to_num)
    items["freight_value"]  = items["freight_value"].map(to_num)
    items["ship_limit_date"]= items["shipping_limit_date"].map(to_ts)
    items["currency_code"]  = currency_code
    items["po_status"]      = "FULFILLED"

    return items[[
        "po_number", "order_id", "order_item_id",
        "seller_id", "warehouse_id", "category_en",
        "unit_price", "freight_value", "ship_limit_date",
        "po_status", "currency_code",
    ]].rename(columns={"seller_id": "supplier_id",
                        "order_item_id": "order_item_id"})


# ---------------------------------------------------------------------------
# Remote load via SSH + psql \COPY  (no local psycopg2 required)
# ---------------------------------------------------------------------------

def _pgbin(client: paramiko.SSHClient) -> str:
    """Detect the psql binary path on the remote host."""
    out, _, rc = ssh_run(
        client,
        "ls /usr/edb/as18/bin/psql /usr/pgsql-16/bin/psql 2>/dev/null | head -1",
        check=False
    )
    return out.strip() or "psql"


def _psql(client: paramiko.SSHClient, pgbin: str, db_name: str,
          db_user: str, db_password: str, port: str, sql: str) -> str:
    """Run a single SQL statement via psql over SSH, return stdout."""
    # Write password to a temp .pgpass so we never shell-quote it
    pgpass = f"localhost:{port}:{db_name}:{db_user}:{db_password}"
    sftp_put_text(client, pgpass + "\n", "/tmp/.pgpass_load")
    cmd = (
        f"chmod 600 /tmp/.pgpass_load && "
        f"PGPASSFILE=/tmp/.pgpass_load {pgbin} "
        f"-h localhost -p {port} -U {db_user} -d {db_name} "
        f"-At -c {shlex.quote(sql)}"
    )
    out, _, _ = ssh_run(client, cmd)
    return out.strip()


def upload_and_copy(client: paramiko.SSHClient, pgbin: str,
                    df: pd.DataFrame, table: str,
                    db_name: str, db_user: str, db_password: str,
                    port: str) -> None:
    """Upload df as CSV to /tmp, then feed it into psql via stdin redirection.

    Uses:  psql -c "COPY table (col1, col2, ...) FROM STDIN ..." < file.csv
    Columns are taken from df.columns so SERIAL PKs are never included.
    This avoids server-side file access (requires the postgres OS user) and
    avoids psql meta-command quoting issues with \\COPY.
    """
    remote_csv = f"/tmp/olist_load_{table.replace('.', '_')}.csv"
    buf = io.StringIO()
    df.to_csv(buf, index=False, header=False, na_rep=r"\N")
    sftp_put_text(client, buf.getvalue(), remote_csv)

    pgpass = f"localhost:{port}:{db_name}:{db_user}:{db_password}"
    sftp_put_text(client, pgpass + "\n", "/tmp/.pgpass_load")

    # Explicit column list so SERIAL PKs are skipped by the server
    col_list = ", ".join(df.columns)
    copy_sql = f"COPY {table} ({col_list}) FROM STDIN WITH (FORMAT csv, NULL '\\N')"
    cmd = (
        f"chmod 600 /tmp/.pgpass_load && "
        f"PGPASSFILE=/tmp/.pgpass_load {pgbin} "
        f"-h localhost -p {port} -U {db_user} -d {db_name} "
        f"-c {shlex.quote(copy_sql)} "
        f"< {remote_csv}"
    )
    ssh_run(client, cmd)
    ssh_run(client, f"rm -f {remote_csv}", check=False)


# ---------------------------------------------------------------------------
# Kaggle download
# ---------------------------------------------------------------------------

def download_olist(data_dir: Path):
    try:
        import kaggle
    except ImportError:
        print("ERROR: 'kaggle' package not installed. Run:  pip install kaggle")
        sys.exit(1)
    data_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n  Downloading Olist dataset to {data_dir} ...")
    try:
        kaggle.api.authenticate()
        kaggle.api.dataset_download_files(
            KAGGLE_DATASET, path=str(data_dir), unzip=True, quiet=False
        )
    except Exception as exc:
        print(f"ERROR: Kaggle download failed: {exc}")
        sys.exit(1)
    print("  Download complete.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    script_dir       = Path(__file__).parent
    default_data_dir = script_dir.parent / "data" / "olist"
    default_ddl      = script_dir / "7-edb-olist-ddl.sql"
    default_key      = Path.home() / ".ssh" / "id_rsa"

    parser = argparse.ArgumentParser(
        description="Load Olist supplier data into EDB Postgres on RHEL/Power10."
    )
    # SSH / host
    parser.add_argument("--host",       required=True,
                        help="RHEL VM hostname or IP (used for both SSH and psql)")
    parser.add_argument("--ssh-user",   default="ec2-user",
                        help="SSH user on the RHEL VM (default: ec2-user)")
    parser.add_argument("--ssh-key",    default=str(default_key),
                        help=f"Path to SSH private key (default: {default_key})")
    # DB
    parser.add_argument("--db-user",    default="edbadmin",
                        help="Postgres user (default: edbadmin)")
    parser.add_argument("--db-password",default="edbadmin1",
                        help="Postgres password (default: edbadmin1)")
    parser.add_argument("--db-name",    default="olist",
                        help="Postgres database name (default: olist)")
    parser.add_argument("--db-port",    default="5444",
                        help="Postgres port (default: 5444 for EDB AS; 5432 for community PG)")
    # Data
    parser.add_argument("--data-dir",   default=str(default_data_dir),
                        help="Local directory containing Olist CSVs")
    parser.add_argument("--ddl-file",   default=str(default_ddl),
                        help="Path to 7-edb-olist-ddl.sql")
    # Localisation
    parser.add_argument("--currency-code", default="GBP",
                        help="ISO 4217 currency code written to all rows (default: GBP)")
    parser.add_argument("--country-code",  default="GB",
                        help="ISO 3166-1 alpha-2 country code (default: GB)")
    parser.add_argument("--region-map",    default=None,
                        help="Optional JSON file: {state_code: region_label, ...}")
    # Flags
    parser.add_argument("--install-edb",   action="store_true",
                        help="Install EDB Postgres on the RHEL VM via SSH before loading")
    parser.add_argument("--create-schema", action="store_true",
                        help="Run DDL to create olist schema and tables before loading")
    parser.add_argument("--skip-download", action="store_true",
                        help="Skip Kaggle download; use CSVs already in --data-dir")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    ssh_key  = Path(args.ssh_key)

    # 1. Download CSVs if needed
    if not args.skip_download:
        download_olist(data_dir)

    # 2. Check required CSVs exist
    required = ["olist_sellers_dataset.csv", "olist_order_items_dataset.csv",
                "olist_products_dataset.csv"]
    missing = [f for f in required if not (data_dir / f).exists()]
    if missing:
        print(f"ERROR: Missing CSV files in {data_dir}: {missing}")
        print("Re-run without --skip-download, or place CSVs manually.")
        sys.exit(1)

    # 3. SSH connect — stays open for the entire operation
    client = ssh_connect(args.host, args.ssh_user, ssh_key)
    edb_info = {}

    try:
        # 4. Optionally install EDB
        if args.install_edb:
            edb_info = install_edb(client)

        # 5. Optionally create schema
        db_port = edb_info.get("EDB_PORT", args.db_port)
        if args.create_schema:
            run_ddl(client, Path(args.ddl_file),
                    "localhost", args.db_user, args.db_password, args.db_name,
                    port=db_port)

        # 6. Build dataframes locally (pure Python — no DB connection yet)
        print("\n  Building localised supplier data ...")
        region_map   = load_region_map(args.country_code, args.region_map)
        translations = load_translations(data_dir)

        tier2 = build_tier2_suppliers(args.country_code)
        print(f"  {len(tier2):,} tier-2 suppliers built "
              f"({sum(tier2['breach_status']=='COMPROMISED')} COMPROMISED).")

        # 7. Load via SSH + psql \COPY — no local psycopg2 required
        pgbin = _pgbin(client)
        print(f"\n  Loading data via SSH + psql on {args.host}:{db_port} ...")

        def psql(sql: str) -> str:
            return _psql(client, pgbin, args.db_name,
                         args.db_user, args.db_password, db_port, sql)

        def copy_table(df: pd.DataFrame, table: str) -> None:
            upload_and_copy(client, pgbin, df, table,
                            args.db_name, args.db_user, args.db_password, db_port)

        # Truncate in dependency order
        print("  Truncating tables ...")
        psql("TRUNCATE olist.purchase_orders, olist.warehouses, "
             "olist.suppliers, olist.tier2_suppliers CASCADE")

        # Load tier-2 first (suppliers FK → tier2)
        print(f"  Loading olist.tier2_suppliers ({len(tier2):,} rows) ...")
        copy_table(tier2[["company_name","company_code","service_type",
                           "region_label","country_code","breach_status",
                           "breach_notified","cve_reference"]],
                   "olist.tier2_suppliers")

        # Read back SERIAL tier2_ids over SSH so we can assign FKs in suppliers
        raw = psql("SELECT tier2_id, company_name FROM olist.tier2_suppliers")
        tier2_id_map = {}
        for line in raw.splitlines():
            parts = line.split("|", 1)
            if len(parts) == 2:
                tier2_id_map[int(parts[0].strip())] = parts[1].strip()

        # Build remaining dataframes now that tier2 IDs are known
        suppliers = build_suppliers(data_dir, region_map, args.currency_code,
                                    args.country_code, tier2_id_map)
        print(f"  {len(suppliers):,} suppliers built.")

        warehouses = build_warehouses(suppliers, region_map,
                                      args.currency_code, args.country_code)
        print(f"  {len(warehouses):,} warehouses built.")

        pos = build_purchase_orders(data_dir, suppliers, warehouses,
                                    translations, args.currency_code)
        print(f"  {len(pos):,} purchase orders built.")

        print(f"  Loading olist.suppliers ({len(suppliers):,} rows) ...")
        copy_table(suppliers, "olist.suppliers")

        print(f"  Loading olist.warehouses ({len(warehouses):,} rows) ...")
        copy_table(warehouses[["warehouse_code","region_label","city","state",
                                "capacity_sqm","currency_code","country_code"]],
                   "olist.warehouses")

        # Read back SERIAL warehouse_ids to patch PO foreign keys
        raw = psql("SELECT warehouse_id, state FROM olist.warehouses")
        wh_by_state = {}
        for line in raw.splitlines():
            parts = line.split("|", 1)
            if len(parts) == 2:
                wh_by_state[parts[1].strip()] = int(parts[0].strip())

        supplier_state = suppliers.set_index("supplier_id")["state"].to_dict()
        pos["warehouse_id"] = pos["supplier_id"].map(
            lambda sid: wh_by_state.get(supplier_state.get(sid))
        )

        print(f"  Loading olist.purchase_orders ({len(pos):,} rows) ...")
        copy_table(pos[["po_number","order_id","order_item_id","supplier_id",
                         "warehouse_id","category_en","unit_price","freight_value",
                         "ship_limit_date","po_status","currency_code"]],
                   "olist.purchase_orders")

        # Verify row counts
        for tbl in ("olist.tier2_suppliers", "olist.suppliers",
                    "olist.warehouses", "olist.purchase_orders"):
            count = psql(f"SELECT COUNT(*) FROM {tbl}")
            print(f"  OK {tbl}: {int(count):,} rows")

        # Show compromised companies — the demo punchline
        raw = psql(
            "SELECT company_name, service_type, region_label "
            "FROM olist.tier2_suppliers WHERE breach_status = 'COMPROMISED' "
            "ORDER BY company_name"
        )
        print("\n  COMPROMISED tier-2 suppliers (cyber demo victims):")
        for line in raw.splitlines():
            parts = [p.strip() for p in line.split("|")]
            if parts:
                print(f"     * {' | '.join(parts)}")

        print("\nDone. EDB Postgres olist tables loaded successfully.")
        print(f"  currency_code = {args.currency_code!r}  "
              f"country_code = {args.country_code!r}  port = {db_port}")

    except Exception as exc:
        print(f"\nERROR: {exc}")
        sys.exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    main()
