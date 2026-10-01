---
name: deploy-watsonx-data-power
description: >
  Full deployment guide for the watsonx.data on IBM Power presales demo on a fresh set
  of TechZone environments. Covers watsonx.data Developer Base Image reservation, IBM i
  data load, PostgreSQL 16 install and load, federation connector registration via the
  Dev Image UI, and demo UI deploy. Supports both DB path variants: Path A (IBM i +
  PostgreSQL) and Path B (PostgreSQL only). Also covers demo reset, re-run, and known
  failure modes.
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

**Primary architecture (confirmed working):**
- **watsonx.data:** Developer Base Image 2.2.0 GA — VMware, TechZone `eu-de`
- **Presto:** Basic auth `ibmlhadmin` / `password` — no IAM, no API keys
- **On-prem data:** IBM i + RHEL on the combined TxC Lab reservation (same network pod)
- **Connectivity:** IBM Cloud Satellite tunnel (RHEL agent → IBM Cloud) for federation endpoints

---

## What You Need Before Starting

Confirm you have the following before running any commands:

| Item | Source | Notes |
|------|--------|-------|
| watsonx.data Dev Image FQDN | TechZone reservation details | E.g. `eu-de.services.cloud.techzone.ibm.com` |
| watsonx.data Dev Image Presto port | TechZone reservation details | Noted as "Presto" port, e.g. `46662` |
| IBM i FQDN or IP | TechZone combined reservation details | Path A only |
| IBM i SSH private key path | Downloaded from TechZone reservation details | Path A only |
| IBM i SSH user | TechZone reservation details (e.g. `U8GO7IL`) | Path A only |
| IBM i OS password | TechZone reservation details | Used as Db2 for i JDBC auth password |
| RHEL VM FQDN | TechZone combined reservation details | Both paths |
| RHEL VM SSH private key path | Downloaded from TechZone reservation details | Both paths |
| RHEL VM SSH user | TechZone reservation details (e.g. `U8GO7IL`) | Both paths |
| Local path to this repo | Workspace root | `c:\Users\...\watsonx-data-power-demo` or equiv |

**IBM VPN must be active** — all TechZone environments are intranet-only.

**No IBM Cloud API key is needed.** The Dev Image uses Basic auth (`ibmlhadmin`/`password`) —
no IAM tokens, no Service IDs, no CRNs.

---

## DB Path Selection

Ask the user which path applies if not already stated:

- **Path A (IBM i + PostgreSQL):** Customer runs IBM i. IBM i = Source 1 (core ERP / Db2 for i).
  PostgreSQL = Source 2 (operational DB). Use this path by default.
- **Path B (PostgreSQL only):** No IBM i. PostgreSQL holds the full Olist dataset.
  Skip all IBM i steps below.

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

## Step 1 — Reserve the watsonx.data Developer Base Image

**This is a v1 TechZone environment — manual reservation only. Bob cannot reserve it automatically.**

Go to: https://techzone.ibm.com/collection/show-business-value-of-watsonxdata-with-ibm-power

Select: **watsonx.data Developer Base Image** (environment ID `6aad32346d68a71f122a688d`)

From the reservation details page, note:
- The **FQDN** — e.g. `eu-de.services.cloud.techzone.ibm.com`
- The **Presto port** — e.g. `46662`
- The **watsonx.data UI port** — e.g. `48544`
- The **SSH port** — e.g. `33130` (for direct OS access if needed)

**Credentials are fixed for all Dev Image reservations:**
| Service | Username | Password |
|---------|----------|---------|
| Presto (Basic auth) | `ibmlhadmin` | `password` |
| watsonx.data UI | `ibmlhadmin` | `password` |
| SSH (OS) | `watsonx` | `watsonx.data` |

Wait for the reservation status to show **Ready** before continuing.

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

### 2d. Apply compatibility views (required for watsonx.data federation)

IBM i `CHAR(N)` columns cause `Unknown type char(N)` errors in Presto. The fix is a set of
views that cast all key columns to `VARCHAR`.

```bash
ssh -i <ibmi-key> <ibmi-user>@<ibmi-fqdn> 'cat > /tmp/compat.sql' < setup/10-ibmi-compat-views.sql
ssh -i <ibmi-key> <ibmi-user>@<ibmi-fqdn> 'system "RUNSQLSTM SRCSTMF(\"/tmp/compat.sql\") COMMIT(*NONE)"'
```

Creates: `OLIST.V_CUSTOMERS`, `OLIST.V_PRODUCTS`, `OLIST.V_ORDERS`, `OLIST.V_ORDERITEMS`.
The federation queries use these views, not the base tables.

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

**For Path B (PostgreSQL only) — extend load to include full Olist dataset:**

Add the `--full-dataset` flag to also load CUSTOMERS, PRODUCTS, ORDERS, ORDERITEMS into PostgreSQL
(in addition to the supplier tables above). This flag is Path B only.

```bash
python setup/8-load-edb-olist.py \
  --host <rhel-fqdn> --ssh-user <rhel-user> --ssh-key <rhel-key> \
  --skip-download --full-dataset \
  --db-port 5432 --currency-code GBP --country-code GB
```

---

## Step 3b — Set IBM i Password for Db2 Authentication (Path A only)

**Do this before Step 4.** The IBM i OS password changes with every TechZone reservation. SSH uses
key auth so connectivity works fine, but Db2 DRDA authentication (used by watsonx.data federation)
validates the OS password directly. If this step is skipped, the `ibmi_olist` connector will fail
with an authentication error.

```bash
python3 setup/0-set-ibmi-password.py \
  --host <ibmi-ip> \
  --user <ibmi-user> \
  --key  "<path-to-ibmi-key>" \
  --password '<ibmi-os-password>'
```

All four values are on the TechZone reservation details page for the combined IBM i + RHEL reservation.

**Expected output:** `Password set for <USER> on IBM i at <IP>.`

---

## Step 4 — Configure IBM Cloud Satellite (connects Dev Image to on-prem data)

The Dev Image runs in IBM Cloud (`eu-de`). Your on-prem data (IBM i, PostgreSQL) is on the
TechZone intranet. IBM Cloud Satellite Connector bridges them.

### 4a. Reserve a Satellite Connector

Go to: https://techzone.ibm.com/collection/show-business-value-of-watsonxdata-with-ibm-power

Select the **IBM Cloud Satellite** environment and reserve it. From the reservation details:
- Note the **IBM Cloud account** (usually `ITZ-V2`)
- Accept the account invite via the **notification bell** at cloud.ibm.com (not email)

### 4b. Start the Satellite agent on the RHEL VM

```bash
# Download the agent start script from the Satellite console:
# IBM Cloud → Satellite → Connectors → <your connector> → Download agent start script

# Copy to RHEL and run
scp -i <rhel-key> connector-agent-start.sh <rhel-user>@<rhel-fqdn>:~/
ssh -i <rhel-key> <rhel-user>@<rhel-fqdn> 'chmod +x ~/connector-agent-start.sh && ~/connector-agent-start.sh'
```

**Verify:** In the Satellite console, the connector status should show **Connected**.

### 4c. Create Link endpoints

In the IBM Cloud Satellite console, create these **Location** endpoints (IBM Cloud → on-prem):

| Name | Destination host | Destination port | Protocol |
|------|-----------------|-----------------|---------|
| `pg-olist` | `127.0.0.1` (localhost on RHEL) | `5432` | TCP |
| `ibmi-db2` | `<ibmi-ip>` (e.g. `129.40.125.73`) | `8471` | TCP |

Each endpoint gets a cloud hostname like `c-01.private.eu-gb.link.satellite.cloud.ibm.com:<port>`.
Note the assigned port numbers — you will use them in Step 5.

**Enable** each endpoint after creation (toggle in the console).

---

## Step 5 — Register Federation Connectors

Run the registration script. It handles catalog registration, engine association, and access
control grants in one command — and triggers the policy version bump so Presto picks up the
grants immediately without a full restart:

```bash
IBMI_PASSWORD='<ibmi-os-password>' \
IBMI_USERNAME='<ibmi-user>' \
IBMI_DATABASE='<ibmi-rdb-name>' \
IBMI_PORT=<satellite-ibmi-port> \
PG_PORT=<satellite-pg-port> \
python3 setup/7-register-catalogs.py
```

- `IBMI_PASSWORD` — IBM i OS password (from TechZone reservation details, changes every reservation)
- `IBMI_USERNAME` — IBM i SSH/OS user (e.g. `UVU2BTL`) — from TechZone reservation details
- `IBMI_DATABASE` — IBM i RDB name (e.g. `PVM02XU9`) — find it with:
  ```bash
  ssh -i <ibmi-key> <ibmi-user>@<ibmi-fqdn> 'system "DSPRDBDIRE" | grep LOCAL'
  ```
- `IBMI_PORT` / `PG_PORT` — Satellite Link endpoint ports assigned in Step 4c
- All other values (Dev Image host/port/credentials, PostgreSQL credentials) are hardcoded
  defaults and do not change between reservations.

**Expected output:**
```
Step 1: Register catalogs in ibm_lh_repo  → INSERT 0 2 (or 0 0 if already present)
Step 2: Insert AMS access control rows    → INSERT 0 4 / INSERT 0 2
Step 3: Bump policy version               → {"policy_version": <n>}
Waiting 10s for Presto PolicySyncMgr to reload...
Done.
```

**Verify** (should return rows immediately after the script completes):
```bash
python3 setup/test_cross_catalog_join.py
```

### If the script succeeds but catalogs still don't appear in SHOW CATALOGS

The only remaining step is a Presto restart to regenerate `.properties` files:
```bash
# SSH into Dev Image and restart Presto
ssh -p 49753 watsonx@eu-de.services.cloud.techzone.ibm.com \
  'sudo docker restart ibm-lh-presto'
```
Wait ~60s then retry `test_cross_catalog_join.py`.

### GUI fallback (if the script fails)

Open `https://<dev-image-fqdn>:<ui-port>` — login `ibmlhadmin` / `password`

1. **Infrastructure Manager → Add Component → Database** — register each connector
   (if not already visible; the script's catalog rows mean they often already appear)
2. **Access Control → Catalogs → `pg_olist` → Add access** → add `ibmlhadmin` → Administrator
3. **Access Control → Catalogs → `ibmi_olist` → Add access** → add `ibmlhadmin` → Administrator
4. Restart Presto once after both grants are saved

**Note on GUI permissions errors:** The Dev Image GUI may show permission errors when editing
existing entries. This is a cosmetic issue with the GUI's edit path — the Add access action
(creating a new entry) works correctly even when Edit is blocked.

---

## Step 6 — Write .env.local on RHEL

```bash
ssh -i <rhel-key> <rhel-user>@<rhel-fqdn> 'cat > ~/watsonx-data-power-demo/demo-ui/.env.local' << 'EOF'
WXD_PRESTO_HOST=<dev-image-fqdn>
WXD_PRESTO_PORT=<presto-port>
WXD_PRESTO_SCHEME=https
WXD_PRESTO_USER=ibmlhadmin
WXD_PRESTO_PASSWORD=password
WXD_PG_CATALOG=pg_olist
WXD_IBMI_CATALOG=ibmi_olist
EOF
```

Replace `<dev-image-fqdn>` and `<presto-port>` with the values from Step 1.

**No `WXD_APIKEY`, `WXD_INSTANCE_CRN`, or `LhInstanceId` needed.** The Dev Image uses Basic
auth and does not require IAM headers.

**Verify the file was written correctly:**
```bash
ssh -i <rhel-key> <rhel-user>@<rhel-fqdn> 'cat ~/watsonx-data-power-demo/demo-ui/.env.local'
```

---

## Step 7 — Deploy the Demo UI

### 7a. Sync files to RHEL VM

```bash
# From workspace root (Windows: use scp -r or rsync via WSL)
scp -r -i <rhel-key> demo-ui/ <rhel-user>@<rhel-fqdn>:~/watsonx-data-power-demo/demo-ui/
```

### 7b. Install Node.js (version matters — check RHEL release first)

Next.js 13.4.9 requires Node ≥ 18. RHEL's default dnf stream ships Node 16 on RHEL 9 — too old.

```bash
ssh -i <rhel-key> <rhel-user>@<rhel-fqdn> "cat /etc/redhat-release"

# RHEL 9.x — enable Node 20 module stream:
ssh -i <rhel-key> <rhel-user>@<rhel-fqdn> \
  "sudo dnf module enable -y nodejs:20 && sudo dnf install -y nodejs && node --version"
# Expected: v20.x.x

# RHEL 10.x — Node 22 ships directly from AppStream (modularity removed in RHEL 10):
ssh -i <rhel-key> <rhel-user>@<rhel-fqdn> \
  "sudo dnf install -y nodejs && node --version"
# Expected: v22.x.x
```

**Important — fix permissions before npm install:** `scp -r` transfers directories as `dr-x------`
(no write bit). Always run this after scp:
```bash
ssh -i <rhel-key> <rhel-user>@<rhel-fqdn> "chmod -R u+rwX ~/watsonx-data-power-demo"
```

### 7c. Install dependencies and build

```bash
ssh -i <rhel-key> <rhel-user>@<rhel-fqdn> \
  "cd ~/watsonx-data-power-demo/demo-ui && npm install --legacy-peer-deps && npm run build 2>&1 | tail -8"
```

**Expected:** Build completes with `✓ Compiled` and route listing. If it fails:
- `Cannot find module '@carbon/react'` → run `npm install --legacy-peer-deps` again
- `SWC binary missing` → confirm Next.js is 13.4.9 (`cat package.json | grep '"next"'`)
- TypeScript errors → check for stray `.tsx` files in `src/pages/api/` (should only be `.ts` files there)

### 7d. Start the UI

```bash
ssh -i <rhel-key> <rhel-user>@<rhel-fqdn> \
  '~/watsonx-data-power-demo/demo-ui/restart.sh'
# Note: this command will show CANCELED in Bob UI — that is expected (nohup detaches)
```

### 7e. Verify

```bash
ssh -i <rhel-key> <rhel-user>@<rhel-fqdn> \
  'sleep 5 && curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/'
# Must return: 200
```

**The CANCELED status on the restart step is a known cosmetic issue.** The only reliable
confirmation is step 7e returning `200`. Do not skip the verification step.

---

## Step 8 — Smoke Test End-to-End

1. Open `http://<rhel-fqdn>:3000` in a browser (IBM VPN active)
2. Confirm the static report page (`/`) loads with product metrics
3. Navigate to `/sources` — confirm source cards are visible
4. Navigate to `/live?scenario=cyber` — confirm the POS stream is scrolling
5. Click **"Inject Cyber Signal"** — confirm an alert card appears within 3 seconds
6. The alert card should show `source: "live"` and data for a COMPROMISED supplier
7. Navigate to `/outcome?scenario=cyber` — confirm the timeline shows cyber outcome
8. Click **"Clear & reset"**, then navigate to `/live?scenario=wildfire`
9. Click **"Inject Wildfire Signal"** — confirm a wildfire alert card appears
10. Navigate to `/outcome?scenario=wildfire` — confirm wildfire timeline

If alert cards do not appear:
- Check `~/demo-ui.log` on the RHEL VM for errors
- Confirm `.env.local` has correct `WXD_PRESTO_HOST` and `WXD_PRESTO_PORT`
- Run a direct Presto query from RHEL to confirm Basic auth works:
  ```bash
  curl -s -u ibmlhadmin:password \
    "https://<dev-image-fqdn>:<presto-port>/v1/statement" \
    -H "Content-Type: text/plain" \
    --data "SHOW CATALOGS" -k | head -50
  ```
  Expected: JSON response containing `pg_olist` and `ibmi_olist`

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

These patterns were validated on RHEL 9.8 / ppc64le. Use them to avoid common pitfalls:

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
| Alert cards don't appear after inject | Dev Image Presto not reachable or `.env.local` wrong | Check `~/demo-ui.log`; verify `.env.local` vars; run direct curl test from RHEL |
| Presto returns 401 | Wrong Basic auth credentials | Dev Image always uses `ibmlhadmin`/`password` — confirm no typos in `.env.local` |
| Presto returns SSL/cert error | Dev Image uses self-signed cert | `WXD_PRESTO_SCHEME=https` is correct; the UI client skips cert verification already |
| IBM i SSH fails with `Permission denied` | Wrong key or wrong user | Download key from TechZone reservation details; confirm user has `*SECOFR` |
| CPYFRMIMPF fails with `MSGID(CPF2817)` | Existing rows in target table | DDL uses DROP+CREATE; re-run `--create-schema` then `--load-data` |
| `ibmi_olist` connector fails in watsonx.data | Wrong RDB name or CHAR type error | Confirm RDB name via `DSPRDBDIRE`; confirm compat views from Step 2d exist |
| `Unknown type char(32)` from IBM i | Base tables used instead of views | Queries must target `V_CUSTOMERS` etc. not `CUSTOMERS`; check compat views |
| `pg_olist` connector fails in watsonx.data | Wrong Satellite endpoint port | Confirm the Satellite endpoint for pg-olist is enabled and note the correct port |
| Satellite agent shows Disconnected | Agent not running on RHEL | SSH in and re-run the agent start script |
| `ibmi_olist` / `pg_olist` show "offline" in Infrastructure Manager | `lhconsole-api` connectivity probe times out through the Satellite tunnel — cosmetic only | Ignore. Verify with `test_cross_catalog_join.py` — if that returns rows, federation is working. The GUI status badge does not reflect Presto's actual query capability. |
| `SWC binary missing` on npm run build | Next.js > 13.x | Confirm `package.json` has `"next": "13.4.9"` |
| `Cannot find module 'live-feed-fetcher'` | Missing file on RHEL | Re-run the `scp -r demo-ui/` sync in Step 7a |
| EDB AS repo returns 404 during `--install-edb` | No ppc64le packages; token required | Expected — script falls back to PostgreSQL 16 automatically |
| psycopg2 import error locally | Not needed | All DB ops use SSH + psql; no local psycopg2 required |

---

## Dev Image vs SaaS — Key Differences

The demo **previously** used watsonx.data SaaS (IBM Cloud). It now uses the Developer Base Image.
Key differences a user coming from earlier sessions should know:

| | Developer Base Image (current) | watsonx.data SaaS (legacy) |
|---|---|---|
| TechZone env | VMware, `eu-de`, v1 | IBM Cloud, `eu-gb`, v1 |
| Presto auth | Basic auth `ibmlhadmin`/`password` | IAM Bearer token (API key) |
| Catalog registration | UI only (localhost API, no external access) | UI or API (API unreliable from outside IBM Cloud) |
| Connector naming | Generic names OK (`pg_olist`, `ibmi_olist`) | Must be reservation-unique (`pg_olist_<key>`) |
| `.env.local` vars | `WXD_PRESTO_USER`, `WXD_PRESTO_PASSWORD` | `WXD_APIKEY`, `WXD_INSTANCE_CRN` |
| Satellite needed? | Yes — for federation endpoints only | Yes — for Presto routing AND federation |
| Cloudflare blocking | Not applicable | Blocks external Presto calls (hard to work around) |
