# Setup Runbook — watsonx.data on IBM Power Demo

**Purpose:** Authoritative step-by-step guide for provisioning the full demo stack on a fresh
TechZone reservation. All steps are scripted — you should not need to touch any GUI.

---

## Prerequisites

Three TechZone reservations must all be **Ready** before starting:

| Environment | Reservation name |
|---|---|
| **IBM i + RHEL** | IBM Power Systems — IBM i and Linux (POWER) |
| **IBM Cloud Satellite** | IBM Cloud Satellite Connector |
| **watsonx.data Dev Image** | IBM watsonx.data Development Lab — 2.2.0 GA |

**All values change with every reservation.** Fill in `setup/reservation.py` — every script reads from there.

| Value | Where to find it | Changes each reservation? |
|---|---|---|
| `IBMI_HOST` | IBM i FQDN from IBM i + RHEL reservation details | ✅ Yes |
| `RHEL_HOST` | RHEL FQDN from IBM i + RHEL reservation details | ✅ Yes |
| `SSH_USER` | TechZone username from IBM i + RHEL reservation details | ✅ Yes |
| `SSH_KEY` | Path to downloaded `.pem` key from IBM i + RHEL reservation | ✅ Yes |
| `IBMI_PASSWORD` | IBM i OS password from IBM i + RHEL reservation details | ✅ Yes |
| `IBMI_RDB` | Run `DSPRDBDIRE` on IBM i after first SSH — e.g. `PVM02X3E` (not always the full prefix) | ✅ Yes |
| `WXD_SSH_PORT` | Dev Image reservation → Published Services → `22: SSH` port | ✅ Yes |
| `WXD_PRESTO_PORT` | Dev Image reservation → Published Services → `8443: Presto Port` | ✅ Yes |
| `SATELLITE_IAM_APIKEY` | Satellite reservation → Reservation Details → "IBM Cloud API key" → eye icon | ✅ Yes |
| `SATELLITE_CONNECTOR_ID` | IBM Cloud console → Satellite → Connectors → `wxd-power-connector` URL | ✅ Stable (same account) |

> The VM IPs (used by Satellite endpoints) are **resolved automatically** from the FQDNs by `2-configure-satellite.py` — you do not need to look them up or hardcode them.

---

## Quick-start prompt

Copy this into a new Bob session at the start of each fresh reservation:

```
New TechZone reservation for the watsonx.data on IBM Power demo.
Read setup/RUNBOOK.md then update setup/reservation.py with these values
and run each phase in order.

Credentials (all change every reservation):
  IBM i + RHEL host prefix: <pvm-XXXXXXXX>         (e.g. pvm-3ef70s3k — from reservation FQDNs)
  SSH user:         <USER>                          (from reservation details)
  SSH key:          C:\Users\...\<key>.pem          (downloaded from reservation)
  IBM i password:   <password>                      (from reservation details)
  IBM i RDB name:   <RDBNAME>                       (confirm via DSPRDBDIRE on IBM i)
  Dev Image SSH port:    <port>                     (Published Services → 22: SSH)
  Dev Image Presto port: <port>                     (Published Services → 8443: Presto Port)
  Satellite IAM API key: <key>                      (Satellite reservation → Reservation Details → IBM Cloud API key → eye icon)

Before running Phase 2: accept the IBM Cloud account invitation email
(arrives in your Outlook "Other" inbox from DTE DTE v2 Infrastructure —
click "Join now." to accept access to the ITZ-V2 account).
```

---

## Phase 1 — IBM i

> Standalone. No dependencies on RHEL or watsonx.data.

### Step 1 — Set DRDA password

The IBM i OS password enables Db2 DRDA authentication (used by the watsonx.data connector).

```bash
python3 setup/0-set-ibmi-password.py \
  --host <IBMI_HOST> \
  --user <SSH_USER> \
  --key  "<SSH_KEY>" \
  --password '<IBMI_PASSWORD>'
```

Expected: `CPC2205: User profile <USER> changed.`

### Step 2 — Load OLIST data

```bash
python3 setup/6-load-ibmi-olist.py \
  --host <IBMI_HOST> \
  --user <SSH_USER> \
  --ssh-key "<SSH_KEY>" \
  --create-schema --skip-download --data-dir ./data/olist
```

Expected: `OK: OLIST/CUSTOMERS loaded` … `OK: OLIST/ORDERITEMS loaded` (4 tables, ~100k rows each).

### Step 3 — Apply compat views

> **Why:** Presto's Db2 for i connector can't map CHAR(N) columns — it throws `Unknown type char(32)`.
> These views expose them as VARCHAR so Presto can read them.

```bash
python3 setup/_apply_ibmi_compat_views.py
```

Update `HOST`, `USER`, `KEY` at the top of the file first. Expected: `SQL7951: View V_CUSTOMERS created` ×4.

---

## Phase 2 — RHEL (PostgreSQL + Satellite connector)

> All steps run against the RHEL VM. Scripts read credentials from `setup/reservation.py`.

### Step 4 — Install PostgreSQL and load OLIST data into PostgreSQL

> **`--install-edb` is required on a fresh instance** — PostgreSQL will not be present.
> The flag installs PostgreSQL 16 from PGDG (EDB AS if available, community PG16 as fallback),
> initialises the cluster, configures remote access, and creates the `edbadmin` user.
> Safe to omit on re-runs if PostgreSQL is already installed.

```bash
python3 setup/8-load-edb-olist.py \
  --host <RHEL_HOST> \
  --ssh-user <SSH_USER> \
  --ssh-key "<SSH_KEY>" \
  --db-user edbadmin --db-password edbadmin --db-port 5432 \
  --install-edb --create-schema --skip-download --data-dir ./data/olist
```

Expected: `EDB_INSTALL_OK` then `OK olist.suppliers: 3095 rows` … `OK olist.purchase_orders: 112650 rows`.

### Step 6 — Apply PostgreSQL compat views

```bash
python3 setup/_apply_pg_compat_views.py
```

Expected: `CREATE VIEW` ×5 (`v_tier2_suppliers`, `v_suppliers`, `v_warehouses`, `v_purchase_orders`, `v_compromised_exposure`).

> `v_compromised_exposure` pre-aggregates the 3-way supplier exposure join inside PostgreSQL.
> This is what keeps the cyber incident query at ~5s rather than ~35s over the Satellite tunnel.
> The 5s latency is intentional — the spinner makes the federation visible to the customer.

### Step 7 — Configure remote access

```bash
python3 setup/_configure_pg_remote.py
python3 setup/_restart_pg.py
```

Sets `listen_addresses = '*'` and md5 auth, then **full restarts** PostgreSQL (reload is not sufficient
for `listen_addresses`). Expected: `listen_addresses = '*'` and `LISTEN 0.0.0.0:5432`.

### Step 8 — Confirm Satellite endpoints

```bash
python3 setup/2-configure-satellite.py
```

Updates Satellite endpoint targets if the VM IPs have changed. Expected: `[OK] ibmi-db2` and `[OK] pg-olist`.

### Step 8a — Accept IBM Cloud account invitation (REQUIRED — first-time per user)

> **Every user must do this once** before the Satellite connector agent can pull from ICR.
> The Satellite reservation lands in the `ITZ-V2` IBM Cloud account (`DTEV2`, account ID `ead8711ba2cc4d08a16fd37427f4f01a`).
> Until you accept the invitation, the IAM API key cannot authenticate to ICR.
> If you skip this, `setup/_start_satellite_agent.py` will fail with `invalid username/password`.

1. Shortly after the IBM Satellite reservation reaches **Ready**, an invitation email arrives from IBM Cloud
2. **Check your "Other" inbox** (not "Focused") — the email is often filtered there by Outlook
3. The email subject is *"Action required: You are invited to join an account in IBM Cloud"* from DTE DTE v2 Infrastructure
4. Click **"Join now."** in the email body
5. Log in with your IBMid if prompted — you should land on the IBM Cloud console in the `ITZ-V2` account
6. Confirm you can see the Satellite locations page — this means the invitation is accepted

Only then proceed to Step 9.

### Step 9 — Start Satellite connector agent

```bash
python3 setup/_start_satellite_agent.py
```

Logs in to ICR with the IAM API key (uses `sudo podman` — RHEL 9 ppc64le does not have Docker),
pulls the connector image, and starts the container. Expected logs after ~20s:

```
WSR04 — Connected successfully
CTB27 — Tunnel connected
```

If `WSR04` doesn't appear, wait 30 more seconds and run `setup/_check_satellite_status.py`.

---

## Phase 3 — watsonx.data catalog registration

> Only run after the Satellite connector shows `WSR04 Connected`.

### Step 10 — Register and activate federation catalogs

Update `IBMI_DATABASE`, `WXD_SSH_PORT`, and `IBMI_PASSWORD` in the script config (or pass as env vars):

```bash
IBMI_PASSWORD='<password>' python3 setup/7-register-catalogs.py
```

This script now does **all five sub-steps** automatically:
1. Obtain JWT from Dev Image
2. Discover `LH_INSTANCE_SECRET`
3. Register `pg_olist` and `ibmi_olist` via lhconsole-api (skips if already registered)
4. Insert `catalog_engine` rows linking both catalogs to `presto-01`
5. Restart Presto and wait 75s for full initialisation

Expected final output:
```
=== Step 5: Restart Presto to pick up new catalog_engine rows ===
  Presto: ibm-lh-presto Up 1 minute
```

### Step 11 — Verify federation

```bash
python3 setup/test_federation_live.py
python3 setup/test_cross_catalog_join.py
```

Expected:
```
SHOW CATALOGS: [... 'ibmi_olist' ... 'pg_olist' ...]
PG v_suppliers COUNT: [[3095]]
IBMi v_customers COUNT: [[99441]]
Cross-catalog join rows: 5
3-way join (delivered orders): 5
```

---

## Phase 4 — Demo UI

### Step 12 — Deploy and start the UI

Update `HOST`, `USER`, `KEY` and the `ENV_CONTENT` Presto port at the top of the script:

```bash
python3 setup/_deploy_ui.py
```

Uploads the `demo-ui/` source, runs `npm install && npm run build`, writes `.env.local`, and starts
`npm start` on port 3000.

### Step 13 — Smoke test

```bash
python3 setup/_check_ui.py
```

Expected: all four pages return `HTTP 200`.

**Access the UI at:**
```
http://<RHEL_HOST>:3000
```

---

## Known quirks

| Issue | Cause | Fix |
|---|---|---|
| `SQL0206: Column NULL not found` on IBM i | Presto JDBC sends `SELECT 1` / `COUNT(*)` as a NULL literal | Use `COUNT("column_name")` — never `COUNT(*)` or `SELECT 1` on IBM i tables |
| `ibmi_olist`/`pg_olist` not in `SHOW CATALOGS` after registration | `catalog_engine` rows missing — lhconsole-api doesn't insert them automatically | Step 10 now handles this; if re-running manually use `setup/_fix_catalog_engine.py` |
| `authenticator was not loaded` (Presto 500) | Presto still booting | Wait 75s after restart before querying |
| `pg_olist` registration fails with 400 | PostgreSQL not listening on `0.0.0.0` | Run `_configure_pg_remote.py` + `_restart_pg.py` (not just reload) |
| `V_PRODUCTS` not created | `SECTOR` column doesn't exist on fresh PRODUCTS table | Fixed — view now created without SECTOR |
| `podman: command not found` or Docker errors | RHEL 9 ppc64le uses podman, not Docker | Scripts use `sudo podman`; ICR login required before pull |
| Node 16 on RHEL ppc64le | NodeSource explicitly rejects ppc64le (exit code 1) | `_deploy_ui.py` now skips NodeSource entirely and uses `dnf install nodejs npm` from RHEL AppStream — no manual action needed | None |
| Port 3000 not reachable externally | FirewallD not running on this VM type; TechZone network allows it | Access directly via `http://<RHEL_HOST>:3000` |

---

## Script inventory

| Script | Phase | What it does |
|---|---|---|
| `setup/0-set-ibmi-password.py` | 1 | Sets IBM i OS DRDA password |
| `setup/6-load-ibmi-olist.py` | 1 | Loads OLIST CSV data into IBM i Db2 |
| `setup/_apply_ibmi_compat_views.py` | 1 | Applies `10-ibmi-compat-views.sql` via RUNSQLSTM |
| `setup/_setup_pg.py` | 2 | Creates PostgreSQL `edbadmin` user and `olist` database |
| `setup/8-load-edb-olist.py` | 2 | Loads OLIST operational data into PostgreSQL |
| `setup/_apply_pg_compat_views.py` | 2 | Applies `11-pg-compat-views.sql` |
| `setup/_configure_pg_remote.py` | 2 | Sets `listen_addresses=*` and md5 auth in pg_hba.conf |
| `setup/_restart_pg.py` | 2 | Full PostgreSQL restart (required after listen_addresses change) |
| `setup/2-configure-satellite.py` | 2 | Creates/updates Satellite endpoints via IBM Cloud API |
| `setup/_start_satellite_agent.py` | 2 | podman login ICR + starts satellite-connector container |
| `setup/_check_satellite_status.py` | 2 | Tails connector logs to confirm WSR04 Connected |
| `setup/7-register-catalogs.py` | 3 | Full registration: JWT → register → catalog_engine → restart Presto |
| `setup/test_federation_live.py` | 3 | Verifies PG and IBM i catalogs visible and queryable |
| `setup/test_cross_catalog_join.py` | 3 | Verifies 3-way cross-catalog join |
| `setup/_deploy_ui.py` | 4 | Uploads source, npm build, starts UI on :3000 |
| `setup/_check_ui.py` | 4 | Smoke tests all UI pages via localhost curl |
