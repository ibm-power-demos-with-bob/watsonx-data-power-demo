import paramiko

key_file = r"C:\Users\029878866\Downloads\user_ssh_private_key (9).user"
try:
    k = paramiko.RSAKey.from_private_key_file(key_file)
except Exception:
    k = paramiko.Ed25519Key.from_private_key_file(key_file)

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("129.40.252.55", username="UVU2BTL", pkey=k)

sh_content = """#!/bin/sh
system "RUNSQLSTM SRCSTMF('/tmp/9-ibmi-add-sector.sql') COMMIT(*NONE) NAMING(*SQL) DFTRDBCOL(OLIST) ERRLVL(30)"
system "RUNSQLSTM SRCSTMF('/tmp/10-ibmi-compat-views.sql') COMMIT(*NONE) NAMING(*SQL) DFTRDBCOL(OLIST) ERRLVL(30)"
echo "COMPLETED_OK"
"""

sftp = c.open_sftp()
with sftp.file("/tmp/apply_views.sh", "w") as f:
    f.write(sh_content)
sftp.close()

stdin, stdout, stderr = c.exec_command("chmod +x /tmp/apply_views.sh && /tmp/apply_views.sh")
out = stdout.read().decode("latin-1", errors="replace")
err = stderr.read().decode("latin-1", errors="replace")
print("STDOUT:\n", out.encode("ascii", "replace").decode("ascii"))
print("STDERR:\n", err.encode("ascii", "replace").decode("ascii"))
c.close()
