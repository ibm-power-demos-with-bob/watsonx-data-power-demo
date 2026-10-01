# watsonx.data on IBM Power — Setup Automation Briefing
### For: Rehan Shahid, AI Solution Architect, IBM Power
### From: David Spurway (Pre-Sales) — via IBM Bob assisted development

---

## 🔔 Update — Rehan's suggested API path (respond here first)

Rehan asked whether we have tried:

```bash
curl -k https://localhost:6443/lakehouse/api/v3/auth/authenticate \
  -H "Content-Type: application/json" \
  -d '{
    "username": "ibmlhadmin",
    "password": "password",
    "instance_id": "0000-0000-0000-0000"
  }'
```

**Answer: No — we have never tried this endpoint.**

All our authentication so far has been either:
- IBM Cloud IAM token exchange (`https://iam.cloud.ibm.com/identity/token`) — for the SaaS
  path, now abandoned
- The `secret:` header obtained via `docker exec ibm-lh-presto env | grep LH_INSTANCE_SECRET`
  — for the Dev Image API path we have been using

Port `6443` does not appear anywhere in our scripts. This endpoint looks like it could be the
missing piece — a way to obtain a proper JWT from inside the Dev Image VM using the known fixed
credentials (`ibmlhadmin`/`password`), which `lhconsole-api` would then recognise as the owner
identity when we POST the catalog registration.

### What we would try next

1. SSH into the Dev Image VM
2. Call the authenticate endpoint from inside the VM (localhost):
   ```bash
   sudo docker exec ibm-lh-presto curl -sk \
     -X POST \
     -H "Content-Type: application/json" \
     -d '{"username":"ibmlhadmin","password":"password","instance_id":"0000-0000-0000-0000"}' \
     https://localhost:6443/lakehouse/api/v3/auth/authenticate
   ```
   *(or call it directly from the VM shell if port 6443 is on the host, not inside a container)*

3. If it returns a JWT, use that as `Authorization: Bearer <token>` alongside the `secret:`
   header when POSTing to:
   ```
   POST https://172.18.0.4:3333/lakehouse/api/v2/0000-0000-0000-0000/database_registrations
   ```

4. Check whether the resulting catalog has an active `Access Control` tab in the UI
   (this is the tell — it only appears when lhconsole-api owns the catalog registration)

If that works, the fix is a one-line addition to `setup/7-register-catalogs.py`:
add a `get_lh_token(cfg)` function that calls this endpoint via SSH, and pass
the resulting token as a second auth header on the registration POST.

**This is our most promising lead yet — please confirm whether port 6443 is on the
container host or inside a specific container, and whether the `/v3/auth/authenticate`
path is the right one for Dev Image v2.2.0.**

---

---

## What We Are Building

A pre-sales demonstration that shows **watsonx.data federating live across IBM i and PostgreSQL
on IBM Power**, reacting to a real-time supply-chain disruption signal (cyber attack / wildfire)
in under a second — without moving data.

The demo stack:
- **IBM i (Db2 for i)** — core ERP data (customers, orders, products, order items)
- **PostgreSQL 16 on RHEL** — supplier/logistics data
- **watsonx.data Developer Base Image v2.2.0** — Presto engine with `db2fori` and `postgresql` federation connectors
- **IBM Cloud Satellite Connector** — tunnel from watsonx.data (IBM Cloud) back to on-prem data sources
- A **Carbon Design System Next.js UI** served from RHEL that runs live federated Presto queries

All three environments are provisioned from IBM TechZone. The demo works — cross-catalog joins
confirmed live in Session 13. The problem is repeatability.

---

## Architecture Overview

```
┌──────────────────────────────────────────────┐
│  IBM Cloud                                   │
│                                              │
│  ┌──────────────────────┐                   │
│  │  watsonx.data Dev     │                   │
│  │  Image v2.2.0        │                   │
│  │  (TechZone VMware,   │                   │
│  │   eu-de)             │                   │
│  │                      │                   │
│  │  Presto engine       │◄──── Demo UI      │
│  │  (ibmlhadmin/        │      queries      │
│  │   password)          │      (Basic auth) │
│  │                      │                   │
│  │  Catalogs:           │                   │
│  │   ibmi_olist         │──►  IBM Cloud     │
│  │   pg_olist           │     Satellite     │
│  └──────────────────────┘     Connector     │
│                                    │         │
└────────────────────────────────────┼─────────┘
                                     │  Satellite tunnel
                              ┌──────┴──────────────┐
                              │  On-prem (Poughkeepsie, TechZone)
                              │
                              │  RHEL VM
                              │  ├── Satellite agent (podman)
                              │  ├── PostgreSQL 16 (port 5432)
                              │  └── Demo UI (Next.js, port 3000)
                              │
                              │  IBM i VM
                              │  └── Db2 for i (DRDA port 446)
                              │       with compatibility views
                              └──────────────────────────────
```

---

## What Works (Confirmed in Session 13)

When catalogs are registered **through the watsonx.data GUI** everything works perfectly:

```sql
SHOW CATALOGS;
-- Returns: hive_data, ibmi_olist, iceberg_data, jmx, pg_olist, system, tpcds, tpch, wxd_system_data

SELECT * FROM pg_olist.olist.v_suppliers LIMIT 5;                         -- ✅ works
SHOW SCHEMAS IN ibmi_olist;                                                -- ✅ full library list
SELECT * FROM ibmi_olist.olist.v_customers LIMIT 1;                       -- ✅ works

-- 2-way cross-catalog join:
SELECT s.company_name, oi."seller id"
FROM pg_olist.olist.v_suppliers s
JOIN ibmi_olist.olist.v_orderitems oi ON s.supplier_id = oi."seller id"
LIMIT 5;                                                                   -- ✅ 5 rows confirmed

-- 3-way join including ibmi_olist.olist.v_orders WHERE order_status = 'delivered'
-- ✅ 5 rows confirmed
```

**The demo is real — not mocked. The audience sees live federated data from both sources.**

---

## The Problem: GUI Registration ≠ Automatable via API

Every TechZone reservation gives **fresh VMs with new IPs, ports, and credentials**. We need to
re-run setup from scratch each time (~45 minute target). The GUI-based catalog registration is
the blocker. Here is what we have discovered over 14 sessions of investigation:

### The Core Tension

| What the GUI does | What the REST API does |
|---|---|
| Registers the catalog ✅ | Registers (sometimes) ✅ |
| Writes `.properties` file to Presto catalog volume ✅ | Writes the file ✅ |
| Sets up Access Control rows in `ams_0000_0000_0000_0000` correctly ✅ | Either skips this or overwrites it ⚠️ |
| Catalog appears in `SHOW CATALOGS` ✅ | Catalog may NOT appear, depending on AMS policy ⚠️ |
| `Access control` tab on catalog is active (owned by lhconsole-api) ✅ | Tab is greyed out — catalog treated as "unowned" ⚠️ |
| Presto picks up catalog on next restart ✅ | Presto picks up catalog BUT won't serve it until AMS allows it ⚠️ |

### What We Have Tried

**Attempt 1 — Direct REST API (v2 endpoint) via SSH tunnel**

Script: [`setup/7-register-catalogs.py`](setup/7-register-catalogs.py)

POSTs to `https://172.18.0.4:3333/lakehouse/api/v2/0000-0000-0000-0000/database_registrations`
from inside the Dev Image VM (via SSH), using the `secret: <LH_INSTANCE_SECRET>` header.

- The POST returns 201 and a valid-looking JSON body
- The catalog row appears in `ibm_lh_repo` (the internal postgres DB)
- The `.properties` file is written to the Presto catalog volume
- **BUT**: the catalog does NOT reliably appear in `SHOW CATALOGS` from Presto
- **AND**: the `Access Control` tab on the catalog is greyed out in the UI

**Attempt 2 — Direct DB inserts into `ams_0000_0000_0000_0000`**

The Access Control layer uses a PostgreSQL table `ams_0000_0000_0000_0000` (a Casbin policy
table). We tried inserting the exact pattern the GUI writes:

```sql
INSERT INTO ams_0000_0000_0000_0000 (ptype, v0, v1, v2) VALUES
  ('g', 'Administrator', 'can_administer', 'catalogs/ibmi_olist'),
  ('g', 'User',          'can_use',        'catalogs/ibmi_olist');
```

- The insert succeeds
- Presto briefly sees the catalog
- **BUT**: `PolicySyncMgr` polls `lhconsole-api` every ~30 seconds and **overwrites the cache**
  back to a state without our rows — because lhconsole-api does not recognise the catalog
  as "owned" by it (the catalog was not registered through the GUI wizard path)

**Attempt 3 — Policy version bump**

The `lhconsole-api` has a `POST /access/policy_versions` endpoint that triggers a cache reload.
We call it after our inserts. Presto reloads from the DB and picks up our grants — temporarily.
But the next `PolicySyncMgr` cycle overwrites again.

**Attempt 4 — Wrote files directly to catalog volume**

Writing `.properties` files directly to `/mnt/infra/ibm-lh-catalogs/` and restarting Presto
causes the catalog to appear. But Presto still refuses to serve queries from it because AMS
(the access control layer) does not believe the catalog is registered — it has no ownership
record in lhconsole-api's internal state.

### What The GUI Does Differently

By observing GUI registration through Chrome DevTools (Network tab), we captured the exact
HTTP shape the browser sends:

```
POST /lakehouse/api/v2/0000-0000-0000-0000/database_registrations
Headers:
  secret: <LH_INSTANCE_SECRET>
  LhInstanceId: 0000-0000-0000-0000
  AuthInstanceId: 0000-0000-0000-0000
  Authorization: Bearer <JWT from browser session>   ← THIS is what we cannot replicate
Body:
  { "database_display_name": "pg_olist",
    "database_type": "postgresql",
    "database_details": { "hostname": ..., "port": ..., "database_name": "olist" },
    "username": "edbadmin",
    "password": "edbadmin1",
    "associated_catalog": { "catalog_name": "pg_olist" },
    "database_properties": [...] }
```

The GUI sends **both** the `secret` header AND a short-lived browser `Authorization: Bearer <JWT>`.

When we send only the `secret` header (which we can obtain programmatically via SSH), the API
accepts the request and returns 201 — but the resulting catalog record is missing the
**owner identity** field that lhconsole-api uses to bind the catalog to the Access Control
policy tree. So the catalog is registered as an "orphan" that Presto knows about but AMS
does not serve.

The JWT is an `IBMLH` token (`iss: *.lakehouse.saas.ibm.com`) — it is only obtainable via the
browser session, expires in ~35 minutes, and there is no documented API to obtain it
programmatically from outside the browser.

---

## The Specific Questions We Need Answered

These questions are aimed at anyone with access to the watsonx.data Dev Image internals,
or to the IBM watsonx.data product team:

### Q1 — Is there a supported API path for programmatic catalog registration on the Dev Image?

The Dev Image (`ibm-lh-dev` container stack) is a self-contained environment. Does it have
a service account or token that can be used to authenticate full catalog registration
(including the ownership record) without a browser session JWT?

Specifically: is there a way to call `POST /lakehouse/api/v2/0000-0000-0000-0000/database_registrations`
such that the resulting catalog is treated as "owned" by lhconsole-api and appears correctly
in the Access Control layer?

### Q2 — What is the `owner_username` / `created_by` field in `ibm_lh_repo`?

When the GUI registers a catalog, there is a field in the `database_registrations` table
(or equivalent) that records who created it. What value does the GUI write, and can we
replicate it via a direct DB insert after a secret-authenticated API call?

### Q3 — Is there a way to trigger a full AMS policy re-sync from ibm_lh_repo state?

Rather than trying to insert the right rows, is there an internal API call or container
command that tells lhconsole-api to "re-read all registered catalogs from `ibm_lh_repo`
and rebuild the AMS policy table from scratch"? This would let us register via direct
DB insert (bypassing the JWT requirement) and then trigger the sync.

### Q4 — What is the lhconsole-api source code / config that controls PolicySyncMgr interval?

If we could pause `PolicySyncMgr` long enough to do our inserts and then trigger a
controlled sync from our state, that would also solve the problem. Is there a config
flag, environment variable, or container command to do this?

### Q5 — IBM i connector specifics

We are using `db2fori` connector type with this JDBC URL:
```
jdbc:as400://<satellite-host>:<port>;naming=sql;errors=full;fullErrors=true;
```
The `<satellite-host>` is the IBM Cloud Satellite Link endpoint FQDN (e.g.
`c-01.private.eu-gb.link.satellite.cloud.ibm.com`) and `<port>` is the assigned Satellite
Link port (e.g. 33180).

We do **not** include a database name in the JDBC URL — the IBM i RDB name (e.g. `PVM02XU9`)
is passed as the `database_name` in the catalog registration payload only.

This works when registered via GUI. Is this the recommended configuration for IBM i
federation through Satellite on Dev Image v2.2.0?

---

## What a Fix Would Look Like

Our ideal outcome is a **one-command setup** on a fresh TechZone reservation:

```bash
IBMI_PASSWORD='<new password>' \
IBMI_DATABASE='<new RDB name>' \
IBMI_PORT=<new satellite port> \
PG_PORT=<new satellite port> \
python3 setup/7-register-catalogs.py
```

That script would:
1. SSH into the Dev Image VM
2. Register `pg_olist` and `ibmi_olist` via the internal API
3. Ensure both catalogs appear correctly in the AMS access control layer
4. Trigger a policy sync
5. Exit cleanly — allowing `python3 setup/test_cross_catalog_join.py` to confirm success

We are **one authentication gap away** from this working. The Presto engine, connectors,
data loading, IBM Cloud Satellite tunnel, and demo UI are all scripted and repeatable.
This single step — lhconsole-api catalog registration with full ownership — is the blocker.

---

## Environment Reference

| Component | Details |
|---|---|
| **Dev Image version** | IBM watsonx.data Development Lab v2.2.0 GA |
| **TechZone collection** | `show-business-value-of-watsonxdata-with-ibm-power` |
| **Internal API base** | `https://172.18.0.4:3333/lakehouse/api/v2/` (from inside VM) |
| **Instance ID** | `0000-0000-0000-0000` (fixed for all Dev Image reservations) |
| **Presto credentials** | `ibmlhadmin` / `password` (fixed) |
| **IBM i connector type** | `db2fori` (jt400-20.0.7.jar) |
| **Presto catalog volume** | `/mnt/infra/ibm-lh-catalogs/` |
| **AMS policy table** | `ams_0000_0000_0000_0000` in `ibm_lh_repo` (postgres) |
| **Policy sync service** | `PolicySyncMgr` in lhconsole-api (~30s poll interval) |

---

## Repo / Contact

The full codebase (setup scripts, demo UI, session log) is in the IBM Bob-managed project
`watsonx-data-power-demo`.

**Session log with full technical detail:** [`_session-log.md`](_session-log.md)
**Current state:** [`_checkpoint.md`](_checkpoint.md)
**Setup scripts:** [`setup/`](setup/)

Please reach out via Slack or email. Happy to walk through this live with screen share —
all the hard-won context is in the session log.
