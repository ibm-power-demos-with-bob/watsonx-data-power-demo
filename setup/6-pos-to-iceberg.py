#!/usr/bin/env python3
"""
============================================================================
watsonx.data Demo — POS Event Writer to COS / Iceberg
============================================================================

Purpose
-------
Generates synthetic retail POS events and writes them as Parquet files into
IBM Cloud Object Storage (COS) under the Iceberg catalog path that watsonx.data
Presto can query as `iceberg_data2.retail.retail_pos_events`.

Also writes injected signal events (from signal-injector.py) into
`iceberg_data2.retail.retail_signals` so the cyber and wildfire federated
queries can join against them.

This script runs continuously on the RHEL VM alongside the demo UI.
It is the "live Iceberg source" — Source 3 in the three-source federation.

How Presto reads these files
----------------------------
watsonx.data Presto reads Parquet files written to COS as Iceberg tables when:
  1. The files are under the registered Iceberg catalog's COS base path
  2. The path layout is Hive-partitioned: <table>/dt=YYYY-MM-DD/<uuid>.parquet
  3. The schema (column names and types) matches what the CREATE TABLE declares

This script writes files in that layout. The Iceberg table DDL is in
setup/10-create-iceberg-tables.sql — run that once in the watsonx.data
Query workspace before starting this writer.

Usage
-----
    # Install dependencies (on RHEL VM)
    pip3 install pyarrow boto3

    # Run with current TechZone environment values (pre-filled in CONFIG):
    python3 setup/6-pos-to-iceberg.py

    # Override COS credentials via environment variables:
    COS_ACCESS_KEY=xxx COS_SECRET_KEY=yyy python3 setup/6-pos-to-iceberg.py

    # Write one batch only and exit (useful for smoke testing):
    python3 setup/6-pos-to-iceberg.py --once

    # Also watch for injected signals and write them to retail_signals:
    python3 setup/6-pos-to-iceberg.py --with-signals

    # Dry run — print what would be written without touching COS:
    python3 setup/6-pos-to-iceberg.py --dry-run

Signal integration
------------------
When --with-signals is set, this script polls /tmp/wxd-demo-signals.json
(written by signal-injector.py and the demo UI's inject-signal.ts) and
flushes any new signals as rows in the retail_signals Iceberg table.
This is what makes the federated queries actually work live.

COS path layout
---------------
    <bucket>/iceberg_data2/retail/retail_pos_events/dt=YYYY-MM-DD/<uuid>.parquet
    <bucket>/iceberg_data2/retail/retail_signals/dt=YYYY-MM-DD/<uuid>.parquet
"""

import argparse
import json
import os
import random
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# CONFIG — read from setup/config.env (gitignored) or environment variables.
# Copy setup/config.env.template -> setup/config.env and fill in before running.
# ---------------------------------------------------------------------------
import _config  # noqa: F401 — loads setup/config.env into os.environ (must be before CONFIG)
CONFIG = {
    "cos_access_key":  os.environ["COS_ACCESS_KEY"],
    "cos_secret_key":  os.environ["COS_SECRET_KEY"],
    "cos_endpoint":    os.environ.get("COS_ENDPOINT", "https://s3.direct.eu-gb.cloud-object-storage.appdomain.cloud"),
    "cos_bucket":      os.environ["COS_BUCKET"],
    "cos_region":      os.environ.get("COS_REGION",   "eu-gb"),
    # Base path inside the bucket — must match the Iceberg catalog's registered path
    "iceberg_base":    os.environ.get("ICEBERG_BASE",    "iceberg_data2/retail"),
    # How many POS events to generate per batch
    "batch_size":      int(os.environ.get("BATCH_SIZE",  "20")),
    # Seconds between batches
    "batch_interval":  int(os.environ.get("BATCH_INTERVAL", "30")),
    # Path where signal-injector.py / inject-signal.ts writes signals
    "signal_store":    os.environ.get("SIGNAL_STORE", "/tmp/wxd-demo-signals.json"),
}

# ---------------------------------------------------------------------------
# POS event generation — matches the schema in pos-stream.ts and event_schema.py
# ---------------------------------------------------------------------------
REGIONS = ["UK-London", "EMEA-North", "EMEA-South", "Americas-East", "APAC"]
STORES  = [f"STR-{r[:3].upper()}-{i:03d}" for r in REGIONS for i in range(1, 20)]
SKUS: list[tuple[str, float, str]] = [
    ("SKU-PRO-MAX-01",        899.00, "TECHNOLOGY"),
    ("SKU-ENERGY-BAR-12",       2.50, "FOOD_BEVERAGE"),
    ("SKU-WIRELESS-EAR-04",   129.99, "TECHNOLOGY"),
    ("SKU-ORGANIC-MILK-01",     1.85, "FOOD_BEVERAGE"),
    ("SKU-SMART-WATCH-09",    299.00, "TECHNOLOGY"),
    ("SKU-PREMIUM-COFFEE-02",   8.95, "FOOD_BEVERAGE"),
    ("SKU-RUNNING-SHOE-07",   159.99, "FASHION"),
    ("SKU-YOGA-MAT-03",        39.99, "CONSUMER_LEISURE"),
    ("SKU-DESK-LAMP-11",       49.99, "HOME_GOODS"),
    ("SKU-MOTOR-OIL-05",       18.50, "AUTOMOTIVE"),
]
PAYMENTS = ["Contactless", "Visa", "Mastercard", "ApplePay", "GooglePay"]


def generate_pos_events(n: int) -> list[dict]:
    events = []
    for _ in range(n):
        store = random.choice(STORES)
        sku, price, sector = random.choice(SKUS)
        qty = random.randint(1, 4)
        now = datetime.now(timezone.utc)
        events.append({
            "event_id":                    f"pos-{uuid.uuid4().hex[:10]}",
            "event_type":                  "pos_transaction",
            "timestamp":                   now.isoformat(),
            "epoch_ms":                    int(now.timestamp() * 1000),
            "transaction_id":              f"TXN-{random.randint(1000000, 9999999)}",
            "store_id":                    store,
            "region":                      next(r for r in REGIONS if store.startswith(f"STR-{r[:3].upper()}")),
            "sku_id":                      sku,
            "sector":                      sector,
            "quantity":                    qty,
            "unit_price":                  price,
            "total_amount":                round(qty * price, 2),
            "payment_method":              random.choice(PAYMENTS),
            "inventory_remaining_estimate": random.randint(5, 120),
        })
    return events


# ---------------------------------------------------------------------------
# Signal reader — reads /tmp/wxd-demo-signals.json written by the UI
# ---------------------------------------------------------------------------
_last_signal_count = 0


def read_new_signals() -> list[dict]:
    """Return any signals added to the signal store since last call."""
    global _last_signal_count
    path = Path(CONFIG["signal_store"])
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        signals = data if isinstance(data, list) else data.get("signals", [])
        new = signals[_last_signal_count:]
        _last_signal_count = len(signals)
        return new
    except (json.JSONDecodeError, OSError):
        return []


# ---------------------------------------------------------------------------
# Parquet writer — uses pyarrow; writes to COS via boto3 S3 client
# ---------------------------------------------------------------------------
def _cos_client():
    try:
        import boto3
        from botocore.client import Config
    except ImportError:
        print("ERROR: boto3 not installed. Run: pip3 install boto3", file=sys.stderr)
        sys.exit(1)
    return boto3.client(
        "s3",
        endpoint_url=CONFIG["cos_endpoint"],
        aws_access_key_id=CONFIG["cos_access_key"],
        aws_secret_access_key=CONFIG["cos_secret_key"],
        config=Config(signature_version="s3v4"),
        region_name=CONFIG["cos_region"],
    )


def write_parquet_to_cos(records: list[dict], table_name: str,
                         dry_run: bool = False) -> str:
    """Write records as a Parquet file to COS under the Hive partition path.

    Path: <iceberg_base>/<table_name>/dt=YYYY-MM-DD/<uuid>.parquet

    Returns the COS key written (or the key that would be written on dry run).
    """
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
        import io
    except ImportError:
        print("ERROR: pyarrow not installed. Run: pip3 install pyarrow", file=sys.stderr)
        sys.exit(1)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    key = f"{CONFIG['iceberg_base']}/{table_name}/dt={today}/{uuid.uuid4().hex}.parquet"

    if dry_run:
        print(f"  [DRY RUN] Would write {len(records)} rows -> s3://{CONFIG['cos_bucket']}/{key}")
        return key

    table = pa.Table.from_pylist(records)
    buf = io.BytesIO()
    pq.write_table(table, buf, compression="snappy")
    buf.seek(0)

    s3 = _cos_client()
    s3.put_object(
        Bucket=CONFIG["cos_bucket"],
        Key=key,
        Body=buf.read(),
        ContentType="application/octet-stream",
    )
    return key


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
def run(args: argparse.Namespace) -> None:
    print(">> [POS->Iceberg] Starting writer")
    print(f"   Bucket  : {CONFIG['cos_bucket']}")
    print(f"   Base    : {CONFIG['iceberg_base']}")
    print(f"   Batch   : {CONFIG['batch_size']} events every {CONFIG['batch_interval']}s")
    if args.dry_run:
        print("   Mode    : DRY RUN — nothing written to COS")
    if args.with_signals:
        print(f"   Signals : watching {CONFIG['signal_store']}")
    print()

    batch_num = 0
    try:
        while True:
            batch_num += 1
            now_str = datetime.now(timezone.utc).strftime("%H:%M:%S")

            # --- POS events ---
            events = generate_pos_events(CONFIG["batch_size"])
            key = write_parquet_to_cos(events, "retail_pos_events", dry_run=args.dry_run)
            print(f"[{now_str}] batch {batch_num}: wrote {len(events)} POS events -> .../{key.split('/')[-2]}/{key.split('/')[-1]}")

            # --- Signal events (if --with-signals) ---
            if args.with_signals:
                new_signals = read_new_signals()
                if new_signals:
                    # Normalise signal dict to match retail_signals schema
                    signal_rows = []
                    for s in new_signals:
                        signal_rows.append({
                            "event_id":        s.get("event_id", f"sig-{uuid.uuid4().hex[:8]}"),
                            "event_type":      s.get("event_type", "external_signal"),
                            "timestamp":       s.get("timestamp", datetime.now(timezone.utc).isoformat()),
                            "epoch_ms":        int(s.get("epoch_ms", time.time() * 1000)),
                            "signal_category": s.get("signal_category", "UNKNOWN"),
                            "signal_code":     s.get("signal_code", "UNKNOWN"),
                            "affected_sector": s.get("affected_sector", "LOGISTICS"),
                            "severity":        s.get("severity", "HIGH"),
                            "headline":        s.get("headline", ""),
                            "detail_url":      s.get("detail_url", ""),
                            "temp_celsius":    s.get("temp_celsius"),
                            "ticker_symbol":   s.get("ticker_symbol"),
                            "price_change_pct":s.get("price_change_pct"),
                            "injected":        bool(s.get("injected", True)),
                            "source_feed":     s.get("source_feed", ""),
                            "source_channel":  s.get("source_channel", ""),
                        })
                    sig_key = write_parquet_to_cos(signal_rows, "retail_signals", dry_run=args.dry_run)
                    print(f"[{now_str}]   + {len(signal_rows)} signal(s) -> .../{sig_key.split('/')[-1]}")

            if args.once:
                print("\n>> [POS->Iceberg] --once flag set - exiting after first batch.")
                break

            time.sleep(CONFIG["batch_interval"])

    except KeyboardInterrupt:
        print(f"\n>> [POS->Iceberg] Stopped after {batch_num} batch(es).")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Write synthetic POS events to COS as Parquet (Iceberg Source 3)."
    )
    parser.add_argument("--once",         action="store_true",
                        help="Write one batch then exit (smoke test).")
    parser.add_argument("--dry-run",      action="store_true",
                        help="Print what would be written without touching COS.")
    parser.add_argument("--with-signals", action="store_true",
                        help="Also flush injected signals from signal store to retail_signals table.")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
