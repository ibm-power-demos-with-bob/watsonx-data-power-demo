#!/usr/bin/env python3
"""Apply PostgreSQL compat views (11-pg-compat-views.sql) via SSH."""
import paramiko, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from reservation import RHEL_HOST as HOST, SSH_USER as USER, SSH_KEY as KEY
from pathlib import Path
SQL_FILE = Path("setup/11-pg-compat-views.sql")

try:
    key = paramiko.Ed25519Key.from_private_key_file(KEY)
except Exception:
    key = paramiko.RSAKey.from_private_key_file(KEY)

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=USER, pkey=key)

sql_content = SQL_FILE.read_text(encoding="utf-8")
sftp = c.open_sftp()
with sftp.file("/tmp/pg_compat_views.sql", "w") as f:
    f.write(sql_content)
sftp.close()
print("SQL uploaded.")

_, out, err = c.exec_command("PGPASSWORD=edbadmin psql -h localhost -U edbadmin -d olist -f /tmp/pg_compat_views.sql 2>&1")
out.channel.recv_exit_status()
result = out.read().decode("utf-8", errors="replace").strip()
print(result[:800])
c.close()
print("Done.")
