#!/usr/bin/env python3
"""
setup/6-load-ibmi-olist.py
==========================
Repeatable Olist → IBM i Db2 data loader.

Strategy
--------
1. Download Olist CSVs from Kaggle (skip if already present).
2. Transform each CSV locally into a clean pipe-delimited file that
   CPYFRMIMPF can consume without ambiguity (timestamps normalised,
   NULLs as empty fields, no header row).
3. SCP each transformed file to /tmp/ on the IBM i IFS.
4. Run CPYFRMIMPF via SSH `system` call to bulk-load into Db2 for i.
5. Optionally run the DDL first (--create-schema) using RUNSQLSTM.

This avoids JDBC/jaydebeapi entirely — no jt400.jar needed — and loads
100k rows in seconds rather than minutes.

Prerequisites
-------------
  pip install kaggle pandas paramiko
  ~/.kaggle/kaggle.json  →  {"username":"…","key":"…"}
    (Free Kaggle account: https://www.kaggle.com → Settings → API)

Usage — first time (creates schema + loads data)
-------------------------------------------------
  python setup/6-load-ibmi-olist.py \\
    --host 129.40.95.187 \\
    --user UD7XZDE \\
    --ssh-key "C:/Users/029878866/Downloads/user_ssh_private_key.user" \\
    --create-schema

Usage — re-run after fresh TechZone reservation (schema exists, reload data)
-----------------------------------------------------------------------------
  python setup/6-load-ibmi-olist.py \\
    --host 129.40.95.187 --user UD7XZDE \\
    --ssh-key "C:/Users/029878866/Downloads/user_ssh_private_key.user" \\
    --create-schema --skip-download

  # If CSVs already downloaded locally:
  python setup/6-load-ibmi-olist.py \\
    --host 129.40.95.187 --user UD7XZDE \\
    --ssh-key "C:/Users/029878866/Downloads/user_ssh_private_key.user" \\
    --create-schema --skip-download --data-dir ./data/olist
"""

import argparse
import os
import sys
from pathlib import Path

import pandas as pd
import paramiko

# ---------------------------------------------------------------------------
# Kaggle dataset slug
# ---------------------------------------------------------------------------
KAGGLE_DATASET = "olistbr/brazilian-ecommerce"

# IFS staging directory on the IBM i
IFS_TMP = "/tmp/olist"

# ---------------------------------------------------------------------------
# CSV → clean pipe-delimited transform functions
# Each returns a list of pipe-delimited lines (no header, no trailing pipe).
# Empty string = NULL for CPYFRMIMPF NULLIND(*FLDDFT).
# ---------------------------------------------------------------------------

def safe(val, maxlen=None):
    """Return empty string for NA, else stripped string (optionally truncated)."""
    if pd.isna(val):
        return ""
    s = str(val).strip().replace("|", " ")   # escape pipe — our delimiter
    if maxlen:
        s = s[:maxlen]
    return s


def safe_num(val):
    if pd.isna(val):
        return ""
    try:
        f = float(val)
        # Return integer string if it's a whole number
        return str(int(f)) if f == int(f) else str(round(f, 2))
    except (ValueError, TypeError):
        return ""


def parse_ts(val):
    """Normalise Olist timestamps to YYYY-MM-DD HH:MM:SS for CPYFRMIMPF."""
    if pd.isna(val):
        return ""
    s = str(val).strip()
    if not s:
        return ""
    # Olist format is already "2017-10-02 10:56:33" — pass through
    # Strip any trailing fractional seconds just in case
    return s[:19]


def transform_customers(data_dir: Path) -> list:
    df = pd.read_csv(data_dir / "olist_customers_dataset.csv",
                     dtype=str, keep_default_na=False)
    df = df.where(df != "", None)
    rows = []
    for r in df.itertuples(index=False):
        rows.append("|".join([
            safe(r.customer_id, 32),
            safe(r.customer_unique_id, 32),
            safe(r.customer_zip_code_prefix, 5),
            safe(r.customer_city, 60),
            safe(r.customer_state, 2),
        ]))
    return rows


def transform_products(data_dir: Path) -> list:
    df = pd.read_csv(data_dir / "olist_products_dataset.csv",
                     dtype=str, keep_default_na=False)
    df = df.where(df != "", None)

    translations: dict = {}
    trans_path = data_dir / "product_category_name_translation.csv"
    if trans_path.exists():
        tdf = pd.read_csv(trans_path, dtype=str, keep_default_na=False)
        translations = dict(zip(tdf["product_category_name"],
                                tdf["product_category_name_english"]))

    rows = []
    for r in df.itertuples(index=False):
        cat_pt = safe(r.product_category_name, 60)
        cat_en = safe(translations.get(r.product_category_name, ""), 60)
        rows.append("|".join([
            safe(r.product_id, 32),
            cat_pt,
            cat_en,
            safe_num(r.product_name_lenght),        # Olist CSV typo — intentional
            safe_num(r.product_description_lenght), # same
            safe_num(r.product_photos_qty),
            safe_num(r.product_weight_g),
            safe_num(r.product_length_cm),
            safe_num(r.product_height_cm),
            safe_num(r.product_width_cm),
        ]))
    return rows


def transform_orders(data_dir: Path) -> list:
    df = pd.read_csv(data_dir / "olist_orders_dataset.csv",
                     dtype=str, keep_default_na=False)
    df = df.where(df != "", None)
    rows = []
    for r in df.itertuples(index=False):
        rows.append("|".join([
            safe(r.order_id, 32),
            safe(r.customer_id, 32),
            safe(r.order_status, 20),
            parse_ts(r.order_purchase_timestamp),
            parse_ts(r.order_approved_at),
            parse_ts(r.order_delivered_carrier_date),
            parse_ts(r.order_delivered_customer_date),
            parse_ts(r.order_estimated_delivery_date),
        ]))
    return rows


def transform_order_items(data_dir: Path) -> list:
    df = pd.read_csv(data_dir / "olist_order_items_dataset.csv",
                     dtype=str, keep_default_na=False)
    df = df.where(df != "", None)
    rows = []
    for r in df.itertuples(index=False):
        rows.append("|".join([
            safe(r.order_id, 32),
            safe_num(r.order_item_id),
            safe(r.product_id, 32),
            safe(r.seller_id, 32),
            parse_ts(r.shipping_limit_date),
            safe_num(r.price),
            safe_num(r.freight_value),
        ]))
    return rows


# ---------------------------------------------------------------------------
# Table load spec
# Each entry: (transform_fn, ifs_filename, ibmi_table, col_count)
# col_count used by CPYFRMIMPF to verify field count per record
# ---------------------------------------------------------------------------
TABLES = [
    (transform_customers,   "customers.del",   "OLIST/CUSTOMERS",  5),
    (transform_products,    "products.del",    "OLIST/PRODUCTS",  10),
    (transform_orders,      "orders.del",      "OLIST/ORDERS",     8),
    (transform_order_items, "orderitems.del",  "OLIST/ORDERITEMS", 7),
]


# ---------------------------------------------------------------------------
# SSH helpers
# ---------------------------------------------------------------------------

def ssh_connect(host, user, key_path):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, key_filename=str(key_path))
    print(f"  SSH connected to {host} as {user}")
    return client


def ssh_run(client, cmd, check=True):
    """Run a command over SSH and return (stdout, stderr, exit_code)."""
    _, stdout, stderr = client.exec_command(cmd)
    # IBM i PASE may return Latin-1/EBCDIC-mapped bytes; decode with fallback
    raw_out = stdout.read()
    raw_err = stderr.read()
    try:
        out = raw_out.decode("utf-8").strip()
    except UnicodeDecodeError:
        out = raw_out.decode("latin-1").strip()
    try:
        err = raw_err.decode("utf-8").strip()
    except UnicodeDecodeError:
        err = raw_err.decode("latin-1").strip()
    rc  = stdout.channel.recv_exit_status()
    if check and rc != 0:
        raise RuntimeError(f"Command failed (rc={rc}):\n  CMD: {cmd}\n  ERR: {err}\n  OUT: {out}")
    return out, err, rc


def scp_put(client, local_path: Path, remote_path: str):
    """Upload a local file to the IBM i IFS via SFTP."""
    sftp = client.open_sftp()
    sftp.put(str(local_path), remote_path)
    sftp.close()


# ---------------------------------------------------------------------------
# Schema creation via RUNSQLSTM
# ---------------------------------------------------------------------------

def _write_utf8_nobom(path: Path, content: str):
    """Write text file with UTF-8, no BOM — required for IBM i IFS / RUNSQLSTM."""
    path.write_bytes(content.encode("utf-8"))


def run_ddl(client, ddl_path: Path, ifs_tmp: str, tmp_dir: Path):
    print("\n  Creating OLIST schema and tables ...")
    remote_ddl  = f"{ifs_tmp}/olist_ddl.sql"
    remote_drop = f"{ifs_tmp}/olist_drop.sql"
    remote_sh   = f"{ifs_tmp}/runddl.sh"

    # Strip BOM + Windows line endings before uploading
    ddl_content = ddl_path.read_bytes().decode("utf-8-sig").replace("\r\n", "\n")
    local_ddl = tmp_dir / "olist_ddl.sql"
    _write_utf8_nobom(local_ddl, ddl_content)

    # Separate DROP script — run first, errors silently ignored (schema may not exist)
    local_drop = tmp_dir / "olist_drop.sql"
    _write_utf8_nobom(local_drop, "DROP SCHEMA OLIST CASCADE;\n")

    # Shell script wrapper:
    # 1. Drop (ignore errors — schema may not exist on a fresh reservation)
    # 2. Short sleep — IBM i journal needs a moment after DROP SCHEMA CASCADE
    # 3. Create (all tables/indexes in one RUNSQLSTM call)
    sh_content = (
        "#!/bin/sh\n"
        # Drop (ignore errors — schema may not exist on a fresh reservation)
        f"system \"RUNSQLSTM SRCSTMF('{remote_drop}') COMMIT(*NONE) NAMING(*SQL) DFTRDBCOL(OLIST) ERRLVL(40)\"\n"
        "sleep 3\n"
        # Create all tables and indexes; DFTRDBCOL resolves FK references correctly
        f"system \"RUNSQLSTM SRCSTMF('{remote_ddl}') COMMIT(*NONE) NAMING(*SQL) DFTRDBCOL(OLIST) ERRLVL(20)\"\n"
        "echo RC=$?\n"
    )
    local_sh = tmp_dir / "runddl.sh"
    _write_utf8_nobom(local_sh, sh_content)

    sftp = client.open_sftp()
    try:
        sftp.mkdir(ifs_tmp)
    except OSError:
        pass  # already exists
    sftp.put(str(local_ddl),  remote_ddl)
    sftp.put(str(local_drop), remote_drop)
    sftp.put(str(local_sh),   remote_sh)
    sftp.close()

    ssh_run(client, f"chmod +x {remote_sh}")
    out, err, rc = ssh_run(client, remote_sh, check=False)
    if rc != 0:
        raise RuntimeError(f"RUNSQLSTM failed (rc={rc}):\n{out}\n{err}")
    print("  Schema creation complete.")


# ---------------------------------------------------------------------------
# Bulk load via CPYFRMIMPF
# ---------------------------------------------------------------------------

def load_table(client, local_rows: list, ifs_tmp: str, ifs_filename: str,
               ibmi_table: str, tmp_dir: Path):
    """Write rows locally, upload to IFS, run CPYFRMIMPF via shell script wrapper."""
    local_file  = tmp_dir / ifs_filename
    remote_file = f"{ifs_tmp}/{ifs_filename}"
    remote_sh   = f"{ifs_tmp}/load_{ifs_filename}.sh"
    local_sh    = tmp_dir / f"load_{ifs_filename}.sh"

    # Write pipe-delimited file — no BOM, Unix line endings
    _write_utf8_nobom(local_file, "\n".join(local_rows) + "\n")
    print(f"  Uploading {len(local_rows):,} rows to {remote_file} ...")
    scp_put(client, local_file, remote_file)

    # Shell script wrapper — avoids inline quoting issues in IBM i bsh
    # MBROPT(*REPLACE) clears + reloads — idempotent re-runs
    sh_content = (
        "#!/bin/sh\n"
        f"system \"CPYFRMIMPF FROMSTMF('{remote_file}') "
        f"TOFILE({ibmi_table}) "
        f"MBROPT(*REPLACE) "
        f"RCDDLM(*LF) "
        f"FLDDLM('|') "
        f"STRDLM(*NONE) "
        f"RMVBLANK(*BOTH) "
        f"DATFMT(*ISO) "
        f"TIMFMT(*ISO)\"\n"
        "echo RC=$?\n"
    )
    _write_utf8_nobom(local_sh, sh_content)
    scp_put(client, local_sh, remote_sh)
    ssh_run(client, f"chmod +x {remote_sh}")

    print(f"  Loading {ibmi_table} via CPYFRMIMPF ...")
    out, err, rc = ssh_run(client, remote_sh, check=False)
    if rc != 0:
        raise RuntimeError(
            f"CPYFRMIMPF failed for {ibmi_table} (rc={rc}):\n{out}\n{err}"
        )
    print(f"  OK: {ibmi_table} loaded.")


# ---------------------------------------------------------------------------
# Download helper
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
            KAGGLE_DATASET,
            path=str(data_dir),
            unzip=True,
            quiet=False,
        )
    except Exception as exc:
        print(f"ERROR: Kaggle download failed: {exc}")
        sys.exit(1)
    print("  Download complete.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    script_dir = Path(__file__).parent
    default_data_dir = script_dir.parent / "data" / "olist"
    default_ddl      = script_dir / "5-ibmi-olist-ddl.sql"
    default_key      = Path.home() / ".ssh" / "id_rsa"

    parser = argparse.ArgumentParser(
        description="Load Olist Brazilian E-Commerce data into IBM i Db2 via CPYFRMIMPF."
    )
    parser.add_argument("--host",        required=True, help="IBM i IP or hostname")
    parser.add_argument("--user",        required=True, help="IBM i OS user profile")
    parser.add_argument("--ssh-key",     default=str(default_key),
                        help=f"Path to SSH private key (default: {default_key})")
    parser.add_argument("--data-dir",    default=str(default_data_dir),
                        help="Local directory for Olist CSVs")
    parser.add_argument("--ddl-file",    default=str(default_ddl),
                        help="Path to 5-ibmi-olist-ddl.sql")
    parser.add_argument("--create-schema", action="store_true",
                        help="Run DDL to create OLIST schema and tables before loading")
    parser.add_argument("--skip-download", action="store_true",
                        help="Skip Kaggle download; use CSVs already in --data-dir")
    args = parser.parse_args()

    data_dir  = Path(args.data_dir)
    ssh_key   = Path(args.ssh_key)
    tmp_dir   = Path(script_dir.parent / "data" / "olist_transformed")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    # 1. Download CSVs (skip when only creating schema)
    if not args.skip_download:
        download_olist(data_dir)

    # 2. Connect
    client = ssh_connect(args.host, args.user, ssh_key)

    try:
        # Ensure IFS staging dir exists
        ssh_run(client, f"mkdir -p {IFS_TMP}", check=False)

        # 3. Optionally create schema
        if args.create_schema:
            run_ddl(client, Path(args.ddl_file), IFS_TMP, tmp_dir)

        # 4. Transform + load each table in FK-safe order
        #    (skipped automatically if no CSVs are present)
        required = [
            "olist_customers_dataset.csv",
            "olist_products_dataset.csv",
            "olist_orders_dataset.csv",
            "olist_order_items_dataset.csv",
        ]
        missing = [f for f in required if not (data_dir / f).exists()]
        if missing:
            print(f"\n  No CSV files found in {data_dir} — skipping data load.")
            print("  Re-run without --skip-download (or place CSVs manually) to load data.")
        else:
            for transform_fn, ifs_filename, ibmi_table, _ in TABLES:
                print(f"\n  Transforming {ibmi_table} ...")
                rows = transform_fn(data_dir)
                print(f"  {len(rows):,} rows transformed.")
                load_table(client, rows, IFS_TMP, ifs_filename, ibmi_table, tmp_dir)
            print("\nDone. All Olist tables loaded into IBM i successfully.")

    except Exception as exc:
        print(f"\nERROR: {exc}")
        sys.exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    main()
