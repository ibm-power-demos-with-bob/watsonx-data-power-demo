#!/usr/bin/env python3
"""Quick check — confirm OLIST compat views exist on IBM i."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reservation as r
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(r.IBMI_HOST, username=r.SSH_USER, key_filename=r.SSH_KEY, timeout=30)
print(f"Connected to {r.IBMI_HOST}")

# Use WRKOBJ to check views exist without embedded quotes in shell command
for view in ["V_CUSTOMERS", "V_ORDERS", "V_ORDERITEMS", "V_PRODUCTS"]:
    _, o, e = c.exec_command(f'system "CHKOBJ OBJ(OLIST/{view}) OBJTYPE(*FILE)"')
    out = o.read().decode().strip()
    err = e.read().decode().strip()
    if err and "CPF9801" in err:
        print(f"  MISSING: OLIST/{view}")
    elif err:
        print(f"  ERROR checking {view}: {err[:80]}")
    else:
        print(f"  OK: OLIST/{view} exists")

c.close()
