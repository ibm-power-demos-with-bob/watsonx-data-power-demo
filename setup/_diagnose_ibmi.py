#!/usr/bin/env python3
"""
Fresh OLIST setup after DLTLIB/CRTLIB:
1. Upload patched DDL (no CREATE SCHEMA) and create all tables
2. Upload all .del files with timestamp fix and run CPYFRMIMPF
"""
import os, re, time
import paramiko

HOST = "pvm02-edaaiu5k.p1356.pok-systems.techzone.ibm.com"
USER = "UH6OWE8"
KEY  = r"C:\Users\029878866\Downloads\pvm-edaaiu5k-key.pem"
IFS  = "/tmp/olist"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TRANSFORMED = os.path.join(SCRIPT_DIR, "..", "data", "olist_transformed")

_TS_RE = re.compile(rb'(\d{4}-\d{2}-\d{2}) (\d{2}):(\d{2}):(\d{2})')

def fix_timestamps(data):
    return _TS_RE.sub(rb'\1-\2.\3.\4', data)

key = paramiko.RSAKey.from_private_key_file(KEY)
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=USER, pkey=key)
print(f"Connected to {HOST}")

def run(cmd, check=False):
    _, out, err = c.exec_command(cmd)
    rc = out.channel.recv_exit_status()
    o = (out.read().decode("utf-8","replace") + err.read().decode("utf-8","replace")).strip()
    if check and rc != 0:
        raise RuntimeError(f"FAILED rc={rc}: {o[:300]}")
    return rc, o

# ── Step 1: Upload patched DDL (CREATE SCHEMA stripped) ────────────────────
print("\n=== Step 1: Upload and run DDL ===")
run(f"rm -rf {IFS}")
run(f"mkdir -p {IFS}", check=True)

raw_ddl = open(os.path.join(TRANSFORMED, "olist_ddl.sql"), "rb").read().decode("utf-8-sig")
lines = [l for l in raw_ddl.splitlines() if not l.strip().upper().startswith("CREATE SCHEMA")]
patched = ("\n".join(lines) + "\n").encode("utf-8")

sftp = c.open_sftp()
with sftp.open(f"{IFS}/ddl.sql", "wb") as f:
    f.write(patched)
print("  DDL uploaded (CREATE SCHEMA removed)")

# ── Step 2: Run DDL ────────────────────────────────────────────────────────
rc, o = run(
    f"system \"RUNSQLSTM SRCSTMF('{IFS}/ddl.sql') "
    f"COMMIT(*NONE) NAMING(*SQL) DFTRDBCOL(OLIST) ERRLVL(20)\""
)
print(f"  RUNSQLSTM rc={rc}")
time.sleep(3)

# Verify tables
for tbl in ["CUSTOMERS", "PRODUCTS", "ORDERS", "ORDERITEMS"]:
    rc2, o2 = run(f"system \"CHKOBJ OBJ(OLIST/{tbl}) OBJTYPE(*FILE)\"")
    print(f"  {tbl}: {'OK' if rc2==0 else 'MISSING'} {o2[:60]}")

# ── Step 3: Upload and load all .del files ─────────────────────────────────
print("\n=== Step 2: Upload and load data ===")
TABLES = [
    ("customers.del",  "OLIST/CUSTOMERS"),
    ("products.del",   "OLIST/PRODUCTS"),
    ("orders.del",     "OLIST/ORDERS"),
    ("orderitems.del", "OLIST/ORDERITEMS"),
]

for fname, table in TABLES:
    local = os.path.join(TRANSFORMED, fname)
    remote = f"{IFS}/{fname}"

    raw = open(local, "rb").read()
    fixed = fix_timestamps(raw.replace(b"\r\n", b"\n"))
    ts_count = len(_TS_RE.findall(raw))
    print(f"\n  Uploading {fname} ({len(raw):,} bytes, {ts_count} timestamps fixed)...")
    with sftp.open(remote, "wb") as f:
        f.write(fixed)

    # Write load script
    remote_sh = f"{IFS}/load_{fname}.sh"
    sh = (
        "#!/bin/sh\n"
        f"system \"CPYFRMIMPF FROMSTMF('{remote}') "
        f"TOFILE({table}) "
        f"MBROPT(*REPLACE) RCDDLM(*LF) FLDDLM('|') "
        f"STRDLM(*NONE) RMVBLANK(*BOTH) DATFMT(*ISO) TIMFMT(*ISO)\"\n"
        "echo RC=$?\n"
    )
    with sftp.open(remote_sh, "w") as f:
        f.write(sh)
    run(f"chmod +x {remote_sh}")

    print(f"  Loading {table}...")
    rc, o = run(remote_sh, check=False)
    print(f"  rc={rc}  {o[:200]}")
    if "CPF2817" in o or "CPF2845" in o:
        print(f"  ERROR loading {table}")
        sftp.close(); c.close()
        import sys; sys.exit(1)
    print(f"  OK: {table} loaded.")

sftp.close()
c.close()
print("\nAll tables loaded successfully.")
