#!/usr/bin/env python3
"""Check which tables/views exist in olist schema on PostgreSQL."""
import paramiko

HOST = "pvm01-4r13fr3k.p604.pok-systems.techzone.ibm.com"
USER = "UHJ907M"
KEY  = r"C:\Users\029878866\Downloads\pvm-4r13fr3k-key.pem"

try:
    key = paramiko.Ed25519Key.from_private_key_file(KEY)
except Exception:
    key = paramiko.RSAKey.from_private_key_file(KEY)

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=USER, pkey=key)

_, out, _ = c.exec_command("PGPASSWORD=edbadmin psql -h localhost -U edbadmin -d olist -c \"\\dt olist.*\" 2>&1")
tables = out.read().decode().strip()
print("Tables:"); print(tables)

_, out, _ = c.exec_command("PGPASSWORD=edbadmin psql -h localhost -U edbadmin -d olist -c \"\\dv olist.*\" 2>&1")
views = out.read().decode().strip()
print("\nViews:"); print(views)

c.close()
