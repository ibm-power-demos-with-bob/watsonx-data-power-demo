# Federation & Demo Deployment Runbook

Complete step-by-step guide to deploying the watsonx.data on IBM Power demo on
fresh TechZone reservations. Follow the steps in order — GUI steps are clearly
marked and include what to capture while you are there.

---

## Architecture

All traffic between on-prem and IBM Cloud flows through a single IBM Cloud
Satellite Connector tunnel. The agent on RHEL makes one outbound WebSocket
connection (`WSS`) to IBM Cloud; that tunnel carries traffic in **both
directions** via two endpoint types:

```
Demo UI (RHEL :3000)
  → localhost:29999  [cloud endpoint: wxd-presto]
    → Satellite tunnel → IBM Cloud
      → Presto engine (*.lakehouse.ibmappdomain.cloud:<port>)

watsonx.data Presto (IBM Cloud)
  → c-01.private.eu-gb.link.satellite.cloud.ibm.com:33156  [location endpoint: pg-olist]
    → Satellite tunnel → RHEL
      → PostgreSQL (127.0.0.1:5432)

  → c-01.private.eu-gb.link.satellite.cloud.ibm.com:33180  [location endpoint: ibmi-db2]
    → Satellite tunnel → RHEL
      → IBM i (<ibmi-ip>:8471)
```

**Why the tunnel is required:** both the Presto engine
(`*.lakehouse.ibmappdomain.cloud`) and the watsonx.data REST API
(`eu-gb.lakehouse.cloud.ibm.com`) sit behind a Cloudflare policy that rejects
requests originating outside IBM Cloud. Routing Demo UI queries through the
`wxd-presto` cloud endpoint means requests arrive from inside IBM Cloud and are
accepted. ⚠️ Do not attempt to call either hostname directly from RHEL or a
laptop.

**Satellite endpoints for this demo (stable across reservations):**

| Name | Type | RHEL address | IBM Cloud address | Destination |
|---|---|---|---|---|
| `pg-olist` | location | n/a | `c-01.private.eu-gb.link.satellite.cloud.ibm.com:33156` | `127.0.0.1:5432` |
| `ibmi-db2` | location | n/a | `c-01.private.eu-gb.link.satellite.cloud.ibm.com:33180` | `<ibmi-ip>:8471` |
| `wxd-presto` | cloud | `localhost:29999` | n/a | `<presto-host>:<presto-port>` |

---

## Prerequisites

- Three TechZone reservations all **Ready**:
  - On-prem combined IBM i + RHEL (same `/28` subnet, same VLAN)
  - IBM Cloud Satellite (provides the Connector in ITZ-V2 account)
  - watsonx.data SaaS
- `setup/config.env` created from `setup/config.env.template` and populated
  with values from the TechZone reservation outputs
- SSH key for on-prem VMs downloaded from the on-prem reservation output
- IBM VPN connected (required to reach `129.40.x.x` on-prem addresses)

---

## Step 1 — Bootstrap the repo on RHEL

```bash
# On RHEL (SSH in first):
sudo dnf install -y git
git clone https://github.com/ibm-power-demos-with-bob/watsonx-data-power-demo.git
cd ~/watsonx-data-power-demo
```

Then copy your local `setup/config.env` to the RHEL VM:

```powershell
# From laptop (PowerShell):
scp -i "C:\Users\<user>\Downloads\<env-key>_key.pem" `
    setup/config.env `
    <OS_USER>@pvm01-<env-key>.p637.pok-systems.techzone.ibm.com:~/watsonx-data-power-demo/setup/config.env
```

---

## Step 2 — Start the Satellite agent

```bash
# On RHEL:
bash ~/watsonx-data-power-demo/setup/start_satellite_agent.sh
```

Confirm connection (wait ~15 s):

```bash
sudo podman logs wxd-connector-agent 2>&1 | grep -E "WSR04|CTB27|CTB20"
```

Expected output:
```
WSR04  Connected successfully
CTB27  Tunnel connected  (TLSv1.3)
CTB20  Created TCP Listener on port 29999.  ep=wxd-presto
```

If `wxd-presto` listener does not appear, the endpoint may not exist yet — run
`python3 setup/bootstrap_sat_endpoints.py` from the laptop to create it.

---

## Step 3 — 🖥️ GUI: Run the watsonx.data wizard

> **Must be done as the student App ID — never your IBM ID.**

1. Open an incognito/private browser window
2. Navigate to `https://cloud.ibm.com/authorize/itzwatsonx`
3. Log in with the student App ID credentials from the reservation output:
   `student_<env-key>_<env-id>_1@techzone.ibm.com` / `<password>`
4. If prompted, accept the `itz-watsonx` account invitation via the
   **notification bell** (top-right) — no email is sent, check the bell icon
5. Click **"Open web console"** from the TechZone reservation page
6. The wizard appears — select **"Run high-performance analytics (Presto C++)"**
7. Set the **catalog name** to `wxd_<env-key-suffix>` (e.g. `wxd_tqj6kn2k`)
   — ⚠️ never use `iceberg_data` — it is permanently taken in the shared MDS
8. Accept the **auto-discovered COS bucket** — do not create a new one
9. Click **Finish** — the engine will show PROVISIONING (5–10 min)

---

## Step 4 — 🖥️ GUI: Capture the Presto engine hostname *(while engine provisions)*

> **Do this while the engine is still PROVISIONING — you do not need to wait
> for RUNNING to read the hostname.**

1. In the watsonx.data console → **Infrastructure Manager**
2. Click the **Starter** engine tile
3. Find the **Engine details** panel — copy the hostname and port. It will look like:
   ```
   ff5b1b42-0d0a-4d03-ac39-b4529cbda74c.d4mn75il0dt1ob8mmlug.lakehouse.ibmappdomain.cloud:32564
   ```
4. Also note the **Engine ID** (e.g. `prismo970`) — needed for ACL grant

**Paste the hostname and port here / into `config.env`:**

```bash
# Add to setup/config.env:
PRESTO_HOST=<uuid>.d4mn75il0dt1ob8mmlug.lakehouse.ibmappdomain.cloud
PRESTO_PORT=<port>   # e.g. 32564  (NOT always 31618 — read from the GUI)
```

Then update the `wxd-presto` Satellite endpoint from the laptop:

```bash
# From laptop:
cd setup
PRESTO_HOST=<paste-here> PRESTO_PORT=<paste-here> python _patch_wxd_presto.py
```

Verify the endpoint shows the new destination:
```
wxd-presto   dest=<uuid>.d4mn75il0dt1ob8mmlug.lakehouse.ibmappdomain.cloud:<port>  client_port=29999
```

---

## Step 5 — Load PostgreSQL data

```bash
# From laptop (SSH-driven):
cd setup
python 8-load-edb-olist.py
```

This installs PostgreSQL 16 on RHEL, creates the `olist` schema, loads all
tables, and creates the compat views. Verify:

```bash
ssh -i <key> <user>@<rhel-fqdn> \
  "psql -U edbadmin -d olist -c 'SELECT COUNT(*) FROM tier2_suppliers'"
# Expect: 50
```

---

## Step 6 — Load IBM i data

```bash
# From laptop (SSH-driven):
python 6-load-ibmi-olist.py
```

Then run the compat views and SECTOR classification on IBM i:

```bash
bash setup/run_ibmi_steps.sh
```

Verify (from IBM i SSH session):
```sql
SELECT COUNT(*) FROM OLIST.ORDERS;        -- expect 99441
SELECT COUNT(*) FROM OLIST.V_CUSTOMERS;   -- expect same, no error
```

> **IBM i RDB name** — needed for the federation connector registration.
> Find it via:
> ```
> WRKACTJOB  → look for system name in the header, e.g. PVM02XJK
> ```
> or in IBM i SSH: `db2 "VALUES(CURRENT SERVER)"`

---

## Step 7 — 🖥️ GUI: Register federation connectors

> Both connectors must be registered through the watsonx.data GUI — this is
> the proven reliable path. The REST API path works but requires the exact
> payload shape documented below.

### PostgreSQL (`pg_olist`)

1. Infrastructure Manager → **Add component** → **PostgreSQL**
2. Fill in:
   | Field | Value |
   |---|---|
   | Display name | `pg_olist` |
   | Hostname | `c-01.private.eu-gb.link.satellite.cloud.ibm.com` |
   | Port | `33156` |
   | Database name | `olist` |
   | Username | `edbadmin` |
   | Password | `edbadmin1` |
   | SSL | disabled |
3. Click **Test connection** — must show ✅ before saving
4. Click **Create** — catalog `pg_olist` appears in Infrastructure Manager
5. If catalog shows `Engines associated = 0`: click the catalog → **Associate engine** → select **Starter**

### IBM i / Db2 for i (`ibmi_olist`)

1. Infrastructure Manager → **Add component** → **IBM Db2 for i**
2. Fill in:
   | Field | Value |
   |---|---|
   | Display name | `ibmi_olist` |
   | Hostname | `c-01.private.eu-gb.link.satellite.cloud.ibm.com` |
   | Port | `33180` |
   | Database name | `<IBM-i-RDB-name>` (e.g. `PVM02XJK` — from Step 6) |
   | Username | `<OS_USER>` (from reservation, e.g. `U8GO7IL`) |
   | Password | `<OS_PASSWORD>` (from reservation) |
   | SSL | disabled |
3. Click **Test connection** — must show ✅ before saving
4. Click **Create** — catalog `ibmi_olist` appears
5. Associate with **Starter** engine if needed (same as above)

---

## Step 8 — 🖥️ GUI: Grant catalog access to the service ID

The watsonx.data service API key (used by the Demo UI) runs as a service ID
that must have explicit DataAccess grants on both federated catalogs.

1. watsonx.data console → **Access control** (left nav)
2. Select the **Catalogs** tab
3. For **`pg_olist`**:
   - Click **Grant access** → search for the service ID name
     (e.g. `itz-110000sg2k-tqj6kn2k`) → grant **DataAccess**
4. Repeat for **`ibmi_olist`**

> If the service ID doesn't appear in the search, run `setup/seed_service_id.py`
> from RHEL (through the tunnel) first — this makes an authenticated call that
> registers the service ID in the MDS, making it searchable.

---

## Step 9 — Deploy the Demo UI

```bash
# From laptop — copies, builds, and starts the UI on RHEL:
bash demo-ui/remote-deploy-demo-ui.sh
```

Or manually:

```bash
# 1. Copy to RHEL
scp -i <key> -r demo-ui/ <user>@<rhel-fqdn>:~/watsonx-data-power-demo/

# 2. On RHEL — create .env.local
cat > ~/watsonx-data-power-demo/demo-ui/.env.local << 'EOF'
WXD_PRESTO_HOST=localhost
WXD_PRESTO_PORT=29999
WXD_APIKEY=<service-api-key-from-reservation>
WXD_INSTANCE_CRN=crn:v1:bluemix:public:lakehouse:eu-gb:a/<account-id>:<instance-guid>::
EOF

# 3. Build and start
cd ~/watsonx-data-power-demo/demo-ui
npm install
npm run build
bash restart.sh
```

---

## Step 10 — Smoke test

### Verify Presto tunnel from RHEL

```bash
# On RHEL — quick Presto connectivity check through cloud endpoint:
curl -sk -o /dev/null -w "%{http_code}" \
  -X POST https://localhost:29999/v1/statement \
  -H "X-Presto-User: ibmlhapikey" \
  --data "SHOW CATALOGS"
# Expect: 200
```

### Verify in watsonx.data Query Workspace

```sql
SHOW CATALOGS;
-- expect: hive_data, pg_olist, ibmi_olist, wxd_<env-key>

SHOW SCHEMAS IN pg_olist;
SELECT COUNT(*) FROM pg_olist.olist.v_tier2_suppliers;     -- expect: 50

SHOW SCHEMAS IN ibmi_olist;
SELECT COUNT(*) FROM ibmi_olist.OLIST.V_CUSTOMERS;         -- expect: 99441
```

### Verify Demo UI

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/
# Expect: 200
```

Open in browser: `http://<rhel-fqdn>:3000`

Run the full demo arc:
1. `/` — Static report loads with supplier data
2. `/live?scenario=cyber` → inject signal → alert appears with `source: live`
3. `/outcome?scenario=cyber` — outcome timeline renders
4. `/live?scenario=wildfire` → inject signal → alert appears
5. `/outcome?scenario=wildfire` — outcome timeline renders

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Cloudflare 403 calling `*.lakehouse.*` from RHEL/laptop | Request not routed through Satellite tunnel | Only call Presto via `localhost:29999`; never directly |
| `WSR04` not in agent logs | Agent not started or wrong connector ID | Re-run `start_satellite_agent.sh`; verify `SAT_CONNECTOR_ID` in `config.env` |
| `CTB20 port 29999` missing from agent logs | `wxd-presto` endpoint not created | Run `bootstrap_sat_endpoints.py` from laptop |
| `Connection failed - Invalid hostname or credentials` in GUI | Wrong RDB name (`*LOCAL` instead of system name) or wrong Satellite endpoint | Use actual RDB name from `WRKACTJOB`/`db2 "VALUES(CURRENT SERVER)"`; confirm endpoint is `c-01.private.eu-gb.link.satellite.cloud.ibm.com` |
| `LHAMS0003E` on watsonx.data console | Timing / logged in as IBM ID / invite not accepted | Wait 5 min; use student App ID only; accept invite via notification bell |
| `catalog does not exist` in Query Workspace | Catalog registered but not associated to engine | Infrastructure Manager → catalog tile → Associate engine → Starter |
| `Access denied: USE catalog pg_olist` | Service ID missing DataAccess grant | Step 8 — grant DataAccess to service ID on both catalogs |
| `Unknown type char(32)` from Prestissimo | Source table has raw `CHAR(N)` columns | Query the compat views (`v_*` in PostgreSQL, `V_*` on IBM i) not the base tables |
| Demo UI shows `source: stub` | `WXD_PRESTO_HOST` not set in `.env.local`, or Presto unreachable | Check `.env.local` has `WXD_PRESTO_HOST=localhost` and `WXD_PRESTO_PORT=29999`; verify curl test above |
| Demo UI port 3000 not reachable from browser | firewalld blocking or UI not started | Check `sudo systemctl status firewalld`; check `curl localhost:3000` from RHEL |
