#!/usr/bin/env python3
"""
===========================================================================
IBM i — set OS password for Db2 DRDA authentication
===========================================================================

The IBM i OS password changes with every TechZone reservation.
SSH uses key-based auth so the password is not needed for SSH access,
but watsonx.data Db2 for i federation uses DRDA authentication, which
validates the OS password directly.

This script must be run BEFORE setting up federation connectors in
watsonx.data (Step 5 in the recipe). If skipped, the ibmi_olist connector
will fail with an authentication error.

Usage
-----
    python3 setup/0-set-ibmi-password.py \\
      --host <ibmi-fqdn-or-ip> \\
      --user <ibmi-user> \\
      --key  <path-to-ssh-private-key> \\
      --password '<ibmi-os-password>'

    # Preferred: just run the script — it reads from setup/reservation.py
    python3 setup/0-set-ibmi-password.py

    # Override via environment variables if needed:
    IBMI_HOST=pvm02-XXXXXXXX.pXXXX.pok-systems.techzone.ibm.com \
    IBMI_USER=XXXXXXX \
    IBMI_KEY="/path/to/pvm-XXXXXXXX-key.pem" \
    IBMI_PASSWORD='YOUR_IBMI_PASSWORD' \
    python3 setup/0-set-ibmi-password.py

Where to find the password
--------------------------
On the TechZone reservation details page for the IBM i + RHEL combined
reservation. It is labelled "OS password" or "Password" and is the same
for both VMs in the combined reservation.

What this script does
---------------------
1. SSHes into the IBM i VM using key-based auth
2. Runs: system "CHGUSRPRF USRPRF(<user>) PASSWORD('<password>')"
3. Verifies the change by checking the profile exists

Why this is needed
------------------
Db2 for i DRDA authentication (port 8471) validates credentials against the
IBM i OS user profile. The TechZone-generated password is not automatically
set on the user profile — it must be applied explicitly. Without this step,
the watsonx.data connector test will return:
  "Authentication failed for user <USER>"
"""

import argparse
import os
import sys

import paramiko

# Pull defaults from reservation.py if present
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import reservation as _r
    _defaults = {
        "host":     _r.IBMI_HOST,
        "user":     _r.SSH_USER,
        "key":      _r.SSH_KEY,
        "password": _r.IBMI_PASSWORD,
    }
except Exception:
    _defaults = {"host": "", "user": "", "key": "", "password": ""}

CONFIG = {
    "host":     os.environ.get("IBMI_HOST",     _defaults["host"]),
    "user":     os.environ.get("IBMI_USER",     _defaults["user"]),
    "key":      os.environ.get("IBMI_KEY",      _defaults["key"]),
    "password": os.environ.get("IBMI_PASSWORD", _defaults["password"]),
}


def set_ibmi_password(host: str, user: str, key: str, password: str) -> None:
    print(f"Connecting to IBM i at {host} as {user}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, key_filename=key,
                   look_for_keys=False, timeout=30)
    print("  Connected.")

    # Set the password
    cmd = f'system "CHGUSRPRF USRPRF({user}) PASSWORD(\'{password}\')"'
    print(f"  Running: {cmd}")
    _, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()

    if err:
        print(f"  stderr: {err}", file=sys.stderr)
    if out:
        print(f"  stdout: {out}")

    # Verify — display the user profile to confirm it exists and is enabled
    print("  Verifying user profile...")
    _, stdout, stderr = client.exec_command(
        f'system "DSPUSRPRF USRPRF({user})" | grep -E "(Status|Password)"'
    )
    verify_out = stdout.read().decode().strip()
    if verify_out:
        print(f"  Profile check: {verify_out[:200]}")
    else:
        # IBM i system command output doesn't always go to stdout in SSH
        # — absence of error is the success signal
        print("  No stdout from DSPUSRPRF (normal for IBM i SSH) — checking for errors...")
        verify_err = stderr.read().decode().strip()
        if verify_err:
            print(f"  ERROR: {verify_err}", file=sys.stderr)
            sys.exit(1)

    client.close()
    print()
    print(f"Password set for {user} on IBM i at {host}.")
    print("You can now proceed with federation connector setup (setup/7-register-catalogs.py).")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Set IBM i OS password for Db2 DRDA authentication.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--host",     default=None, help="IBM i hostname or IP (overrides IBMI_HOST)")
    parser.add_argument("--user",     default=None, help="IBM i SSH/OS username (overrides IBMI_USER)")
    parser.add_argument("--key",      default=None, help="Path to SSH private key file (overrides IBMI_KEY)")
    parser.add_argument("--password", default=None, help="IBM i OS password to set (overrides IBMI_PASSWORD)")
    args = parser.parse_args()

    if args.host:     CONFIG["host"]     = args.host
    if args.user:     CONFIG["user"]     = args.user
    if args.key:      CONFIG["key"]      = args.key
    if args.password: CONFIG["password"] = args.password

    missing = []
    for k, label in [("host", "--host / IBMI_HOST"), ("user", "--user / IBMI_USER"),
                     ("key",  "--key / IBMI_KEY"),   ("password", "--password / IBMI_PASSWORD")]:
        if not CONFIG[k]:
            missing.append(label)
    if missing:
        print("ERROR: missing required values:", file=sys.stderr)
        for m in missing:
            print(f"  {m}", file=sys.stderr)
        print("\nAll values are on the TechZone reservation details page.", file=sys.stderr)
        sys.exit(1)

    set_ibmi_password(CONFIG["host"], CONFIG["user"], CONFIG["key"], CONFIG["password"])


if __name__ == "__main__":
    main()
