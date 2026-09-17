---
name: deploy-watsonx-data-power
description: >
  Full deployment guide for the watsonx.data on IBM Power presales demo on a fresh set
  of TechZone environments. Covers watsonx.data SaaS provisioning, IBM i data load,
  PostgreSQL 16 install and load, federation connector configuration, and demo UI deploy.
  Supports both DB path variants: Path A (IBM i + PostgreSQL) and Path B (AIX + PostgreSQL only).
  Also covers demo reset, re-run, and known failure modes.
globs:
  - "setup/**"
  - "demo-ui/**"
  - "queries/**"
  - "event-generators/**"
  - "RECIPE.md"
  - "COLLECTION.md"
---

# deploy-watsonx-data-power — Deployment Skill

You are deploying the **watsonx.data on IBM Power** presales demo on fresh TechZone environments.
This skill tells you exactly what to run, in what order, with what parameters, and what to check
after each step.

---

## What You Need Before Starting

Confirm you have the following before running any commands:

| Item | Source | Notes |
|------|--------|-------|
| watsonx.data IBM Cloud API key | IBM Cloud → IAM → Service credentials | Must have Manager role on the instance |
| watsonx.data instance CRN | IBM Cloud resource details | Looks like `crn:v1:bluemix:...` |
| watsonx.data COS bucket name | From the TechZone reservation details | Used by Iceberg catalog |
| watsonx.data Presto engine ID | watsonx.data console → Infrastructure → Presto engine name | E.g. `presto-demo` |
| IBM i FQDN or IP | TechZone reservation details | Path A only |
| IBM i SSH private key path | Downloaded from TechZone reservation details (User Private SSH Key) | Path A only |
| IBM i `*SECOFR` user credentials | TechZone reservation details | Path A only |
| RHEL VM FQDN | TechZone reservation details | Both paths |
| RHEL VM SSH private key path | Downloaded from TechZone reservation details | Both paths |
| Local path to this repo | Workspace root | `c:\Users\...\watsonx-data-power-demo` or equiv |

**IBM VPN must be active** — all TechZone environments are intranet-only.

---

## DB Path Selection

Ask the user which path applies if not already stated:

- **Path A (IBM i + PostgreSQL):** Customer runs IBM i. IBM i = Source 1 (core ERP). PostgreSQL = Source 2 (operational DB). Use this path by default.
- **Path B (AIX + PostgreSQL):** Customer runs workloads on AIX rather than IBM i. No IBM i. PostgreSQL = both Source 1 and Source 2 (full Olist dataset in PostgreSQL). Skip all IBM i steps below.

---

## Step 0 — Confirm Connectivity

Before running any deployment steps, verify SSH access to each environment:

```bash
# Test RHEL VM
ssh -i <rhel-key> -o StrictHostKeyChecking=no <rhel-user>@<rhel-fqdn> 'hostname && uname -m'
# Expected: hostname output, then ppc64le

# Test IBM i (Path A only)
ssh -i <ibmi-key> -o StrictHostKeyChecking=no <ibmi-user>@<ibmi-fqdn> 'system "WRKACTJOB" | head -5'
# Expected: IBM i active job output (will look like IBM i system output, not Linux)
```

If SSH fails:
- Confirm IBM VPN is active
- Confirm the TechZone reservation is in **Ready** state (not Provisioning)
- Confirm you are using the **private** key from the reservation, not a personal key
- On IBM i, confirm the user has `*SECOFR` authority

---

## Step 1 — Provision watsonx.data SaaS

Run the provisioning script to configure Presto, Iceberg catalog, and COS connector:

```bash
cd setup/
python 4-provision-via-rest-api.py \
  --api-key "<IBM_CLOUD_API_KEY>" \
  --crn "<INSTANCE_CRN>" \
  --cos-bucket "<COS_BUCKET_NAME>" \
  --engine-id "<PRESTO_ENGINE_ID>"
```

**What this does:** Creates the Iceberg catalog (`iceberg_data`), registers the COS storage
connector, and verifies the Presto engine can see the catalog via `SHOW CATALOGS`.

**Verify:**
```bash
# Script prints: "✅ SHOW CATALOGS returned: iceberg_data2, system, ..."
# If it fails with 401: API key is wrong or has insufficient permissions
# If it fails with 409 (conflict): catalog already exists — safe to skip, or delete and re-run
```

---

## Step 2 — Load IBM i Data (Path A only, skip for Path B)

### 2a. Run IBM i DDL

```bash
python setup/6-load-ibmi-olist.py \
  --host <ibmi-fqdn> \
  --user <ibmi-user> \
  --key <path-to-ibmi-key> \
  --create-schema
```

This uploads and runs `setup/5-ibmi-olist-ddl.sql` via `RUNSQLSTM` on IBM i.
Creates: `OLIST.CUSTOMERS`, `OLIST.PRODUCTS`, `OLIST.ORDERS`, `OLIST.ORDERITEMS`.

**Verify:** Script prints table counts (0 rows — DDL only at this stage).

### 2b. Load data

```bash
python setup/6-load-ibmi-olist.py \
  --host <ibmi-fqdn> \
  --user <ibmi-user> \
  --key <path-to-ibmi-key> \
  --load-data \
  --data-dir data/olist/
```

Expected load counts: CUSTOMERS 99,441 · PRODUCTS 32,951 · ORDERS 99,441 · ORDERITEMS 112,650.

**If CPYFRMIMPF fails with a quoting error:** The loader wraps the IBM i `bsh` command in a
shell script wrapper — confirm the `--host` parameter matches the IBM i IP exactly as shown
in the TechZone reservation details.

### 2c. Add SECTOR column

```bash
ssh -i <ibmi-key> <ibmi-user>@<ibmi-fqdn> 'cat > /tmp/sector.sql' < setup/9-ibmi-add-sector.sql
ssh -i <ibmi-key> <ibmi-user>@<ibmi-fqdn> 'system "RUNSQLSTM SRCSTMF(\"/tmp/sector.sql\") COMMIT(*NONE)"'
```

**Verify:** `SELECT SECTOR, COUNT(*) FROM OLIST.PRODUCTS GROUP BY SECTOR` should return 9 rows.

---

## Step 3 — Install PostgreSQL on RHEL and Load Data

### 3a. Install PostgreSQL and create schema (both paths)

```bash
python setup/8-load-edb-olist.py \
  --host <rhel-fqdn> \
  --ssh-user <rhel-user> \
  --ssh-key <rhel-key> \
  --install-edb \
  --create-schema \
  --skip-download
```

This installs **PostgreSQL 16** via the PGDG repo (`download.postgresql.org` — no token required),
initialises the cluster on port **5432**, creates the `olist` database, and runs
`setup/7-edb-olist-ddl.sql` via SSH.

**Note on EDB AS:** The EDB Advanced Server repo at `downloads.enterprisedb.com` requires a
token and publishes no ppc64le packages — it returns 404. The script falls back automatically
to community PostgreSQL 16, which is functionally identical for watsonx.data federation.

Tables created:
- `olist.tier2_suppliers` — 50 fictional tier-2 sub-contractors (4 pre-seeded COMPROMISED)
- `olist.suppliers` — tier-1 suppliers, each FK'd to a tier2_suppliers row
- `olist.warehouses` — regional distribution nodes
- `olist.purchase_orders` — POs with value, currency, region
- `olist.v_po_detail` — view joining all four tables

### 3b. Load data (both paths)

```bash
python setup/8-load-edb-olist.py \
  --host <rhel-fqdn> \
  --ssh-user <rhel-user> \
  --ssh-key <rhel-key> \
  --skip-download \
  --db-port 5432 \
  --currency-code GBP \
  --country-code GB
```

All data is loaded entirely over SSH via `psql COPY FROM STDIN` — **no local psycopg2 or pip
installs required**. At the end the script prints the 4 COMPROMISED tier-2 companies:
`Nexaflow Logistics Ltd, Alderton Supply Chain Services, Castleton Supply Technologies, Greystone Supply Chain`.

**For Path B (AIX+PostgreSQL) — extend load to include full Olist dataset:**

Add the `--full-dataset` flag to also load CUSTOMERS, PRODUCTS, ORDERS, ORDERITEMS into PostgreSQL
(in addition to the supplier tables above). This flag is Path B only.

```bash
python setup/8-load-edb-olist.py \
  --host <rhel-fqdn> --ssh-user <rhel-user> --ssh-key <rhel-key> \
  --skip-download --full-dataset \
  --db-port 5432 --currency-code GBP --country-code GB
```

---

## Step 4 — Configure watsonx.data Federation Connectors

Follow `setup/2-configure-federation.md` step by step. The key connectors to configure:

| Connector | Type | Source | Database / Schema |
|-----------|------|--------|------------------|
| `ibmi_olist` | Db2 for i | IBM i FQDN, port 8471 | `OLIST` (Path A only) |
| `pg_olist` | PostgreSQL | RHEL FQDN, port 5432, user `edbadmin`, db `olist` | `olist` |
| `iceberg_data2` | Iceberg | Already configured via Step 1 | `iceberg_data2` |

For **Path B**, skip the `ibmi_olist` connector. The `pg_olist` connector must point to the
extended schema that includes CUSTOMERS, PRODUCTS, ORDERS, ORDERITEMS as well as suppliers.

**Verify connectors:**
In the watsonx.data Query workspace, run:
```sql
SHOW SCHEMAS IN ibmi_olist;            -- should show: OLIST  (Path A)
SHOW SCHEMAS IN pg_olist;              -- should show: olist
SELECT COUNT(*) FROM pg_olist.olist.tier2_suppliers;  -- should show: 50
SHOW CATALOGS;                         -- should include: iceberg_data2
```

---

## Step 5 — Wire POS Event Generator to Iceberg

```bash
# On the RHEL VM
scp -i <rhel-key> event-generators/retail-pos-events.py <rhel-user>@<rhel-fqdn>:~/
ssh -i <rhel-key> <rhel-user>@<rhel-fqdn> \
  'nohup python3 ~/retail-pos-events.py \
     --cos-bucket <COS_BUCKET_NAME> \
     --api-key <IBM_CLOUD_API_KEY> \
     > ~/pos-events.log 2>&1 & echo started'
```

**Verify:** Check `~/pos-events.log` on the RHEL VM after 30 seconds — should show rows being written.

---

## Step 6 — Deploy the Demo UI

### 6a. Sync files to RHEL VM

```bash
# From workspace root (Windows: use scp -r or rsync via WSL)
scp -r -i <rhel-key> demo-ui/ <rhel-user>@<rhel-fqdn>:~/watsonx-data-power-demo/demo-ui/
```

### 6b. Install dependencies and build

```bash
ssh -i <rhel-key> <rhel-user>@<rhel-fqdn> \
  "cd ~/watsonx-data-power-demo/demo-ui && npm install --legacy-peer-deps && npm run build 2>&1 | tail -8"
```

**Expected:** Build completes with `✓ Compiled` and route listing. If it fails:
- `Cannot find module '@carbon/react'` → run `npm install --legacy-peer-deps` again
- `SWC binary missing` → confirm Next.js is 13.4.9 (`cat package.json | grep '"next"'`)
- TypeScript errors → check for stray `.tsx` files in `src/pages/api/` (should only be `.ts` files there)

### 6c. Start the UI

```bash
ssh -i <rhel-key> <rhel-user>@<rhel-fqdn> \
  '~/watsonx-data-power-demo/demo-ui/restart.sh'
# Note: this command will show CANCELED in Bob UI — that is expected (nohup detaches)
```

### 6d. Verify

```bash
ssh -i <rhel-key> <rhel-user>@<rhel-fqdn> \
  'sleep 5 && curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/'
# Must return: 200
```

**The CANCELED status on the restart step is a known cosmetic issue.** The only reliable
confirmation is step 6d returning `200`. Do not skip the verification step.

---

## Step 7 — Smoke Test End-to-End

1. Open `http://<rhel-fqdn>:3000` in a browser (IBM VPN active)
2. Confirm the static report page (`/`) loads with product metrics
3. Navigate to `/sources` — confirm three source cards are visible
4. Navigate to `/live?scenario=cyber` — confirm the POS stream is scrolling
5. Click **"Inject Cyber Signal"** — confirm an alert card appears within 3 seconds
6. Navigate to `/outcome?scenario=cyber` — confirm the timeline shows cyber outcome
7. Click **"Clear & reset"** on `/live?scenario=cyber`, then navigate to `/live?scenario=wildfire`
8. Click **"Inject Wildfire Signal"** — confirm a wildfire alert card appears
9. Navigate to `/outcome?scenario=wildfire` — confirm wildfire timeline

If alert cards do not appear:
- Check `~/demo-ui.log` on the RHEL VM for errors
- Confirm `/tmp/wxd-demo-signals.json` and `/tmp/wxd-demo-alerts.json` are writable (`chmod 666`)
- Confirm the EDB connection string in the UI env is correct (`EDBHOST`, `EDBPORT`, `EDBUSER`, `EDBPASS`)

---

## Resetting the Demo for Another Run

```bash
# Clear alert and signal stores on the RHEL VM
ssh -i <rhel-key> <rhel-user>@<rhel-fqdn> \
  'rm -f /tmp/wxd-demo-alerts.json /tmp/wxd-demo-signals.json && echo cleared'

# Or, just navigate to / on the UI — each /live page clears its alert store on mount
```

---

## SSH / Remote Command Patterns

These patterns were validated on RHEL 10.2 / ppc64le. Use them to avoid common pitfalls:

| Pattern | Command |
|---------|---------|
| Kill whatever is on port 3000 | `kill -9 $(ss -tlnp \| grep 3000 \| grep -oP "pid=\K[0-9]+") 2>/dev/null` |
| Non-blocking start (setsid pattern) | `PORT=3000 setsid npm start >> ~/demo-ui.log 2>&1 & echo started` |
| Verify port 3000 is up | `sleep 5 && curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/` |
| Single-quote outer SSH arg | Use single quotes to wrap the entire remote command when it contains double quotes |
| CANCELED on nohup steps | **Expected** — always follow with the curl verification step |

---

## Known Failure Modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `EADDRINUSE :3000` on restart | Previous Next.js process still running | Run the kill-port-3000 pattern above, then restart |
| Alert cards don't appear after inject | File store not writable or wrong path | `chmod 666 /tmp/wxd-demo-*.json`; check `~/demo-ui.log` |
| IBM i SSH fails with `Permission denied` | Wrong key or wrong user | Download key from TechZone reservation details; confirm user has `*SECOFR` |
| CPYFRMIMPF fails with `MSGID(CPF2817)` | Existing rows in target table | DDL uses DROP+CREATE; re-run `--create-schema` then `--load-data` |
| `pg_olist` connector fails in watsonx.data | Connector not yet wired | Follow `setup/2-configure-federation.md` step 2 |
| `SWC binary missing` on npm run build | Next.js > 13.x | Confirm `package.json` has `"next": "13.4.9"` |
| `Cannot find module 'live-feed-fetcher'` | Missing file on RHEL | Re-run the `scp -r demo-ui/` sync in Step 6a |
| CISA feed fetch fails | RHEL VM has no outbound internet | TechZone RHEL VMs should have outbound; check with `curl https://www.cisa.gov` |
| EDB AS repo returns 404 during `--install-edb` | No ppc64le packages; token required | Expected — script falls back to PostgreSQL 16 automatically |
| psycopg2 import error locally | Not needed | All DB ops use SSH + psql; no local psycopg2 required |
