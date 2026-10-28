#!/usr/bin/env python3
"""Verify OLIST tables/views on IBM i via the SQL catalog.

CHKOBJ gives false 'MISSING' for objects whose SQL name is > 10 chars (V_CUSTOMERS, V_ORDERITEMS),
because IBM i stores them under a generated 10-char system name. Query QSYS2.SYSTABLES instead.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paramiko
from reservation import IBMI_HOST, SSH_USER, SSH_KEY

k = paramiko.RSAKey.from_private_key_file(SSH_KEY)
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(IBMI_HOST, username=SSH_USER, pkey=k)

def db2(sql):
    sql = sql.replace("'", "''")   # double single quotes: SQL sits inside QSH CMD('...')
    _, so, se = c.exec_command(f"""system "QSH CMD('db2 \\"{sql}\\"')" """)
    so.channel.recv_exit_status()
    return (so.read().decode("latin-1", "replace") + se.read().decode("latin-1", "replace")).strip()

print(db2("SELECT TABLE_NAME, TABLE_TYPE, SYSTEM_TABLE_NAME FROM QSYS2.SYSTABLES WHERE TABLE_SCHEMA = 'OLIST' ORDER BY 1"))
for v, col in [("CUSTOMERS", "CUSTID"), ("ORDERS", "ORDERID"), ("ORDERITEMS", "ORDERID"), ("PRODUCTS", "PRODID")]:
    print(v, db2(f"SELECT COUNT({col}) FROM OLIST.{v}").splitlines()[2:3])
c.close()
