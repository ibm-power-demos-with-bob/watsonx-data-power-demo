---
name: deploy-watsonx-data-power
description: >
  Full deployment guide for the watsonx.data on IBM Power presales demo on a fresh set
  of TechZone environments. Covers watsonx.data SaaS provisioning, IBM i data load,
  PostgreSQL 16 install and load, federation connector configuration, and demo UI deploy.
  Supports both DB path variants: Path A (IBM i + PostgreSQL) and Path B (AIX + EDB/PostgreSQL).
  Also covers demo reset, re-run, and known failure modes.
version: 1.0.0
author: EMEA AI on IBM Power Squad
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
- **Path B (AIX + EDB):** Customer runs Oracle on AIX. No IBM i. PostgreSQL (EDB-positioned) = both Source 1 and Source 2 (full Olist dataset). The database is community PostgreSQL 16 running the EDB story — Oracle-compatible positioning without Oracle licensing. Skip all IBM i steps below.

> **On "EDB" in Path B:** EDB Postgres Advanced Server is the Oracle-compatible build of PostgreSQL.
> The watsonx.data JDBC connector treats it identically to community PostgreSQL. For demo deployment,
> community PostgreSQL 16 (PGDG repo) is used — the EDB Advanced Server repo at
> `downloads.enterprisedb.com` requires a token and publishes no ppc64le packages (404 confirmed).
> The demo story and audience positioning as "EDB replacing Oracle" is accurate regardless.

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

> **⚠️ CRITICAL — Accept the IBM Cloud invitation BEFORE opening the watsonx.data console**
> On a fresh TechZone reservation, an `itz-watsonx` account invitation arrives in the IBM Cloud
> notification bell (not by email). You **must** accept it via the bell in your normal IBM ID
> session at cloud.ibm.com **before** opening the watsonx.data console for the first time.
> If the console is opened first, MDS initialises under the wrong account identity and the instance
> is permanently broken — symptom: *"tls: failed to verify certificate: x509: certificate signed
> by unknown authority"* when the first-run wizard tries to complete. The only fix is to delete
> the reservation and provision a fresh one.
>
> **Correct sequence:**
> 1. TechZone reservation reaches **Ready**
> 2. Open **cloud.ibm.com** (IBM ID, normal browser) → click notification bell → accept invite
> 3. Only now open the watsonx.data console via `https://cloud.ibm.com/authorize/itzwatsonx` in incognito
> 4. Complete the first-run wizard (Presto C++ → Starter → skip Spark → accept discovered COS bucket → `iceberg_data` catalog name → Finish and go)
> 5. Once the main UI loads, MDS is initialised — run `setup/4-provision-via-rest-api.py`

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

**For Path B (AIX+EDB) — extend load to include full Olist dataset:**

Add the `--full-dataset` flag to also load CUSTOMERS, PRODUCTS, ORDERS, ORDERITEMS into PostgreSQL
(in addition to the supplier tables above). This flag is Path B only.

```bash
python setup/8-load-edb-olist.py \
  --host <rhel-fqdn> --ssh-user <rhel-user> --ssh-key <rhel-key> \
  --skip-download --full-dataset \
  --db-port 5432 --currency-code GBP --country-code GB
```

---

## Step 3b — Install IBM Cloud Satellite Connector agent on RHEL

This step bridges IBM Cloud (watsonx.data SaaS) → PowerVS private network so the Presto engine
can reach both the RHEL PostgreSQL and the IBM i Db2 endpoints via Satellite Link endpoints.

**Use Satellite Connector, not Satellite Location.** Connector is a lightweight Docker container
agent — no worker nodes, no infrastructure provisioning, ready in minutes. Location is a full
infrastructure deployment designed for running IBM Cloud services on-premises; it is overkill
here and requires permissions that may not be available in TechZone accounts.

**Confirmed working pattern (from Hybrid-by-Design Orchestrate demo):**
- Satellite Connector lives in the **same IBM Cloud account and same reservation** as the SaaS service
- Connector agent runs as a **Docker container on the RHEL VM** — outbound connections only
- IBM Cloud CLI (`ibmcloud`) used to create the Connector and Link endpoints
- IBM i does not run any agent — its `:8471` port is a destination reached via RHEL's
  private network access to IBM i (both on the same PowerVS private subnet)

**Prerequisites:**
- `ibmcloud` CLI installed locally with `satellite` plugin: `ibmcloud plugin install satellite`
- Logged in to the same IBM Cloud account as the watsonx.data SaaS instance
- Docker installed on the RHEL VM: `sudo dnf install -y docker && sudo systemctl enable --now docker`

```bash
# 1. Create the Satellite Connector (on your local machine, ibmcloud CLI)
ibmcloud sat connector create --name wxd-power-demo --region eu-gb

# 2. Retrieve the Connector ID
CONNECTOR_ID=$(ibmcloud sat connector ls --output json | python3 -c \
  "import sys,json; cs=json.load(sys.stdin); \
   print(next(c['id'] for c in cs if c['name']=='wxd-power-demo'))")
echo "Connector ID: $CONNECTOR_ID"

# 3. Generate the agent token for the RHEL VM
ibmcloud sat connector create-agent --connector-id $CONNECTOR_ID

# 4. Pull and run the Connector agent on the RHEL VM
#    Replace <AGENT_TOKEN> with the token generated in step 3
ssh -i <rhel-key> <rhel-user>@<rhel-fqdn> "sudo docker run -d \
  --name satellite-connector-agent \
  --restart always \
  -e SATELLITE_CONNECTOR_ID=$CONNECTOR_ID \
  -e SATELLITE_CONNECTOR_AGENT_TOKEN=<AGENT_TOKEN> \
  icr.io/ibm/satellite-connector/satellite-connector-agent:latest"
```

**Verify agent is registered:**
In IBM Cloud console → Satellite → Connectors → `wxd-power-demo` → Agents:
the RHEL VM should appear with status **Connected** (takes 1–3 minutes).

```bash
# Or via CLI:
ibmcloud sat connector get --connector-id $CONNECTOR_ID
```

**Create Link endpoints** — automated script:

Run the included automated endpoint setup script. `--ibmi-ip` is the on-prem IP of the IBM i
VM from the TechZone reservation details:

```bash
python setup/satellite-endpoints.py \
  --api-key "<IBM_CLOUD_API_KEY>" \
  --account-id "<ACCOUNT_ID>" \
  --connector-id "<CONNECTOR_ID>" \
  --ibmi-ip "<IBMI_IP_FROM_TECHZONE>"
```

This creates the two Link endpoints (if not already present) and prints a summary including the
cloud-side hostnames and ports assigned by Satellite.

---

## Step 4 — Configure watsonx.data Federation Connectors

The federation connector script requires the Satellite Link hostnames and ports from Step 3b.
**These change with every reservation** — never hardcode them.

> **Why does this need the IBM i OS password?**
> The SSH key is used only to SSH into the RHEL VM. The IBM i OS password is different — it is
> stored by watsonx.data and used by the Presto engine to open **JDBC connections to Db2 for i**
> (port 8471, DDM protocol) at query time. Db2 for i DDM authenticates with OS username/password;
> it has no concept of SSH keys. The password comes from the TechZone reservation details page
> (same credentials used when you SSH into the IBM i from the VPN).

### Option A — one-liner chain (recommended)

`satellite-endpoints.py --output-env` emits shell `export` lines; `eval $()` sets them in the
current shell. All status output goes to stderr so `eval` only sees the four exports:

```bash
# 1. Create/verify endpoints AND export the hostnames/ports into the current shell
eval $(python setup/satellite-endpoints.py \
  --api-key "<IBM_CLOUD_API_KEY>" \
  --account-id "<ACCOUNT_ID>" \
  --connector-id "<CONNECTOR_ID>" \
  --ibmi-ip "<IBMI_IP_FROM_TECHZONE>" \
  --output-env)

# 2. Run the federation connector script using those exported values
WXD_APIKEY="<STUDENT_API_KEY>" \
WXD_INSTANCE_CRN="<INSTANCE_CRN>" \
IBMI_HOST=$IBMI_SAT_HOST \
IBMI_PORT=$IBMI_SAT_PORT \
IBMI_USERNAME="<IBMI_OS_USER>" \
IBMI_PASSWORD="<IBMI_OS_PASSWORD>" \
PG_HOST=$PG_SAT_HOST \
PG_PORT=$PG_SAT_PORT \
python setup/5-add-federation-connectors.py
```

### Option B — two separate steps

```bash
# Step 1: get the Satellite Link hostnames/ports (human-readable)
python setup/satellite-endpoints.py \
  --api-key "<IBM_CLOUD_API_KEY>" \
  --account-id "<ACCOUNT_ID>" \
  --connector-id "<CONNECTOR_ID>" \
  --ibmi-ip "<IBMI_IP_FROM_TECHZONE>"
# Read the "Cloud Host" lines from the output, then:

# Step 2: feed them explicitly as CLI args
python setup/5-add-federation-connectors.py \
  --wxd-apikey "<STUDENT_API_KEY>" \
  --wxd-crn "<INSTANCE_CRN>" \
  --ibmi-host "<IBMI_SAT_HOST>" \
  --ibmi-port "<IBMI_SAT_PORT>" \
  --ibmi-username "<IBMI_OS_USER>" \
  --ibmi-password "<IBMI_OS_PASSWORD>" \
  --pg-host "<PG_SAT_HOST>" \
  --pg-port "<PG_SAT_PORT>"
```

For **Path B** (no IBM i), add `--pg-only` and omit the `--ibmi-*` args:
```bash
python setup/5-add-federation-connectors.py \
  --wxd-apikey "<STUDENT_API_KEY>" \
  --wxd-crn "<INSTANCE_CRN>" \
  --pg-host "<PG_SAT_HOST>" \
  --pg-port "<PG_SAT_PORT>" \
  --pg-only
```

**API field note:** The watsonx.data v3 REST API uses `display_name` / `type` / `connection`
(not `database_display_name` / `database_type` / `details`) — confirmed via live probing.
Port must be an integer. `5-add-federation-connectors.py` uses the correct field names.

**Verify connectors** in the watsonx.data Query workspace:
```sql
SHOW SCHEMAS IN ibmi_olist;                            -- should show: OLIST  (Path A)
SHOW SCHEMAS IN pg_olist;                              -- should show: olist
SELECT COUNT(*) FROM pg_olist.olist.tier2_suppliers;   -- should show: 50
SHOW CATALOGS;                                         -- should include: iceberg_data2
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
- Confirm the PostgreSQL connection string in the UI env is correct (`PGHOST`, `PGPORT`, `PGUSER`, `PGPASS`)

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
| Non-blocking start (nohup pattern) | `nohup npm start > ~/demo-ui.log 2>&1 & disown; echo started` |
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
| EDB AS repo returns 404 during `--install-edb` | No ppc64le packages; token required | Expected — script uses PostgreSQL 16 automatically (identical for this demo) |
| psycopg2 import error locally | Not needed | All DB ops use SSH + psql; no local psycopg2 required |
