#!/usr/bin/env python3
"""
Load the Bond career table (bond_career_analysis) into Db2 for i (library OLIST).

Why: the Bond demo's primary "system of record" table is tailorable. For IBM i
audiences it lives on IBM i (catalog ibmi_olist); otherwise PostgreSQL
(setup/9-load-bond-data-pg.py) stands in for it (e.g. for Oracle on AIX).
The benchmark and review tables always stay in PostgreSQL, so with IBM i as
the primary source Acts 3 and 6 become genuine cross-source joins
(Db2 for i + PostgreSQL) through one watsonx.data Presto query.

Run AFTER the OLIST library exists (Phase 1 of the RUNBOOK).
Then set BOND_PRIMARY_SOURCE=ibmi in the UI .env.local (see _deploy_ui.py).

Usage: python setup/9b-load-bond-data-ibmi.py
"""
import json
import os
import sys
from pathlib import Path

import paramiko

sys.path.insert(0, os.path.dirname(__file__))
from reservation import IBMI_HOST as HOST, SSH_USER as USER, SSH_KEY as KEY

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA = REPO_ROOT / "demo-ui" / "src" / "data" / "bond" / "bond_actress_career_analysis.json"
IFS_SQL = "/tmp/bond_career_ibmi.sql"

rows = json.load(open(DATA, encoding="utf-8"))

# Column order, with Db2 for i types. Booleans are stored as SMALLINT 0/1.
COLS = [
    ("actress_name", "VARCHAR(100)"), ("character_name", "VARCHAR(100)"),
    ("film_title", "VARCHAR(100)"), ("release_year", "INTEGER"),
    ("bond_era", "VARCHAR(50)"), ("nconst", "VARCHAR(20)"),
    ("role_category", "VARCHAR(100)"), ("occupation", "VARCHAR(150)"),
    ("character_depth_score", "INTEGER"),
    ("has_independent_objective", "SMALLINT"), ("professional_expertise", "SMALLINT"),
    ("participates_in_climax", "SMALLINT"), ("intelligence_or_combat_role", "SMALLINT"),
    ("survives_film", "SMALLINT"),
    ("age_at_bond", "INTEGER"), ("age_group", "VARCHAR(50)"),
    ("prior_career_years", "INTEGER"), ("pre_bond_credits", "INTEGER"),
    ("pre_bond_avg_rating", "DECIMAL(4,2)"), ("pre_bond_avg_score", "DECIMAL(4,2)"),
    ("post_bond_credits_5y", "INTEGER"), ("post_bond_avg_rating_5y", "DECIMAL(4,2)"),
    ("post_bond_credits_lifetime", "INTEGER"), ("post_bond_avg_rating_lifetime", "DECIMAL(4,2)"),
    ("post_bond_avg_score_lifetime", "DECIMAL(4,2)"), ("post_bond_active_years", "INTEGER"),
    ("rating_delta_naive", "DECIMAL(4,2)"), ("career_trajectory", "VARCHAR(100)"),
    ("character_description", "VARCHAR(500)"),
]


def lit(v):
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, (int, float)):
        return str(v)
    return "'" + str(v).replace("'", "''") + "'"


stmts = ["DROP TABLE OLIST.BOND_CAREER_ANALYSIS;"]  # first run: error 'not found' is harmless
stmts.append(
    "CREATE TABLE OLIST.BOND_CAREER_ANALYSIS (\n  "
    + ",\n  ".join(f"{n.upper()} {t}" for n, t in COLS)
    + "\n);"
)
for r in rows:
    vals = ", ".join(lit(r[n]) for n, _ in COLS)
    stmts.append(f"INSERT INTO OLIST.BOND_CAREER_ANALYSIS VALUES ({vals});")
sql = "\n".join(stmts) + "\n"

try:
    key = paramiko.Ed25519Key.from_private_key_file(KEY)
except Exception:
    key = paramiko.RSAKey.from_private_key_file(KEY)
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=USER, pkey=key)
print(f"Connected to {HOST}")


def run(cmd):
    _, out, err = c.exec_command(cmd)
    rc = out.channel.recv_exit_status()
    o = (out.read().decode("utf-8", "replace") + err.read().decode("utf-8", "replace")).strip()
    return rc, o


sftp = c.open_sftp()
with sftp.file(IFS_SQL, "wb") as f:
    f.write(sql.encode("utf-8"))
sftp.close()
# Tag the file as UTF-8 so accented names (e.g. Lea Seydoux) load correctly
print("setccsid:", run(f"setccsid 1208 {IFS_SQL}"))

rc, o = run(
    f"system \"RUNSQLSTM SRCSTMF('{IFS_SQL}') COMMIT(*NONE) NAMING(*SQL) "
    f"DFTRDBCOL(OLIST) ERRLVL(30)\""
)
print(f"RUNSQLSTM rc={rc}\n{o[:600]}")

c.close()
print("Done. Verify via Presto: SELECT count(actress_name) FROM ibmi_olist.olist.bond_career_analysis")
