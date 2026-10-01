#!/usr/bin/env python3
"""Insert catalog_engine rows and AMS policies for pg_olist and ibmi_olist, then restart Presto."""
import paramiko, time
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reservation as _r

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(_r.WXD_HOST, port=_r.WXD_SSH_PORT, username=_r.WXD_SSH_USER, password=_r.WXD_SSH_PASS)

def run(cmd, timeout=30):
    _, out, err = c.exec_command(cmd, timeout=timeout)
    out.channel.recv_exit_status()
    stdout = out.read().decode("utf-8", errors="replace").strip()
    stderr = err.read().decode("utf-8", errors="replace").strip()
    print((stdout + (" ERR:" + stderr[:300] if stderr else ""))[:800].encode("ascii","replace").decode("ascii"))

# 1. Show current catalog table to confirm both registrations are there
print("--- Current catalog table (pg/ibmi rows) ---")
run("sudo docker exec ibm-lh-postgres psql -U admin -d ibm_lh_repo -c \"SELECT catalog_name, database_id FROM catalog WHERE catalog_name IN ('pg_olist','ibmi_olist');\" 2>&1")

# 2. Insert catalog_engine rows for presto-01
print("\n--- Inserting catalog_engine rows ---")
run("""sudo docker exec ibm-lh-postgres psql -U admin -d ibm_lh_repo -c \
  "INSERT INTO catalog_engine (engine_id, engine_name, catalog_name, instance_id) VALUES ('presto-01','presto-01','pg_olist','0000-0000-0000-0000') ON CONFLICT DO NOTHING;" 2>&1""")
run("""sudo docker exec ibm-lh-postgres psql -U admin -d ibm_lh_repo -c \
  "INSERT INTO catalog_engine (engine_id, engine_name, catalog_name, instance_id) VALUES ('presto-01','presto-01','ibmi_olist','0000-0000-0000-0000') ON CONFLICT DO NOTHING;" 2>&1""")

# Verify
print("\n--- catalog_engine after insert ---")
run("sudo docker exec ibm-lh-postgres psql -U admin -d ibm_lh_repo -c 'SELECT * FROM catalog_engine;' 2>&1")

# 3. Add AMS policy rows granting ibmlhadmin access
print("\n--- Inserting AMS policy rows ---")
run("""sudo docker exec ibm-lh-postgres psql -U admin -d ibm_lh_repo -c \
  "INSERT INTO ams_0000_0000_0000_0000 (ptype,v0,v1,v2) VALUES ('g','Administrator','can_administer','catalogs/pg_olist') ON CONFLICT DO NOTHING;" 2>&1""")
run("""sudo docker exec ibm-lh-postgres psql -U admin -d ibm_lh_repo -c \
  "INSERT INTO ams_0000_0000_0000_0000 (ptype,v0,v1,v2) VALUES ('g','User','can_use','catalogs/pg_olist') ON CONFLICT DO NOTHING;" 2>&1""")
run("""sudo docker exec ibm-lh-postgres psql -U admin -d ibm_lh_repo -c \
  "INSERT INTO ams_0000_0000_0000_0000 (ptype,v0,v1,v2) VALUES ('g','Administrator','can_administer','catalogs/ibmi_olist') ON CONFLICT DO NOTHING;" 2>&1""")
run("""sudo docker exec ibm-lh-postgres psql -U admin -d ibm_lh_repo -c \
  "INSERT INTO ams_0000_0000_0000_0000 (ptype,v0,v1,v2) VALUES ('g','User','can_use','catalogs/ibmi_olist') ON CONFLICT DO NOTHING;" 2>&1""")

# 4. Restart Presto so it picks up the new catalog_engine entries
print("\n--- Restarting Presto ---")
run("sudo docker restart ibm-lh-presto", timeout=30)
print("Waiting 45s for Presto to initialise...")
time.sleep(45)
run("sudo docker ps --filter name=ibm-lh-presto --format '{{.Names}} {{.Status}}'")

c.close()
print("\nDone. Run test_federation_live.py to verify.")
