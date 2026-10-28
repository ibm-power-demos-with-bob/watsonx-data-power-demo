#!/usr/bin/env python3
"""
Upload pre-built .del files from data/olist_transformed/ directly to IBM i
and load them via CPYFRMIMPF. Used when CSVs are unavailable but .del files exist.
Assumes DDL (schema + tables) has already been created.

Fixes applied in memory before upload:
- Strips Windows CRLF -> LF (RCDDLM(*LF) requires LF only)
- Converts timestamps from SQL format (YYYY-MM-DD HH:MM:SS) to IBM i CPYFRMIMPF
  format (YYYY-MM-DD-HH.MM.SS) using a regex substitution across all fields.
  The pre-built .del files were committed with the old format; this corrects them.
- Cleans up /tmp/olist on IBM i before uploading to avoid IFS space errors.
"""
import io, os, re, sys
import paramiko

# Regex: match SQL timestamp pattern "YYYY-MM-DD HH:MM:SS" in pipe-delimited fields
# Replace the space+colons separator with hyphen+dots for IBM i CPYFRMIMPF
_TS_RE = re.compile(rb'(\d{4}-\d{2}-\d{2}) (\d{2}):(\d{2}):(\d{2})')

def fix_timestamps(data: bytes) -> bytes:
    """Convert YYYY-MM-DD HH:MM:SS -> YYYY-MM-DD-HH.MM.SS throughout a .del file."""
    return _TS_RE.sub(rb'\1-\2.\3.\4', data)

HOST = "pvm02-edaaiu5k.p1356.pok-systems.techzone.ibm.com"
USER = "UH6OWE8"
KEY  = r"C:\Users\029878866\Downloads\pvm-edaaiu5k-key.pem"
IFS  = "/tmp/olist"

TABLES = [
    ("customers.del",  "OLIST/CUSTOMERS"),
    ("products.del",   "OLIST/PRODUCTS"),
    ("orders.del",     "OLIST/ORDERS"),
    ("orderitems.del", "OLIST/ORDERITEMS"),
]

script_dir = os.path.dirname(os.path.abspath(__file__))
data_dir   = os.path.join(script_dir, "..", "data", "olist_transformed")

key = paramiko.RSAKey.from_private_key_file(KEY)
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=USER, pkey=key)
print(f"Connected to {HOST}")

def run(cmd, check=True):
    _, out, err = c.exec_command(cmd)
    rc  = out.channel.recv_exit_status()
    o   = out.read().decode("utf-8", "replace").strip()
    e   = err.read().decode("utf-8", "replace").strip()
    combined = (o + " " + e).strip()
    if check and rc != 0:
        raise RuntimeError(f"Command failed rc={rc}: {cmd}\n{combined}")
    return rc, o, e

# Clean up IFS staging dir to free space, then recreate
print("Cleaning up /tmp/olist on IBM i IFS ...")
run("rm -rf /tmp/olist", check=False)
run("mkdir -p /tmp/olist")
print("  Done.")

sftp = c.open_sftp()

for fname, table in TABLES:
    local  = os.path.join(data_dir, fname)
    remote = f"{IFS}/{fname}"

    if not os.path.exists(local):
        print(f"  SKIP {fname} -- not found at {local}")
        continue

    # Read file, strip CRLF, and fix timestamps in memory
    raw      = open(local, "rb").read()
    lf_data  = raw.replace(b"\r\n", b"\n")
    fixed    = fix_timestamps(lf_data)
    size_orig   = len(raw)
    crlf_count  = raw.count(b"\r\n")
    ts_count    = len(_TS_RE.findall(lf_data))

    print(f"\n  Uploading {fname} ({size_orig:,} bytes, {crlf_count:,} CRLF stripped, {ts_count:,} timestamps fixed) to {remote} ...")
    with sftp.open(remote, "wb") as f:
        f.write(fixed)
    print(f"  Uploaded {len(fixed):,} bytes (LF only, IBM i timestamp format).")

    remote_sh = f"{IFS}/load_{fname}.sh"
    sh_lines = [
        "#!/bin/sh",
        (
            f"system \"CPYFRMIMPF FROMSTMF('{remote}') "
            f"TOFILE({table}) "
            f"MBROPT(*REPLACE) RCDDLM(*LF) FLDDLM('|') "
            f"STRDLM(*NONE) RMVBLANK(*BOTH) DATFMT(*ISO) TIMFMT(*ISO)\""
        ),
        "echo RC=$?",
    ]
    with sftp.open(remote_sh, "w") as f:
        f.write("\n".join(sh_lines) + "\n")
    run(f"chmod +x {remote_sh}")

    print(f"  Loading {table} via CPYFRMIMPF ...")
    rc, o, e = run(remote_sh, check=False)
    out_combined = (o + " " + e).strip()
    print(f"  rc={rc}  {out_combined[:300]}")
    if "CPF2817" in out_combined or "CPF2845" in out_combined:
        print(f"  ERROR: CPYFRMIMPF reported an error for {table}")
        sftp.close()
        c.close()
        sys.exit(1)
    print(f"  OK: {table} loaded.")

sftp.close()
c.close()
print("\nAll tables loaded successfully.")
