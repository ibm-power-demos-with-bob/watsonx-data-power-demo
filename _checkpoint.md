# 🔖 Checkpoint — watsonx.data on IBM Power Demo

## Current Status
**Session 17 — COMPLETE. Full demo stack is running end-to-end.**

All three TechZone environments are Ready and fully operational. Federation is live:
- IBM i Db2 (`ibmi_olist`) — 99,441 customers, 112,650 order items queryable via Presto
- PostgreSQL 16 on RHEL (`pg_olist`) — 3,095 suppliers, 112,650 purchase orders
- Cross-catalog join confirmed working (PG ↔ IBM i 3-way join)
- Demo UI running on RHEL at `http://pvm01-4r13fr3k.p604.pok-systems.techzone.ibm.com:3000`

> Full session history → [`_session-log.md`](_session-log.md)
> Environment details → [`checkpoint-environments.md`](checkpoint-environments.md)

---

## Active Reservations (Session 16)

| Environment | Status | Key details |
|---|---|---|
| **IBM i + RHEL (On-prem)** | ✅ Ready | `UHJ907M` / `v07zF-4WDyP_a4x` / `pvm-4r13fr3k-key.pem` |
| **IBM Cloud Satellite** | ✅ Ready | ID `6abe30c2db5476036233b2a2` / API key `MH_j3NAOnqXLvgu1Z34KPa38MW6h_KtVyzr_BB7gVHyE` |
| **watsonx.data Dev Image** | ✅ Ready | SSH port `44574` / Presto port `48872` / `eu-de.services.cloud.techzone.ibm.com` |

---

## What Is Known-Good This Session

- **IBM i RDB name**: `PVM02X4R` (confirmed live via `DSPRDBDIRE`)
- **Satellite endpoints**: both updated and verified via API:
  - `ibmi-db2` → `c-01.private.eu-gb.link.satellite.cloud.ibm.com:33180` → `129.40.252.51:8471` ✅
  - `pg-olist`  → `c-01.private.eu-gb.link.satellite.cloud.ibm.com:33156` → `129.40.252.57:5432` ✅
- **Satellite connector ID**: `U2F0ZWxsaXRlQ29ubmVjdG9yOiJkYTdoc29tbDFxc2Zhb2FhbGhqZyI` (persists across reservations for this user; new users must look it up from the IBM Cloud UI)
- **Dev Image JWT auth**: `POST https://localhost:9443/lakehouse/api/v2/auth/authenticate` with body `{"username":"ibmlhadmin","password":"password","instance_id":"0000-0000-0000-0000","instance_name":"lh-default"}` → returns `accessToken` ✅
- **Dev Image registration payload**: credentials go inside `database_details` (not top-level) in v2.2
- **Dev Image always does a live connection test** before registering a catalog — no skip option exists. Registration will fail until Satellite agent is running on RHEL.

---

## What Was Done This Session (Session 17)

- IBM i DRDA password set via `setup/0-set-ibmi-password.py`
- IBM i OLIST library loaded (99,441 customers, 112,650 order items, 32,951 products, 99,441 orders)
- IBM i compat views created: `V_CUSTOMERS`, `V_ORDERS`, `V_ORDERITEMS`, `V_PRODUCTS` (no SECTOR col)
- RHEL: PostgreSQL 16 installed from PGDG repo (ppc64le), initialised, remote access configured
- RHEL: EDB olist data loaded — 3,095 suppliers, 23 warehouses, 112,650 purchase orders (GBP/GB)
- RHEL: PostgreSQL compat views applied (`v_suppliers`, `v_warehouses`, `v_tier2_suppliers`, `v_purchase_orders`)
- Satellite connector agent started via podman (ICR login required) — confirmed `WSR04 Connected`
- `pg_olist` and `ibmi_olist` registered in watsonx.data; `catalog_engine` rows inserted manually
- `setup/7-register-catalogs.py` password fixed: `edbadmin` (not `edbadmin1`)
- `test_federation_live.py` fixed: IBM i uses `count("customer id")` not `count(*)`
- Presto restarted to pick up new catalog_engine rows (45–60s boot time)
- Demo UI built and started on RHEL port 3000 — all pages HTTP 200, `/api/detect-signals` ok
- Query latency fix: `v_compromised_exposure` pre-aggregated view added to PostgreSQL; cyber exposure query now reads 1 row instead of 3-way join over 112k rows — ~35s → ~5s
- Poll interval reduced: 1,500ms → 500ms in `wxd-query-internal.ts`

---

## Next Steps (for a NEW TechZone reservation)

All steps are now scripted. On a fresh reservation, run in this order:

```bash
# Phase 1 — IBM i
python3 setup/0-set-ibmi-password.py --host <ibmi-fqdn> --user <user> --key <key> --password <pass>
python3 setup/6-load-ibmi-olist.py --host <ibmi-fqdn> --user <user> --ssh-key <key> --create-schema --skip-download --data-dir ./data/olist
python3 setup/_apply_ibmi_compat_views.py       # (update HOST/USER/KEY at top first)

# Phase 2 — RHEL
python3 setup/_setup_pg.py                       # creates edbadmin/olist DB
python3 setup/8-load-edb-olist.py --host <rhel-fqdn> --ssh-user <user> --ssh-key <key> --db-user edbadmin --db-password edbadmin --db-port 5432 --create-schema --skip-download --data-dir ./data/olist
python3 setup/_apply_pg_compat_views.py          # applies v_suppliers etc.
python3 setup/_configure_pg_remote.py            # listen_addresses=* + md5 auth
python3 setup/_restart_pg.py                     # full restart to pick up listen_addresses
python3 setup/2-configure-satellite.py           # update Satellite endpoints if IPs changed
python3 setup/_start_satellite_agent.py          # podman login ICR + start agent
python3 setup/_check_satellite_status.py         # confirm WSR04 Connected

# Phase 3 — watsonx.data
python3 setup/7-register-catalogs.py
python3 setup/_fix_catalog_engine.py             # insert catalog_engine rows + restart Presto
# wait ~60s for Presto to boot
python3 setup/test_federation_live.py
python3 setup/test_cross_catalog_join.py

# Phase 4 — Demo UI
python3 setup/_deploy_ui.py                      # uploads, builds, starts on port 3000
python3 setup/_check_ui.py                       # smoke test
```

---

## Known Quirks

- **Cyber query latency ~5s** — this is correct and expected; the spinner reinforces the "live federation" story. The `v_compromised_exposure` view pushes aggregation down to PostgreSQL (predicate pushdown), so Presto reads 1 row over the Satellite tunnel rather than joining 112k rows. Do not try to make it faster — 5s looks real, <1s looks fake.
- **IBM i `COUNT(*)`** fails with `SQL0206` — always use `COUNT("column_name")` for IBM i tables
- **IBM i `SELECT 1`** also fails — Presto/JDBC sends it as a NULL literal which IBM i rejects
- **`V_PRODUCTS` has no `SECTOR` column** — the SECTOR enrichment step hasn't been run; view works without it
- **Demo UI port 3000** is not exposed externally through TechZone network — access via SSH tunnel: `ssh -L 3000:localhost:3000 -i <key> <user>@<rhel-fqdn>` then browse `http://localhost:3000`
- **IBM i column names have spaces** not underscores — e.g. `"customer id"`, `"order id"`, `"seller id"`. Always quote them in Presto SQL
- **podman not docker** on RHEL 9 ppc64le — use `sudo podman` for all container ops
- **NodeSource doesn't support ppc64le** — Node.js installed from RHEL repos (v16), which works fine for Next.js 14

---

## Starting a New Task

### Continuing with the CURRENT reservation (session 17 still active)

```
Continuing the watsonx.data on IBM Power demo — session 17.
Read _checkpoint.md for the current state. The full stack is live.
  IBM i + RHEL: UHJ907M / v07zF-4WDyP_a4x / pvm-4r13fr3k-key.pem
  Dev Image: SSH 44574 / Presto 48872 / eu-de.services.cloud.techzone.ibm.com
  Demo UI: http://pvm01-4r13fr3k.p604.pok-systems.techzone.ibm.com:3000
```

### Starting a FRESH TechZone reservation

```
New TechZone reservation for the watsonx.data on IBM Power demo.
Read setup/RUNBOOK.md for the authoritative setup steps.

I have updated setup/reservation.py with the new credentials:
  RESERVATION_PREFIX = "<new-prefix>"
  SSH_USER  = "<USER>"
  SSH_KEY   = r"C:\Users\029878866\Downloads\<key>.pem"
  IBMI_PASSWORD = "<password>"
  IBMI_RDB      = "<RDBNAME>"
  WXD_SSH_PORT  = <port>
  WXD_PRESTO_PORT = <port>

Please run each phase of the RUNBOOK in order (Phases 1–4).
All credentials are in reservation.py — no need to edit individual scripts.
```
