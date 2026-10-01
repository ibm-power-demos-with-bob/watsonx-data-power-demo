#!/usr/bin/env python3
"""Apply 10-ibmi-compat-views.sql to IBM i via SCP + RUNSQLSTM."""
import paramiko, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from reservation import IBMI_HOST as HOST, SSH_USER as USER, SSH_KEY as KEY
from pathlib import Path
SQL_FILE = Path("setup/10-ibmi-compat-views.sql")

try:
    key = paramiko.Ed25519Key.from_private_key_file(KEY)
except Exception:
    key = paramiko.RSAKey.from_private_key_file(KEY)

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=USER, pkey=key)
print(f"Connected to {HOST}")

sql_content = SQL_FILE.read_text(encoding="utf-8")
sftp = c.open_sftp()
with sftp.file("/tmp/compat_views.sql", "w") as f:
    f.write(sql_content)
sftp.close()
print("SQL file uploaded to /tmp/compat_views.sql")

cmd = "system \"RUNSQLSTM SRCSTMF('/tmp/compat_views.sql') COMMIT(*NONE) NAMING(*SQL) DFTRDBCOL(OLIST) ERRLVL(30)\""
_, out, err = c.exec_command(cmd)
stdout = out.read().decode("latin-1", errors="replace")
stderr = err.read().decode("latin-1", errors="replace")
print("STDOUT:", stdout[:3000])
if stderr.strip():
    print("STDERR:", stderr[:500])
c.close()
