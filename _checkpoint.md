# 🔖 Checkpoint — watsonx.data on IBM Power Demo

## Current Status
**Session 19/20 — FULL STACK DEPLOYED & COMPLEMENTARY BOND STRATEGIC INTELLIGENCE INVESTIGATION INTEGRATED.**

- Demo UI: `http://pvm01-edaaiu5k.p1356.pok-systems.techzone.ibm.com:3000` (or SSH tunnel `-L 3000:localhost:3000`)
- **Demo 1 (Operational Agility - Satnav)**: Both scenarios (`supplier-cyber-incident` ~6s, `eu-wildfire` ~5s) live and verified.
- **Demo 2 (Strategic Intelligence - Smartphone)**: Interactive 6-Act Bond Investigation (`/bond-investigation`) deployed on remote RHEL UI with live query execution, 3-clock confounder breakdown, and commercial enterprise translation bridge.
- Verified: all endpoints (`/`, `/live`, `/sources`, `/bond-investigation`, `/api/bond-query`) return HTTP 200.
- `SATELLITE_CONNECTOR_ID` now filled in `reservation.py`; agent shows `WSR04 Connected`.

**Session 19 deployment gotchas (found this session):**
- `data/olist/*.csv` are gitignored and were **0-byte placeholders** (sellers/products/translation) → `8-load-edb-olist.py` fails with "No columns to parse". Fix: re-download from Kaggle (`kaggle.api.dataset_download_files('olistbr/brazilian-ecommerce', ...)`; `~/.kaggle/kaggle.json` is present) and copy into `data/olist/`.
- `demo-ui/` source had been deleted from the working tree (still in git) → restored with `git checkout HEAD -- demo-ui`. Check `git status` before deploying.
- `_smoke_test_ui.py` now reads `reservation.py` (was hard-coded to old reservation). Its `/api/wxd-query-internal` check always shows "Internal Server Error" — that file is a helper module with no route; ignore it. Use `setup/_check_ui_queries.py` (inject-signal + POST /api/alerts) for a real end-to-end test.
- `_start_satellite_agent.py` prints a ✅ that crashes on Windows cp1252 console (harmless; set `PYTHONIOENCODING=utf-8`).

---

**Earlier in session 19 — IBM i Phase 1 COMPLETE.**

IBM i OLIST loaded via `setup/_diagnose_ibmi.py` (CUSTOMERS 99,441 / ORDERS 99,441 / ORDERITEMS 112,650 / PRODUCTS 32,951) and compat views applied via `_apply_ibmi_compat_views.py` (all 4 views exist). Verify with `python setup/_check_ibmi_load.py`.

Root causes of the earlier load failures (all fixed in `_diagnose_ibmi.py`):
1. `CREATE SCHEMA` in DDL conflicts with `CRTLIB` — RUNSQLSTM aborts silently. Fix: strip it before upload.
2. Failed CPYFRMIMPF attempts corrupted the file member. Fix: DLTLIB/CRTLIB reset.
3. Note: `CHKOBJ OBJ(OLIST/V_CUSTOMERS)` reports false MISSING — long SQL names get system names `V_CUS00001`/`V_ORD00001`. Check via `QSYS2.SYSTABLES` instead (`_check_ibmi_load.py`). `_check_ibmi_views.py` has this false-negative bug.

All three TechZone environments are Ready and fully operational. Federation is live:
- IBM i Db2 (`ibmi_olist`) — 99,441 customers, 112,650 order items queryable via Presto
- PostgreSQL 16 on RHEL (`pg_olist`) — 3,095 suppliers, 112,650 purchase orders
- Cross-catalog join confirmed working (PG ↔ IBM i 3-way join)
- Demo UI running on RHEL at `http://pvm01-4r13fr3k.p604.pok-systems.techzone.ibm.com:3000`

> Full session history → [`_session-log.md`](_session-log.md)
> Environment details → [`checkpoint-environments.md`](checkpoint-environments.md)

---

## Active Reservations (Session 19 — current)

All three are **Ready**. All expire **31 Oct 2026** (~12:05–12:10 UTC).

| Environment | Request ID | Status | Expires |
|---|---|---|---|
| **IBM i + RHEL** | `6ae08c9014551a1d930e9d4d` | ✅ Ready | 31 Oct 12:05 UTC |
| **watsonx.data Dev Image** | `6ae08cfd2416223c66b20f81` | ✅ Ready | 31 Oct 12:10 UTC |
| **IBM Satellite** | `6ae08d3493a341e8c94fe628` | ✅ Ready | 31 Oct 11:45 UTC |

### IBM i + RHEL credentials
| Field | Value |
|---|---|
| `RESERVATION_PREFIX` | `edaaiu5k` |
| `RESERVATION_VLAN` | `p1356` |
| `RHEL_HOST` | `pvm01-edaaiu5k.p1356.pok-systems.techzone.ibm.com` (IP: `129.40.97.178`) |
| `IBMI_HOST` | `pvm02-edaaiu5k.p1356.pok-systems.techzone.ibm.com` (IP: `129.40.97.182`) |
| `SSH_USER` | `UH6OWE8` |
| `SSH_KEY` | `C:\Users\029878866\Downloads\pvm-edaaiu5k-key.pem` ✅ saved |
| `IBMI_PASSWORD` | `a.Eh3A*03XuYEoq` |
| `IBMI_RDB` | `PVM02XED` (confirmed via DSPRDBDIRE) |

### watsonx.data Dev Image credentials
| Field | Value |
|---|---|
| `WXD_HOST` | `eu-de.services.cloud.techzone.ibm.com` |
| `WXD_SSH_PORT` | `39957` |
| `WXD_PRESTO_PORT` | `27799` |
| `WXD_SSH_USER` | `watsonx` / `WXD_SSH_PASS` = `watsonx.data` |
| `WXD_API_USER` | `ibmlhadmin` / `WXD_API_PASS` = `password` |

### IBM Satellite credentials
| Field | Value |
|---|---|
| `SATELLITE_IAM_APIKEY` | `Pauy15VZw_g3_vv5YHxFpIVI2QIgY5vXZP2sRtB2YDn3` |
| `SATELLITE_CONNECTOR_ID` | **Still needed** — check IBM Cloud console → Satellite → Connectors → `wxd-power-connector` |
| `SATELLITE_REGION` | `eu-gb` |

> `setup/reservation.py` is already populated with all of the above. `SATELLITE_CONNECTOR_ID` is the only remaining blank.

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

## What Was Done This Session (Session 19 — Deployment)

- DRDA password set: `CPC2205: User profile UH6OWE8 changed.` ✅
- `IBMI_RDB` confirmed: `PVM02XED` ✅
- `reservation.py` fully populated (all except `SATELLITE_CONNECTOR_ID`) ✅
- SSH key saved to `C:\Users\029878866\Downloads\pvm-edaaiu5k-key.pem` ✅
- Recipe fixes committed: `d7f3a96` (requirements.txt, .gitattributes, parse_ts fix, VLAN fix, Step 8b)
- **IBM i data load NOT YET COMPLETE** — blocked by two bugs found and fixed during this session:
  - DDL `CREATE SCHEMA` conflict: fixed in `_diagnose_ibmi.py` (strips the line before RUNSQLSTM)
  - `DLTLIB OLIST` succeeded (`CPC2194`) and `CRTLIB OLIST` succeeded (`CPC2102`) — library is clean
  - Final script `_diagnose_ibmi.py` runs DDL + full data load in one pass — was mid-run when context limit hit
- `setup/_diagnose_ibmi.py` is the **complete Phase 1 reset + load script** — run it first in the new session

---

## What Was Done This Session (Session 18 — Recipe Fixes)

- **Fix: Satellite ACL gap** — Step 8b added to RUNBOOK.md: new users must authorise their IAM Service ID on `wxd-power-connector` before starting the agent. `_start_satellite_agent.py` now resolves and prints the Service ID automatically.
- **Fix: Satellite API outage guidance** — Added guidance to Step 8 for HTTP 503 / LG0009 errors (IBM Cloud Satellite Link API outage not reflected on status page).
- **Fix: Timestamp format bug** — `parse_ts()` in `6-load-ibmi-olist.py` now outputs `YYYY-MM-DD-HH.MM.SS` (IBM i CPYFRMIMPF format) not `YYYY-MM-DD HH:MM:SS` (SQL format). This fixes CPF2817 field errors on ORDERS and ORDERITEMS.
- **Fix: Hard-coded VLAN** — `reservation.py.template` previously hard-coded `.p1223.` in the FQDN. Replaced with `RESERVATION_VLAN` variable (separate from `RESERVATION_PREFIX`). RUNBOOK prerequisites table updated. This was the issue Andrew observed with the `p1226` reference.
- **Fix: Missing requirements.txt** — Added `setup/requirements.txt` listing `paramiko`, `pandas`, `psycopg2-binary`, `kaggle`, `requests`, `ibm-cloud-sdk-core`.
- **Fix: CRLF line endings** — Added `.gitattributes` enforcing `eol=lf` for `*.del`, `*.sql`, `*.sh`, and `*.py` files. The existing `.del` files in `data/olist_transformed/` should be recommitted after this to strip the Windows CRLF endings from git history.

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
