# 🔖 Checkpoint — watsonx.data on IBM Power Demo

## Current Status
**Session 6 (2026-09-17) — Fresh reservations confirmed via TechZone API, starting from clean slate:**

All three new reservations are Ready (confirmed via TechZone API):

| Reservation | Request ID | Key | Expires |
|---|---|---|---|
| On-prem IBM i + RHEL | `6aaabd3afd09876e26e6a6ad` | `jkf6fl2k` | 2026-09-21T07:30Z |
| IBM Cloud Satellite | `6aaabe3f304e6b230f866ad3` | -- | 2026-09-21T07:05Z |
| watsonx.data SaaS | `6aabd7dfe00bd16e25b73a52` | `tqj6kn2k` | 2026-09-21T12:20Z |

**Key facts from the API pull:**
- On-prem: RHEL `pvm01-jkf6fl2k` at `129.40.125.69`, IBM i `pvm02-jkf6fl2k` at `129.40.125.73`, user `U8GO7IL`, pass `0@0PJp+*eB3j)Vq`. SSH key `C:\Users\029878866\Downloads\jkf6fl2k_key.pem`. **Fresh VM — all data loads must be re-run from scratch.**
- watsonx.data SaaS: service API key `dBtUhP7tpCUKn4NjFYEAo4-qj2HL58NBArXn5D4jBYj9`, student App ID `student_tqj6kn2k_6aabd7e37abf28461499b835_1@techzone.ibm.com` / `dhiuevfoz0scgpw`. **Wizard NOT yet run — Instance GUID and CRN are unknown until wizard completes.**
- Satellite: TechZone detail API returns 404 for Satellite request ID (self-referencing env ID quirk). Connector must be verified via `ibmcloud sat connector ls` in ITZ-V2. Previous connector `wxd-power-connector` (ID `U2F0ZWxsaXRlQ29ubmVjdG9yOiJkYTdoc29tbDFxc2Zhb2FhbGhqZyI`) may be reused.

**Immediate next steps (pick up here):**
1. **Run watsonx.data wizard** — open incognito -> `https://cloud.ibm.com/authorize/itzwatsonx` -> log in as student App ID `student_tqj6kn2k_6aabd7e37abf28461499b835_1@techzone.ibm.com` / `dhiuevfoz0scgpw`. Accept `itz-watsonx` invite via notification bell first. Catalog name: **`wxd_tqj6kn2k`**. Engine: Presto Starter. Accept auto-discovered COS bucket.
2. **Retrieve Instance GUID + CRN** — from IBM Cloud Resource List once wizard completes (`ibmcloud resource service-instance itz-110000sg2k-tqj6kn2k --output json`). Record in [`checkpoint-environments.md`](checkpoint-environments.md).
3. **Verify Satellite connector** — log into ITZ-V2 (`2112072 - ITZ-V2`), run `ibmcloud sat connector ls`. Confirm `wxd-power-connector` present. Update `ibmi-db2` endpoint to `129.40.125.73:8471`. If new connector, run `setup/bootstrap_sat_endpoints.py`.
4. **Start Satellite agent on RHEL** — run `setup/start_satellite_agent.sh` on RHEL. Confirm `WSR04 Connected` + `CTB27 Tunnel connected`.
5. **Load PostgreSQL data** — `python3 setup/8-load-edb-olist.py` (SSH-driven from laptop).
6. **Load IBM i data** — `python3 setup/6-load-ibmi-olist.py`, then `setup/run_ibmi_steps.sh`.
7. **Get Presto hostname** — once engine RUNNING, run `python3 /tmp/get_presto_hostname.py` from RHEL via `localhost:29999` tunnel. Update `wxd-presto` endpoint destination.
8. **Register federation connectors** — `pg_olist` and `ibmi_olist` via watsonx.data GUI (proven path).
9. **Deploy Demo UI** — scp `demo-ui/` to RHEL, `npm install`, `npm run build`, set `.env.local`, run `restart.sh`.
10. **End-to-end smoke test** — `SHOW CATALOGS`, cross-source query, alert flow in UI.
- Full runbook: [`setup/5-add-federation-connectors.md`](setup/5-add-federation-connectors.md)

**Previously confirmed (sessions 1-5):**
- Bidirectional Satellite Connector architecture: cloud endpoints (on-prem->IBM Cloud) + location endpoints (IBM Cloud->on-prem).
- Cloudflare blocks calls to `*.lakehouse.ibmappdomain.cloud` and `eu-gb.lakehouse.cloud.ibm.com` from outside IBM Cloud — only Satellite cloud endpoint routes bypass it.
- CHAR->VARCHAR compat views required on both IBM i and PostgreSQL for Prestissimo C++ connector.
- watsonx.data wizard is the only reliable setup path (REST API schema changed Sep 2026).
- Federation connectors: GUI is proven path; use `connection.name` field (not `connection.database`) for API calls.
- IBM i RDB name for `jkf6fl2k` reservation: `PVM02XJK` (confirmed via WRKACTJOB).

---

**Session 3 notes (superseded by session 4 above):**
**Live query unblocked — one ACL step remaining (2026-09-14 session 3):**
- **Root cause of Presto C++ CHAR issue confirmed:** Prestissimo (C++) does not support `CHAR(n)` column types from any connector — the failure occurs at scan time before any SQL-level CAST can help. Fix is views in the source databases exposing every CHAR column as VARCHAR.
- **PostgreSQL compat views created:** `setup/11-pg-compat-views.sql` deployed to RHEL. `olist.v_suppliers`, `v_purchase_orders`, `v_warehouses`, `v_tier2_suppliers` all created. `detect-signals.ts` queries now target these views.
- **Presto auth fixed:** `wxd-query-internal.ts` now exchanges the API key for a Bearer IAM token via `POST https://iam.cloud.ibm.com/identity/token` before each query. The old Basic auth with raw API key was rejected as "malformed token".
- **Correct Presto host discovered:** `70733fc8-2b02-4683-ba01-628f66e07284.d4mn75il0dt1ob8mmlug.lakehouse.ibmappdomain.cloud:31618` — per-engine UUID hostname, not the API host. Confirmed reachable from RHEL (HTTP 401 = auth required, not network blocked). `.env.local` updated with correct host:port.
- **Remaining blocker:** `Access denied: USE catalog pg_olist — permission check failed`. The service ID `itz-110000sg2k-limql82k` does not have USE permission on `pg_olist` or `ibmi_olist`. These catalogs were created by the student App ID. Fix: in watsonx.data console → Access Control → Catalogs → grant DataAccess to `itz-110000sg2k-limql82k` on both `pg_olist` and `ibmi_olist`. Once done, live federated data will flow — the 10-second Presto query is already running successfully, just being blocked at the ACL check.
- **Start script fixed:** `setsid sh -c "PORT=3000 npm start > ~/demo-ui.log 2>&1" </dev/null &` wrapped in `/tmp/start_ui.sh` — returns immediately with no "executing" hang. The `</dev/null` closes stdin so the SSH session detaches cleanly.
- **TechZone MCP confirmed as API key source:** `techzone-get-request(6aa43072e182c81b8c7ff43e).output[service_api_key].value` returns the key directly. Deploy skill should always fetch via MCP rather than ask the user to paste it.

**IBM i compatibility views + UI live federation (2026-09-14 session 2):**
- **IBM i compatibility views created:** `setup/10-ibmi-compat-views.sql` and `setup/10-ibmi-compat-views-drop.sql` written. All four views (`OLIST.V_CUSTOMERS`, `OLIST.V_PRODUCTS`, `OLIST.V_ORDERS`, `OLIST.V_ORDERITEMS`) created on the active IBM i (`pvm02-e991q02k.p1276.pok-systems.techzone.ibm.com`) via `RUNSQLSTM`. Confirmed by `SQL7951` (severity 0) messages and presence of `V_CUS00001.FILE`, `V_PRODUCTS.FILE`, `V_ORDERS.FILE`, `V_ORD00001.FILE` in `/QSYS.LIB/OLIST.LIB/`. Root cause: watsonx.data Db2 for i connector rejects `CHAR(32)` source columns with `Unknown type char(32)`; all CHAR(N) key columns are now exposed as `VARCHAR(N)` through the views. `WHENEVER SQLERROR CONTINUE/STOP` is not supported by `RUNSQLSTM COMMIT(*NONE)` — use separate drop/create files to handle idempotent re-runs.
- **Watsonx.data Presto query route added:** `demo-ui/src/pages/api/wxd-query.ts` (HTTP API route) and `demo-ui/src/pages/api/wxd-query-internal.ts` (shared Presto HTTP polling loop) written. No external npm dependencies — uses Node.js built-in `https`/`http`. Credentials via env vars `WXD_PRESTO_HOST`, `WXD_APIKEY`, `WXD_INSTANCE_CRN`.
- **`detect-signals.ts` updated:** now calls `wxdQuery()` to run live federated SQL against `pg_olist` for cyber/wildfire exposure data. Gracefully falls back to hardcoded stub values when env vars are not set or the query fails. Alert `source` field is `'live'` when Presto host is configured, `'stub'` otherwise. Alert reasoning labels updated to reference `pg_olist` and `ibmi_olist` catalogs.
- **`demo-ui/.env.local.template` created:** template with correct `WXD_PRESTO_HOST=eu-gb.lakehouse.cloud.ibm.com` and `WXD_INSTANCE_CRN` pre-filled. Fill in `WXD_APIKEY` from TechZone reservation page.
- **`demo-ui/.env.local` deployed to RHEL:** API key is placeholder; CRN and host are set. Rebuild and restart done — UI returns HTTP 200, end-to-end alert flow validated via Node.js test script.
- **`restart.sh` updated:** uses `setsid` instead of `nohup ... & disown` to detach Next.js without leaving the SSH tool in a hanging "executing" state.
- **Next step:** fill in the real `WXD_APIKEY` in `/home/U5VZFHW/watsonx-data-power-demo/demo-ui/.env.local` on RHEL, restart the UI (`setsid npm start >> ~/demo-ui.log 2>&1 &` from the demo-ui dir), then validate the IBM i compatibility views in the watsonx.data Query Workspace with: `SELECT "customer id", "state" FROM ibmi_olist.OLIST.V_CUSTOMERS FETCH FIRST 5 ROWS ONLY`.

**watsonx.data SaaS — new location validation (2026-09-14):**
- **New reservation:** `6aa43072e182c81b8c7ff43e` (container) → environment `6aa43079afcaade13de047bd` (`watsonx.data SaaS`) — ✅ Ready.
- **TechZone placement:** Europe / `eu-de` / Frankfurt `fra04`.
- **watsonx.data service location:** London / `eu-gb` — the reservation created the service in London despite the TechZone placement being Frankfurt. The IBM Cloud Resource List confirms `itz-wxdata-110000sg2k-limql82k` in London. The working GUI is explicitly on the `eu-gb` route; the earlier `eu-de` browser route was the wrong service endpoint and remained at the loading/CRN prompt.
- **Window:** 2026-09-14 04:55 UTC → 2026-09-18 04:55 UTC.
- **Environment key:** `limql82k`; IBM Cloud login URL remains `https://cloud.ibm.com/authorize/itzwatsonx`.
- **Important correction:** the environment ID supplied in the request (`6aa43079afcaade13de047bd`) is not the parent reservation ID; TechZone APIs require the parent request ID `6aa43072e182c81b8c7ff43e` for request details.
- **Instance CRN:** `crn:v1:bluemix:public:lakehouse:eu-gb:a/9f8f95eee4714473a87fa319d964063c:e4ec7696-6363-4ad9-a21f-41eba7b7a663::`.
- **Wizard result:** Apache Iceberg catalog setup completed successfully with catalog name `wxd_limql82k`; no catalog-name collision occurred.
- **Federation test (2026-09-14):** New instance API authentication succeeded and engine `prismo600` was found RUNNING. Direct API PostgreSQL registration returned HTTP 400 `Connection failed - Invalid hostname or credentials` using Satellite endpoint `c-01.private.eu-gb.link.satellite.cloud.ibm.com:33156`.
- **GUI/API payload breakthrough (2026-09-14):** The GUI Test connection payload uses `connection.name` for the database name, not `connection.database`. Replaying the captured shape against the existing `POST /lakehouse/api/v3/database_registrations` endpoint succeeded with HTTP 201. The essential payload shape is `type: postgresql` plus `connection: {name: "olist", hostname, port, username, password, ssl: false}`. A temporary `pg_olist_api_capture` registration was created successfully and immediately deleted (HTTP 204) after validation. The direct API failure was therefore caused by the missing `connection.name` field; GUI and API use the same registration path.
- **Targeted schema tests:** Adding `database: "olist"` is rejected by the current API as an unknown field. Adding `validate_certificate: true` is also rejected as an unknown field. Retrying with the supported current payload and `ssl: true` still returns the same HTTP 400 connection error. No test connector was created.
- **IBM i API payload test (2026-09-14):** Retried `ibmi_olist` using the corrected GUI-derived `connection.name` field and the same Satellite endpoint `:33180`. The API returned Cloudflare HTTP 520 twice, including after the documented 60-second retry interval. No connector was created. This is a different service-side failure from the previous HTTP 400 and does not yet disprove the corrected payload; the next test should be the IBM i GUI workflow.
- **API association test (2026-09-14):** Direct API listing returns zero database registrations even though the GUI shows `ibmi_olist` and `pg_olist`; attempting the unscoped `POST /prestissimo_engines/prismo600/catalogs` with `ibmi_olist` returned HTTP 500 `failed to associate catalogs`.
- **GUI association payload (2026-09-14):** The successful GUI request is `POST /lakehouse/api/v3/e4ec7696-6363-4ad9-a21f-41eba7b7a663/prestissimo_engines/prismo600/catalogs`, HTTP 201, body `{"catalog_names":["ibmi_olist"]}`. The missing instance-GUID path segment caused the earlier API association failure. The automation script now uses the instance-scoped association URL.
- **IBM i GUI breakthrough (2026-09-14):** The GUI connection test succeeded using the IBM i system relational database name `PVM02XE9` rather than `*LOCAL`, with Satellite endpoint `c-01.private.eu-gb.link.satellite.cloud.ibm.com:33180`, user `U5VZFHW`, password from the TechZone reservation, and SSL disabled. `PVM02XE9` was confirmed from the IBM i relational database directory (`DSPRDBDIRE`).
- **IBM i connector test (2026-09-14):** Registration of `ibmi_olist` previously returned HTTP 400 `Connection failed - Invalid hostname or credentials` against Satellite endpoint `c-01.private.eu-gb.link.satellite.cloud.ibm.com:33180` when using `*LOCAL`. From the proven `sftp-server`, TCP connectivity to port 33180 succeeds. The GUI test now succeeds with `PVM02XE9`, so the earlier failure was caused by using the special `*LOCAL` value rather than the system’s actual RDB name.
- **SFTP diagnostic (2026-09-14):** Connected to the existing personal-account IBM Cloud VSI `ubuntu@161.156.199.126` (`sftp-server`) using the local key `~/.ssh/sftp_admin`. From that host, Satellite PostgreSQL connectivity succeeded: `psql` through `c-01.private.eu-gb.link.satellite.cloud.ibm.com:33156` returned `COUNT(*) = 50` from `olist.tier2_suppliers` and listed all four `COMPROMISED` suppliers. Satellite routing, endpoint, PostgreSQL service, database, username, and password are therefore confirmed valid from an IBM Cloud source.
- **Root cause narrowed:** Satellite agent is healthy and its logs show recent successful traffic from IBM Cloud source `10.16.62.208` to PostgreSQL (`BytesToCloud 277`, `BytesFromCloud 262`). The local Windows machine and the on-prem RHEL VM cannot directly open the private Satellite client port, which is expected; the failed registration is watsonx.data connector validation, not proof that the Satellite tunnel is down.
- **Next validation:** verify and record the new instance CRN, GUID, COS bucket, catalog, and engine details. Do not assume the previous instance's CRN, catalog, COS bucket, engine, or student credentials apply.

**watsonx.data Engine Provisioning (2026-09-11/12):**
- **watsonx.data SaaS (`6aa13d26ab35f2ba12942117`):** ✅ Ready. Wizard completed successfully under student identity. Engine `prismo476` is now **RUNNING**, with catalog `wxd_7jtdt22k`. ⚠️ Expires 2026-09-13 — extend before next session.
- **On-prem combined reservation expires 2026-09-12** — also extend before next session.

**Active Lab Environments & Satellite Link Verified (2026-09-08):**
- **On-Prem Power Lab (`6aa029199f3cc7ab3a08b99c` - POK):**
  - Combined reservation with RHEL 9.8 (`129.40.94.91`) and IBM i 7.6 (`129.40.94.90`) on shared subnet (`129.40.94.88/29`, VLAN 1276) — 0.36ms latency between them.
  - IBM i loaded with full OLIST dataset (`99k` orders, `112k` items) + `SECTOR` classification & index (`setup/9-ibmi-add-sector.sql`).
  - RHEL VM loaded with PostgreSQL 16 (50 tier-2 suppliers, 3,095 suppliers, 23 warehouses, 112k POs) + Demo UI running on port 3000 (`http://129.40.94.91:3000`).
- **TechZone IBM Cloud Satellite (`6aa03ab5ecf40da0d25de733` in DTEV2 / `ead8711ba2cc4d08a16fd37427f4f01a`):**
  - Connector: `wxd-power-connector` (ID: `U2F0ZWxsaXRlQ29ubmVjdG9yOiJkYTdoc29tbDFxc2Zhb2FhbGhqZyI`). Account/user: `2112072-ITZ-V2`.
  - Active agent: `pvm01-e991q02k.56` on the combined-reservation RHEL VM.
  - Connector Agent running as root in podman on on-prem RHEL VM (`wxd-connector-agent`).
  - Agent active, connected, and tunnel established via TLS 1.3 to `wss://c-01-ws.eu-gb.link.satellite.cloud.ibm.com/ws`.
  - **Satellite Link Endpoints Created & Active:**
    - `pg-olist`: `c-01.private.eu-gb.link.satellite.cloud.ibm.com:33156` → `127.0.0.1:5432` (PostgreSQL on RHEL)
    - `ibmi-db2`: `c-01.private.eu-gb.link.satellite.cloud.ibm.com:33180` → `129.40.94.90:8471` (Db2 for i)
- **TechZone Collection URLs:**
  - **Overall demo collection:** https://techzone.ibm.com/collection/show-business-value-of-watsonxdata-with-ibm-power
  - **On-prem combined (IBM i + RHEL):** https://techzone.ibm.com/collection/68b03b541dd77334b923bc2e
- **Next Steps for Next Session:**
  1. ✅ **New on-prem combined (IBM i + RHEL) reserved:** request `6aaabd3afd09876e26e6a6ad`, environment key `jkf6fl2k`. Status: **Scheduled**. Provisions 2026-09-17 07:00 UTC → expires 2026-09-21 07:00 UTC. RHEL 9.8 on Power10 (4 vCPU, 32 GB, 500 GB extra disk) + IBM i V7R6TR1 on Power11. Credentials in reservation output once Ready.
  2. Run `setup/5-add-federation-connectors.py` from the RHEL VM using the watsonx.data service API key and verified Satellite client endpoints. Endpoint ownership and Satellite API access are confirmed; registration still returns `Connection failed - Invalid hostname or credentials`, so the remaining issue is watsonx.data-specific reachability or connector credential compatibility.
  2a. ✅ **Cross-account Satellite tunnel proven:** existing personal-account VPC VSI `sftp-server` (`161.156.199.126`, account `7c7ab84cf29f2e005fd71e1635548059`) resolved the Satellite hostname, opened TCP 33156/33180, and queried PostgreSQL through `pg-olist` successfully (`3095` suppliers, `50` tier-2 suppliers). IBM i endpoint TCP 33180 is also reachable.
  3. Use [`setup/5-add-federation-connectors.md`](setup/5-add-federation-connectors.md) as the fresh-TechZone rebuild runbook.
  4. Test end-to-end federated query via Presto (`SHOW CATALOGS`, then cross-source query).
  5. Wire retail POS generator → COS Iceberg bucket.
  6. Run full demo arc smoke test on Demo UI (`http://129.40.94.91:3000`).

**Session notes (2026-08-27 — Satellite Connector breakthrough + networking investigation):**
- **Satellite Connector `wxd-power-demo-2` created** in personal IBM Cloud account (`eu-gb` region). ID: `U2F0ZWxsaXRlQ29ubmVjdG9yOiJkYTg0anE3bDFybDNqa2s5bG9xMCI`
- **API key `satellite-connector-key`** created in personal IBM Cloud account: `Evqp2cEMRhsM-3Q_1YhjqWYx7TybJvS97yDASQSFMr60`
- **Satellite agent running on PowerVS RHEL** (`13.120.79.110`) — must run as **root** via `sudo podman` (rootless podman gets killed immediately, exit 137, due to IP firewall/cgroup restrictions for non-root). Image loaded into root's podman store via `podman save | sudo podman load`. Agent connects successfully: `WSR04 Connected`, `CTB27 Tunnel connected`, TLS 1.3. UI shows **Active agent** ✅
- **Run command (must be root):**
  ```
  sudo podman run -d --name wxd-connector-agent --restart always --network host \
    --env SATELLITE_CONNECTOR_ID=<connector-id-from-config.env> \
    --env SATELLITE_CONNECTOR_IAM_APIKEY=<sat-apikey-from-config.env> \
    icr.io/ibm/satellite-connector/satellite-connector-agent:latest
  ```
- **Old RAG demo VM** (`67.18.70.83`, `hybrid-ai.power-iaas.cloud.ibm.com`) found and shut down — 499 days uptime, RHEL 9.4 ppc64le, no Satellite Connector on it. AIX instance in same workspace also already shut down. Delete both from IBM Cloud console to stop storage charges.
- **Networking investigation — definitive results:**
  - `129.40.x.x` on-prem TechZone addresses are **IBM intranet only** — reachable via IBM VPN from laptop but NOT routable over the public internet. On-prem RHEL → on-prem IBM i times out even on port 22.
  - PowerVS RHEL (`192.168.241.78/29`) and PowerVS IBM i (`192.168.241.213`) are on **different `/29` subnets** within the same workspace — no L3 route between them, vSRX blocks cross-subnet traffic.
  - PowerVS vSRX **open ports** (fixed, not configurable): `22, 443, 992, 2005, 2007, 2010, 2012, 9470, 9475, 9476, 6443, ICMP`. Port `8471` (Db2 for i DDM) and `5432` (PostgreSQL) are **not** on the list. Port 8471 is hardcoded in IBM i DDM service — cannot be remapped.
  - PowerVS RHEL has outbound internet on port 443 ✅ — Satellite agent connects fine.
  - PowerVS `env3` interface on RHEL has no IPv4 address — unconfigured second NIC.
- **Possible path forward (to investigate after long weekend):** Add a **private network** in the PowerVS workspace and attach both VMs to it — this is self-service in IBM Cloud PowerVS console and would give both VMs a shared subnet bypassing the vSRX entirely. Port 8471 would then be reachable VM-to-VM on the private network.

**Session notes (2026-09-14 — new Frankfurt reservation check):**
- Both the previous and current watsonx.data TechZone requests can show **Ready** while the IBM Cloud Resource List shows one active watsonx.data service. Treat TechZone reservations as access/provisioning records, not as a one-to-one inventory of IBM Cloud resources.
- The current reservation has fresh credentials and a distinct service CRN (`e4ec7696-6363-4ad9-a21f-41eba7b7a663`) compared with the previous checkpointed instance GUID (`3d6fbad3-6573-42d0-ac2f-3487b889773f`). Do not infer that both reservations use the same watsonx.data instance solely from the Resource List.
- Successful wizard completion on the current reservation confirms the current setup path works; it does not by itself prove the underlying IBM Cloud resource is shared with the previous reservation.
- Resource List confirms three active database resources: `Db2-Governance` in Dallas, `Db2-Governance-fra` in Frankfurt, and `itz-wxdata-110000sg2k-limql82k` in London.
- The reservation is placed in Frankfurt, but the watsonx.data service is provisioned in London (`eu-gb`). This is a service-placement mismatch in the TechZone bundle, not a second Frankfurt watsonx.data instance.
- The supplied CRN `crn:v1:bluemix:public:lakehouse:eu-gb:a/9f8f95eee4714473a87fa319d964063c:e4ec7696-6363-4ad9-a21f-41eba7b7a663::` matches the visible watsonx.data resource and should be used for the federation test.
- Federation test against the new instance reproduced the HTTP 400 `Connection failed - Invalid hostname or credentials` error for PostgreSQL; IAM authentication and engine discovery both succeeded.
- Targeted retries confirmed the current API schema rejects explicit `database` and `validate_certificate` fields; `ssl: true` is accepted syntactically but does not change the connection failure. This rules out those payload additions as the immediate fix.
- IBM i registration was tested separately and produced the identical error. Satellite TCP reachability to `ibmi-db2:33180` from the SFTP server is confirmed, so the issue is not PostgreSQL-specific.
- The working GUI screenshot confirms the correct service route is `eu-gb`, instance `itz-wxdata-110000sg2k-limql82k`, with two engines visible and the catalog `wxd_limql82k` associated to the Starter Presto engine. This gives us the correct GUI context for comparing the Add component database workflow with the API.
- GUI inspection (2026-09-14): PostgreSQL Add component explicitly asks for **Database name**, Hostname, Port, Username, Password, and an optional SSL toggle. `watsonx.data instance` is selected; `Platform assets catalog` is disabled with “unavailable or not configured”, which is unrelated to this test. The GUI therefore provides a useful comparison path and suggests `database: olist` is semantically required even though the current direct API schema rejects that field.
- GUI Test connection and Create both succeeded with the exact Satellite/PostgreSQL values; `pg_olist` is now registered through the Infrastructure Manager. This is the decisive result: connectivity, credentials, endpoint, database name, and watsonx.data SaaS reachability are all valid. The Query Workspace initially reported `Catalog pg_olist does not exist`, while only `wxd_limql82k` appeared in the associated-catalog list. The Infrastructure Manager Catalogs view confirmed `pg_olist` existed with `Database associated = pg_olist` but `Engines associated = 0`; associating it with `Starter` fixed the issue.
- **GUI/API payload breakthrough (2026-09-14):** The GUI Test connection payload uses `connection.name` for the database name, not `connection.database`. Replaying the captured shape against the existing `POST /lakehouse/api/v3/database_registrations` endpoint succeeded with HTTP 201. The essential payload shape is `type: postgresql` plus `connection: {name: "olist", hostname, port, username, password, ssl: false}`. A temporary `pg_olist_api_capture` registration was created successfully and immediately deleted (HTTP 204) after validation. The direct API failure was therefore caused by the missing `connection.name` field; GUI and API use the same registration path.
- **End-to-end PostgreSQL validation (2026-09-14):** `SHOW CATALOGS`, `SHOW SCHEMAS IN pg_olist`, and `SELECT COUNT(*) FROM pg_olist.olist.tier2_suppliers` all ran successfully in Query Workspace after the engine association. Queries were slow immediately after the engine restart, but completed successfully.
- **IBM i GUI registration state (2026-09-14):** The new `ibmi_olist` data source/catalog is registered and visually present, but currently has `Engines associated = 0`, matching the earlier PostgreSQL intermediate state. Associate it with the running `Starter` engine before querying it.
- **IBM i query validation (2026-09-14):** After recovering the watsonx.data console session, `SHOW SCHEMAS IN ibmi_olist;` completed successfully in approximately 12 seconds. The catalog, engine association, Satellite path, and IBM i metadata access are working; table-scan/query compatibility remains to be tested.
- **IBM i metadata validation (2026-09-14):** `DESCRIBE ibmi_olist.OLIST.ORDERS` succeeded, but took approximately 78 seconds. watsonx.data exposes the descriptive lowercase column names (`order id`, `customer id`, etc.), not the IBM i short names (`ORDERID`, `CUSTID`). The connector exposes the expected `ORDERS` table and system metadata tables. Federated queries must quote names containing spaces, for example `COUNT("order id")`.
- **IBM i table-scan validation (2026-09-14):** `FETCH FIRST 1 ROWS ONLY` syntax was accepted, but querying/casting the `CHAR(32)` `order id` column still fails with `Unknown type char(32)`. The failure occurs during connector type handling before the projection cast can help; test a native `VARCHAR` column next, then use an IBM i compatibility view if required.
- **IBM i type compatibility result (2026-09-14):** Selecting the native `VARCHAR(20)` column `order status` succeeded in approximately 20 seconds. The watsonx.data Db2 for i connector can read native VARCHAR columns; the failure is isolated to the source `CHAR(32)` columns such as `order id` and `customer id`.
- Satellite endpoint logs confirm IBM Cloud traffic reached `pg-olist` and PostgreSQL responded, so the remaining issue is connector validation details such as endpoint ACL/source authorization, database credentials, or watsonx.data connector compatibility.
- Wizard completed successfully using the reservation-unique Apache Iceberg catalog name `wxd_limql82k`; no errors or namespace collision.
- TechZone token authenticated successfully, but the supplied environment ID is a child environment ID; request details are keyed by parent reservation `6aa43072e182c81b8c7ff43e`.
- New reservation is **Ready** in `eu-de` / `fra04`, scheduled for four days. Its reservation output supplies a fresh environment key and fresh student App ID credentials.
- The new reservation's platform metadata still lists `eu-gb` / `lon02` as an enabled alternative, but the actual placement is `eu-de` / `fra04`; use the actual placement for this test.
- No watsonx.data service credentials or instance CRN were written to the checkpoint yet; retrieve them from the new reservation output/console and do not reuse the previous London values.

**Session notes (2026-09-11 — watsonx.data wizard + API archaeology):**
- **New reservation `6aa13d26ab35f2ba12942117`** provisioned Ready in `eu-gb`/`lon02`.
- **Invitation:** the 30-day invite link from an earlier reservation still works — no need to wait for a new one from the new reservation.
- **watsonx.data API schema changed** between Aug and Sep 2026. `storage_registrations` POST no longer accepts `associated_catalogs` in body. `POST /catalogs` endpoint is GET-only. Engine `size_config: starter` requires specific node_type values unknown to API consumers. **The wizard is the only reliable setup path.**
- **Root cause of repeated 400s:** any prior storage registration (whether from a failed wizard run or an API call) blocks the wizard with `duplicate key value violates unique constraint "bucket_pkey"`. Fix: `DELETE /storage_registrations/{bucket_id}` (204), then re-run wizard immediately.
- **Catalog name collision:** `iceberg_data` is permanently taken in the shared `itz-watsonx` MDS. Always use a reservation-unique name like `wxd_<env-key-suffix>`. This reservation: `wxd_7jtdt22k`.
- **Student credentials essential:** IBM ID fails with MDS permission errors. Use student App ID credentials (`student_7jtdt22k_1@techzone.ibm.com` / `lkx4v6rziecfubi`) for all watsonx.data console work.
- **TechZone Service API Key** (`4TluHu2xZhUKr8t4GjK6PdDKtsmqxYtfccP0EbESkE-Y`) is pre-provisioned in the reservation output — no need to create one manually.
- **Auth headers:** `/storage/cos/*` endpoints require two extra headers beyond the standard pair: `iamToken: <token>` and `LhInstanceId: <instance_guid>`.
- **Engine:** `prismo476`, PROVISIONING at end of session. Catalog `wxd_7jtdt22k` associated. COS bucket `watsonx-data-3d6fbad3-6573-42d0-ac2f-3487b889773f` registered with HMAC keys.
- **Definitive procedure** written to `checkpoint-environments.md` under "Definitive watsonx.data Setup Procedure".
- **`setup/4-provision-via-rest-api.py` is now obsolete** for initial setup — needs rewrite to match new API schema, or retire in favour of wizard + federation script only.

**Session notes (2026-09-XX — Recipe alignment to CE Marketplace pattern):**
- **Recipe aligned to reference pattern** (Carbon-GenAI-Demos and PowerSC-Vault-Demo reviewed as reference).
- **Skills flattened**: `.bob/skills/deploy-watsonx-data-power/SKILL.md` → `.bob/skills/deploy-watsonx-data-power.md` (flat file, matching reference pattern). Both files exist; the flat file is the canonical one going forward.
- **New skill: `watsonx-data-power-story-builder`** — guides seller through story phase: DB path selection, scenario framing, talking points, punchline moments, anticipated objections, tester prompt. Written to `.bob/skills/watsonx-data-power-story-builder.md`.
- **New mode: `watsonx-data-power-demo`** — seller persona YAML in `.bob/modes/watsonx-data-power-demo.yaml`. Knows both paths, story-builder + deploy skill workflows, TechZone manual reservation requirement, EDB/PG16 deployment distinction, SSH patterns, demo arc, punchline moments.
- **New file: `GETTING-STARTED.md`** — one-page quick-start matching Carbon-GenAI-Demos reference pattern. Three-step guide (Story → Reserve → Deploy), 6-step arc table, punchline column callout, links to COLLECTION.md, RECIPE.md, RECIPE-JOURNEY.md.
- **RECIPE.md updated** — added `GETTING-STARTED.md` link, `watsonx-data-power-story-builder` skill, `modes` entry, Path B renamed to `aix_plus_edb`, warning note about manual reservation. Added `edb` tag.
- **COLLECTION.md updated** — Path B renamed to "AIX + EDB (Oracle replacement)"; full EDB positioning explanation added (Oracle-compatible, migration story, deployment uses PG16 with EDB positioning accurate); Path B infrastructure table updated; Known Issues row updated.
- **Path B story clarified**: "EDB as Oracle replacement" is the correct framing — Oracle-compatible syntax, IBM Power-native, no Oracle licensing. Community PostgreSQL 16 is the deployment vehicle; EDB AS binary is available via EDB portal (token-gated, ppc64le support via subscription). Story is accurate regardless of which binary.
- **Tester prompt added to story-builder skill** — standard prompt any team member can use to start the recipe from scratch.
- **Agreed next phase**: reserve clean TechZone environments (fresh watsonx.data SaaS + IBM i + RHEL/Power10), run full recipe from scratch to validate all steps work end-to-end, then publish to `https://github.com/ibm-power-demos-with-bob/watsonx-data-power-demo` and invite team tester.

**Session notes (2026-09-XX — Recipe packaging):**
- **`RECIPE.md` written** — CE Marketplace frontmatter (name, title, description, tags, skills, techzone config for all three reservation types, db_path_variants), quick-start guide.
- **`COLLECTION.md` written** — full one-stop instructions: two DB path variants (Path A IBM i+EDB / Path B AIX+EDB), story phase guide, infrastructure requirements table, 6-step how-to-run (story → reserve → deploy → demo), demo reset, customer customisation options, known issues, related demos.
- **`RECIPE-JOURNEY.md` written** — living journal covering why the demo was built, all key architecture decisions (DB path split, v1 TechZone constraint, EDB replacing Oracle, synthetic signal injection, tier-2 punchline column, map vs. satnav AI narrative, Next.js pin, file-based alert store), full session log from session 1 through this session, next steps, and the tester prompt.
- **`.bob/skills/deploy-watsonx-data-power/SKILL.md` written** — full step-by-step deploy skill covering: pre-flight connectivity checks, watsonx.data SaaS provisioning, IBM i DDL + data load (Path A), EDB install + load (both paths, including `--full-dataset` flag for Path B), federation connector config, POS generator wiring, UI deploy + verify, smoke test, reset, SSH patterns, and known failure modes.
- **Agreed next phase:** reserve clean TechZone environments (fresh watsonx.data SaaS + IBM i + RHEL/Power10), run full recipe from scratch to validate, then publish to `https://github.com/ibm-power-demos-with-bob/watsonx-data-power-demo` and invite a team tester.

**Session notes (2026-08-25 — live feeds, acronym expansions, /sources view):**
- **Connected genuine live feeds**: Ingests real public CISA Known Exploited Vulnerabilities catalog (`cisa.gov`) and live A9/AP-7 European freight corridor telemetry (`api.open-meteo.com`) via new [`live-feed-fetcher.ts`](demo-ui/src/pages/api/live-feed-fetcher.ts).
- **Expanded acronyms**: Replaced shorthand references with plain-English labels ("Cybersecurity Threat Intelligence · Known Exploited Vulnerabilities Feed" and "Route & Freight Corridor Telemetry").
- **Added `/sources` Federation Architecture transition page**: Dedicated view inserted between `/` (Static Report) and `/live?scenario=cyber` (Live Satnav), clearly detailing the three sources, what each holds, their respective blindspots, and how watsonx.data joins across them in real time.
- **Toned down AI framing**: Framed the core value as zero-ETL data federation speed and immediate operational visibility, with built-in Matrix Math Acceleration (MMA) on IBM Power positioned as hardware readiness for optional on-box AI scoring.
- **Deploy hygiene & restart script**: Added [`restart.sh`](demo-ui/restart.sh) to cleanly terminate orphan worker processes and prevent `EADDRINUSE` port collision.

**Session notes (2026-08-25 — signal detection split + source-story plan):**
- **Implemented a separate detection flow in the live demo**: injection no longer creates the alert directly. `POST /api/inject-signal` now writes a signal event into a shared signal store (`/tmp/wxd-demo-signals.json`) via new [`signal-store.ts`](demo-ui/src/pages/api/signal-store.ts). `POST /api/alerts` now runs a separate detector via new [`detect-signals.ts`](demo-ui/src/pages/api/detect-signals.ts), which checks business relevance and only then writes an alert into the existing alert store.
- **Business relevance logic is now explicit in the detector**: the cyber scenario is matched to tier-2 supplier context in EDB plus open-order exposure in IBM i; the wildfire scenario is matched to route/supplier context in EDB plus near-term order exposure in IBM i. This makes the story "button simulates the world; system detects the consequence" defendable.
- **Remote validation completed on the RHEL VM**: synced changed files, built successfully with `npm run build`, restarted on port 3000, and verified with `curl` returning `200`.
- **Important remote cleanup**: stray files existed on the VM under `demo-ui/src/pages/api/SignalControlPanel.tsx` and `demo-ui/src/pages/api/live.tsx`; removed them because they interfered with Next.js build/typecheck.
- **Agreed next story refinement**:
- Cyber scenario should be framed as a **synthetic event injected into an IBM X-Force Exchange-aligned monitored signal channel**. X-Force is the upstream cyber intelligence source; our detector decides business relevance using EDB + IBM i.
- Wildfire/logistics scenario should be framed as a **synthetic disruption injected into a route/travel-intelligence-aligned monitored signal channel**. Upstream source class: real route/travel disruption intelligence (aligned to the travel-planner work using Google Maps Directions API with National Rail-style fallback), not a literal "wildfire feed".
- **Next implementation/story task after current interruption**: update UI copy, source labels, and presenter wording so cyber explicitly references X-Force Exchange and wildfire explicitly references route/travel intelligence; keep synthetic injection for deterministic demos.

**Session notes (2026-08-25 — demo story flow + UI arc refactor):**
- **Demo flow is now a 5-step arc**: ① Static report (`/`) → ② Cyber live (`/live?scenario=cyber`) → ③ Cyber outcome (`/outcome?scenario=cyber`) → ④ Wildfire live (`/live?scenario=wildfire`) → ⑤ Wildfire outcome (`/outcome?scenario=wildfire`) → back to ①
- **`/live` page** now accepts `?scenario=cyber|wildfire` — shows only the relevant signal button, breadcrumb in header, "See the outcome →" button stays greyed until a signal has been fired
- **`/outcome` page** now accepts `?scenario=cyber|wildfire` — shows only the relevant timeline block; third Power pillar is scenario-specific: cyber → "Reduced Attack Surface" (IBM i object-based memory, PowerSC), wildfire → "Hybrid Cloud Continuity" (on-prem + IBM Cloud resilience); closing CTA routes to the next arc step
- **Alert store** moved from in-memory module-level array to **file-based** (`/tmp/wxd-demo-alerts.json`) — fixes cross-worker process isolation in Next.js production mode where `alertsStore` was not shared across workers, causing DELETE to have no effect
- **Alert clearing**: `DELETE /api/alerts` wipes the file; `GET /api/alerts?scenario=cyber|wildfire` filters by scenario; on mount the live page fires DELETE then polls sequentially (not in parallel) to avoid the race condition where poll repopulates before DELETE lands
- **PosStreamPanel**: added teal left-border signpost subtitle — "This is your business right now — not Friday's report. Sector tags show which product lines are exposed the moment a signal fires."
- **Alert cards**: both `CyberAlertCard` and `WildfireAlertCard` now have a "What this enables" section (green-tinted, 3 ✓ action bullets) bridging to the outcome page
- **`/outcome` timeline fix**: new-world green bar now fills from left edge → `actionAt` dot (not full track width); Scenario 2 uses `scaleOrigin={toMinutes('Mon 06:00')}` so both bars share Monday morning as the anchor — wildfire new-world green sliver is visibly short vs the 96h old-world red bar
- **`getServerSideProps`** added to `/live` and `/outcome` — forces SSR so `router.query` is populated on first render (previously static pages meant query params were undefined until client hydration, breaking the scenario param)
- **Kill pattern**: `kill -9 $(ss -tlnp | grep 3000 | grep -oP "pid=\K[0-9]+")` — kills whatever PID is on port 3000 regardless of process name (old `pkill -f "next start"` missed processes running as `MainThread`)
- **`outcome.tsx` timeline notes:**
- `outcome.tsx` timeline bars now use **proportional time-based positioning** (`toMinutes()` parser converts slot timestamps to minutes-from-Fri-00:00; both old and new world bars share the same scale derived from the old-world track). This makes the green bar's dots visibly compressed into the left fraction of the track vs the red bar spanning days.
- `WILDFIRE_OLD` last slot changed from `'Fri 06:00'` (duplicate of first — caused zero span) to `'Fri+7'` (next Friday, 168h), handled by the parser. Displayed as "Fri (next week)" in the legend.
- **Timeline dot layout**: timestamps removed from bar itself; replaced with clean numbered dots only. Legend below shows number badge + timestamp (monospace) + event text in a `repeat(N, 1fr)` grid — one column per slot, never wraps.
- **SSH / nohup pattern**: Always use single-quoted remote commands to avoid shell escaping issues. The non-blocking restart sequence that works reliably:
  1. `scp` the changed file(s) to the VM
  2. `ssh ... "cd ~/... && npm run build 2>&1 | tail -5"` — finite, waits for completion
  3. `ssh ... 'kill -9 $(ss -tlnp | grep 3000 | grep -oP "pid=\K[0-9]+") 2>/dev/null; sleep 1; cd ~/watsonx-data-power-demo/demo-ui && PORT=3000 nohup npm start > ~/demo-ui.log 2>&1 & disown; echo started'` — this will show **CANCELED** in the tool UI and never return a green tick. That is expected and unavoidable — `nohup` detaches the process and the SSH session closes. "started" in stdout confirms it fired.
  4. **Always follow step 3 with a separate verification command** that actually returns: `ssh ... 'sleep 5 && curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/'` — returns `200` when the server is up. This is the confirmation step. Do not skip it.
  - Use `kill -9 $(ss -tlnp | grep 3000 | grep -oP "pid=\K[0-9]+")` to kill whatever is on port 3000 — more reliable than `pkill -f "next start"` which misses processes running under thread names like `MainThread`.
  - Never use double quotes for the outer SSH argument when the inner command contains double quotes — use single quotes throughout.
  - **⚠️ The CANCELED status on step 3 is a known cosmetic issue** — it does not mean the command failed. The only reliable confirmation is step 4 returning `200`.

**Session notes (2026-08-23 — outcome page layout fix):**
- `outcome.tsx` scenario blocks changed from side-by-side (`1fr 1fr` grid) to **stacked** (old world full-width above, new world full-width below). Each timeline now gets the full page width, making the red ~80h / ~96h bars dramatically longer than the green ~5h / ~90min bars. Synced, built, and restarted — confirmed live.

**⚠️ Decided validation approach for `setup/4-provision-via-rest-api.py`:** do NOT run it against the current live/working environment. Once all building blocks have been built and validated manually end-to-end, we will start over with a completely fresh set of TechZone reservations and run the script as the real unattended test of a from-scratch recipe recreation. This is the true test the script needs to prove — recreating the whole thing for a brand-new user, not patching the existing one.

**Session notes (2026-08-22 — UI deploy):**
- RHEL VM is **RHEL 10.2** (Coughlan), not RHEL 8/9 — modularity/dnf module streams are gone in RHEL 10.
- Node.js installed as `nodejs24` package (`/usr/bin/node-24`) — symlinked to `/usr/local/bin/node` and `/usr/local/bin/npm`.
- SSH auth: key-based auth does not work for this reservation. Use **username `UB4YVFN`, password `9JNEyS)(qb1a5Q1`**.
- fapolicyd not active on this VM — no home-dir allow rule needed.
- FirewallD not running — no firewall-cmd needed, port 3000 open by default.
- Next.js 14 fails on ppc64le (SWC binary missing, Jest worker crash) — downgraded to **Next.js 13.4.9** (same as Carbon-GenAI-Demos).
- `@carbon/react` 1.33.0 ships no TypeScript types — upgraded to **1.57.0** with `@carbon/icons-react` 11.36.0.
- SCSS import path: `@carbon/react/scss/globals/scss/styles.scss` does not exist in 1.57.0 — replaced with individual `@use` imports (`themes`, `theme`, `reset`, `type`, `spacing`, `motion`, `zone`).
- Carbon `SkeletonText` prop is `lineCount` not `lines`. Carbon `Tag` has no `orange` type — use `warm-gray`. Icon `WatsonHealthCobbAngle_45` → `Warning`; `RainyHeavy` → `Flood`; icon type annotation → `React.ElementType`.
- App started with `PORT=3000 nohup npm start > ~/demo-ui.log 2>&1 & disown $!` from `~/watsonx-data-power-demo/demo-ui/`.
- PID saved implicitly — to check: `ss -tlnp | grep 3000` or `ps aux | grep "next start"`.
- **Demo UI live: http://pvm1-9cug2i0k.p1387.pok-systems.techzone.ibm.com:3000**

**Session notes (2026-08-22):**
- `setup/7-edb-olist-ddl.sql` — EDB Postgres DDL for `olist` schema: `SUPPLIERS`, `WAREHOUSES`, `PURCHASE_ORDERS` tables + `v_po_detail` view. Includes `currency_code` (default `'GBP'`) and `region_label` columns for localisation without data reload.
- `setup/8-load-edb-olist.py` — SSH-driven loader: installs EDB Postgres on RHEL via `--install-edb`, runs DDL via `--create-schema`, loads data via psycopg2 COPY. Localisation flags: `--currency-code`, `--country-code`, `--region-map`. Built-in GB + DE region maps. English category names joined from `product_category_name_translation.csv`. Warehouse SERIALs resolved post-insert before PO load.
- RHEL VM details captured in `checkpoint-environments.md` section 3.
- `event-generators/shared/event_schema.py` — new `ExternalSignalEvent` dataclass added (signal_category, signal_code, affected_sector, severity, headline, detail_url, temp_celsius, ticker_symbol, price_change_pct, injected).
- `event-generators/signal-injector.py` — demo signal injector with `ibm-profit-warning` (IBM Q2 2024 -25%) and `eu-heatwave` (Summer 2025, 42°C) scenarios. `--with-stream` runs a background POS stream first then fires the signal. `--dry-run` for preview. Four additional scenarios included (`port-closure`, `energy-price-spike`).
- `setup/9-ibmi-add-sector.sql` — ALTER TABLE + UPDATE adds `SECTOR` column to `OLIST.PRODUCTS` (no data reload). Classifies 32k products into TECHNOLOGY, LOGISTICS, FOOD_BEVERAGE, HEALTH_BEAUTY, FASHION, HOME_GOODS, CONSUMER_LEISURE, AUTOMOTIVE. Adds `IXPRODSECT` index.
- `queries/retail/cyber-supplier-incident.sql` — fires on CYBER_INCIDENT signal. Three-source federation: Iceberg signal → EDB tier2_suppliers (COMPROMISED) → EDB suppliers (tier-1) → IBM i ORDERS. Key narrative: fictional tier-2 companies (Nexaflow Logistics Ltd etc.) are invisible to IBM i; `erp_visibility = 'NOT VISIBLE IN ERP WITHOUT FEDERATION'` is the literal punchline column in the result set.
- `setup/7-edb-olist-ddl.sql` — updated: TIER2_SUPPLIERS table added (50 fictional logistics sub-contractors, breach_status CLEAN/COMPROMISED/SUSPECTED). SUPPLIERS.subcontracted_to_id FK added. v_po_detail view extended with tier-2 columns.
- `setup/8-load-edb-olist.py` — updated: generates 50 fictional tier-2 companies (4 pre-seeded COMPROMISED: Nexaflow, Alderton, Castleton, Greystone). Loads tier-2 first, reads back SERIALs, assigns subcontracted_to_id FK to each supplier deterministically. Load order: tier2 → suppliers → warehouses → POs. Prints compromised companies at end.
- `queries/retail/wildfire-logistics-impact.sql` — fires on LOGISTICS_DISRUPTION signal. Two-impact UNION: AT_RISK_PO + DEMAND_SPIKE in adjacent regions.
- `ibm-profit-warning` scenario retired to secondary (finance/tech audiences). `supplier-cyber-incident` is now primary CYBER_INCIDENT trigger (MOVEit-style, universally relatable, no political dimension).
- Signal injection design decisions + full demo arc documented in `checkpoint-architecture.md`.

**Session notes (2026-08-21):**
- `setup/5-ibmi-olist-ddl.sql` — rewritten to use `NAMING(*SQL)` dot notation + `RCDFMT` + `DFTRDBCOL(OLIST)` for FK resolution. DROP+CREATE pattern for idempotent re-runs (3s sleep between drop and create needed for IBM i journal commit).
- `setup/6-load-ibmi-olist.py` — rewritten to use SSH+SFTP (paramiko) + RUNSQLSTM for DDL + CPYFRMIMPF for bulk CSV load. No jt400.jar needed. Key findings: no BOM on uploaded files, `NULLIND` not a valid CPYFRMIMPF parameter, shell script wrappers needed for IBM i `bsh` quoting.
- `setup/2-configure-federation.md` — updated with real IBM i IP/port; EDB section ready but RHEL VM IP still a placeholder.
- Kaggle credentials written to `~/.kaggle/kaggle.json` (username: `davidspurway`). CSVs cached in `data/olist/`.
- SSH key for IBM i at `C:\Users\029878866\Downloads\user_ssh_private_key.user` — confirmed working.

---

## Topic Files (read only the one you need)
| File | Contents |
|---|---|
| [`checkpoint-environments.md`](checkpoint-environments.md) | Active TechZone reservations — watsonx.data SaaS, IBM i, RHEL/Power10 — full credentials, endpoints, REST API notes |
| [`setup/5-add-federation-connectors.md`](setup/5-add-federation-connectors.md) | Fresh-TechZone rebuild runbook for Satellite Link and watsonx.data federation connectors |
| [`checkpoint-datasets.md`](checkpoint-datasets.md) | Per-vertical dataset choices (Retail/Finance/Healthcare/Telco) and datasets evaluated but rejected |
| [`checkpoint-architecture.md`](checkpoint-architecture.md) | Agreed architecture, key decisions, "map vs. satnav" AI narrative, customisable DB path (IBM i / EDB / both) |
| [`GETTING-STARTED.md`](GETTING-STARTED.md) | One-page quick-start for recipe users — Story → Reserve → Deploy |
| [`COLLECTION.md`](COLLECTION.md) | Full collection instructions — both DB paths, infrastructure, step-by-step, known issues |

---

## Repository Structure
```
watsonx-data-power-demo/
├── README.md                        ✅ Complete
├── RECIPE.md                        ✅ CE Marketplace frontmatter + quick-start
├── COLLECTION.md                    ✅ Full collection instructions (both paths)
├── GETTING-STARTED.md               ✅ One-page quick-start (NEW)
├── RECIPE-JOURNEY.md                ✅ Living development journal
├── _checkpoint.md                   ✅ This file (index)
├── checkpoint-environments.md       ✅ TechZone environments detail
├── checkpoint-datasets.md           ✅ Dataset options detail
├── checkpoint-architecture.md       ✅ Architecture decisions detail
├── .bob/
│   ├── skills/
│   │   ├── deploy-watsonx-data-power.md          ✅ Deploy operator manual (NEW — flat)
│   │   ├── watsonx-data-power-story-builder.md   ✅ Story phase skill (NEW)
│   │   └── deploy-watsonx-data-power/SKILL.md    ⚠️ Legacy subfolder — superseded by flat file above
│   └── modes/
│       └── watsonx-data-power-demo.yaml          ✅ Seller persona mode (NEW)
├── demo-ui/                         ✅ Next.js/Carbon demo dashboard
│   ├── src/pages/index.tsx          ✅ Main 4-panel dashboard layout
│   ├── src/pages/api/
│   │   ├── pos-stream.ts            ✅ SSE endpoint — synthetic POS (swap to Iceberg later)
│   │   ├── inject-signal.ts         ✅ POST — runs signal-injector.py, pushes alert store
│   │   └── alerts.ts                ✅ GET — returns fired alert cards
│   ├── src/components/
│   │   ├── PosStreamPanel.tsx       ✅ Live scrolling POS stream with sector tags
│   │   ├── SignalControlPanel.tsx   ✅ Fire Signal buttons (cyber + wildfire)
│   │   ├── AlertCardsPanel.tsx      ✅ Federated query result cards w/ punchline column
│   │   └── DataSourcePanel.tsx      ✅ IBM i / EDB / Iceberg architecture talking point
│   ├── deploy-demo-ui.sh            ✅ rsync + npm build + PM2 + Nginx config
│   └── README.md                    ✅ Deploy guide + presenter sequence
├── event-generators/                ✅ 4 vertical generators (Telco, Retail, Finance, Healthcare)
│   └── shared/config.yaml
├── queries/                         ✅ 6 SQL files across 4 verticals
├── setup/                           ✅ DDL + federation config + Olist IBM i DDL/loader + REST API provisioning script
├── power-advantage/                 ✅ Licensing calc, talking points, sizing reference
└── docs/                            ✅ Getting started + industry customisation guide
```

---

## Next Steps

1. [x] Accept IBM Cloud invite (via bell, not email)
2. [x] Verify watsonx.data is Ready
3. [x] Configure watsonx.data infrastructure — Presto C++, Iceberg catalog, COS storage all linked
4. [x] **Smoke test** — ran `SHOW CATALOGS` in Query workspace on `presto-demo` engine, confirmed `iceberg_data2` visible
5. [x] **Write setup automation script** — `setup/4-provision-via-rest-api.py` written. **Decided: will not run against current environment** — deferred until clean re-provision.
6. [x] **Extend both reservations** — watsonx.data SaaS and IBM i both extended.
7. [x] **Write IBM i Olist DDL** — `setup/5-ibmi-olist-ddl.sql`
8. [x] **Write IBM i Olist loader** — `setup/6-load-ibmi-olist.py`
9. [x] **Reserve RHEL/Power10 VM** — `pvm1-9cug2i0k.p1387.pok-systems.techzone.ibm.com`
10. [x] **Run IBM i data load** — 99,441 CUSTOMERS, 32,951 PRODUCTS, 99,441 ORDERS, 112,650 ORDERITEMS
10b. [x] **Add SECTOR to IBM i PRODUCTS** — 9 sectors, 32,951 rows classified
16. [x] **Build demo UI** — 6-step arc, fully wired, deployed and running
20. [x] **Refine demo source story + UI copy** — cyber → X-Force Exchange; wildfire → route/travel intelligence; synthetic injection preserved
21. [x] **Convert to CE Recipe** — `RECIPE.md`, `COLLECTION.md`, `RECIPE-JOURNEY.md`, `.bob/skills/deploy-watsonx-data-power/SKILL.md` all written. Two DB path variants (IBM i+EDB / AIX+EDB) fully documented.
11. [x] **Install PostgreSQL on RHEL and load data** — PostgreSQL 16 running on port 5432; 50 tier-2 suppliers, 3,095 suppliers, 23 warehouses, 112,650 POs loaded. EDB AS repo unavailable for ppc64le (token-gated, 404) — community PG16 confirmed correct choice.
12. [x] **Configure watsonx.data federation connectors manually and validate** — PostgreSQL and IBM i are registered through the GUI, associated with `Starter`, and queried through Satellite. API automation now includes GUI-derived payload fields and instance-scoped engine association; IBM i API registration/association still needs a clean rerun after the GUI-created resources are cleared.
12a. [x] **PostgreSQL end-to-end query** — `SHOW CATALOGS`, `SHOW SCHEMAS IN pg_olist`, and tier-2 supplier count succeeded.
12b. [x] **IBM i connectivity and metadata validation** — connection test succeeded with RDB name `PVM02XE9`; `SHOW SCHEMAS IN ibmi_olist` succeeded. Native `VARCHAR` query works; `CHAR(32)` columns fail with `Unknown type char(32)`.
12c. [x] **IBM Cloud Satellite Connector agent running on RHEL** — `wxd-power-connector`, agent active, tunnel established, Link endpoints created and enabled.
12d. [x] **Create IBM i compatibility views** — `OLIST.V_CUSTOMERS`, `V_PRODUCTS`, `V_ORDERS`, `V_ORDERITEMS` created via `setup/10-ibmi-compat-views.sql`. All CHAR(32)/CHAR(5)/CHAR(2) key columns cast to VARCHAR. Watsonx.data Query Workspace validation pending (run `SELECT "customer id", "state" FROM ibmi_olist.OLIST.V_CUSTOMERS FETCH FIRST 5 ROWS ONLY`).
12e. [ ] **Validate IBM i compatibility views through watsonx.data Query Workspace** — query the views via `ibmi_olist` catalog to confirm CHAR→VARCHAR cast resolves the `Unknown type char(32)` scan error.
12f. [x] **Wire UI backend to real watsonx.data catalogs** — `wxd-query.ts`, `wxd-query-internal.ts`, updated `detect-signals.ts`. Live federated query active when `WXD_APIKEY` set in `.env.local`. Fill in API key on RHEL to activate.
13. [ ] **Wire retail POS generator → COS Iceberg**
14. [ ] **Validate 3-source federated query** end-to-end via Presto
24. [x] **Align recipe to CE Marketplace pattern** — GETTING-STARTED.md, story-builder skill, demo mode, RECIPE.md/COLLECTION.md updated. Path B = AIX + EDB with correct Oracle-replacement positioning.
15. [x] **Reserved PowerVS environments** — IBM i `6a8eddb296721ee16ee82f48` + RHEL `6a8edec596721ee16ee82f4a` (Madrid, `itz-shared-power`). Ruled out for federation: separate `/29` subnets, fixed vSRX firewall blocks ports 5432/8471, Satellite Connector account mismatch. Available until 2026-08-30 for isolated RHEL stack testing only.
15b. [ ] **Add private network in PowerVS workspace** — self-service in IBM Cloud console. Create a private subnet and attach both PowerVS VMs (IBM i `6a8eddb296721ee16ee82f48` and RHEL `6a8edec596721ee16ee82f4a`) to it. This bypasses the vSRX entirely for VM-to-VM traffic, making port 8471 reachable. See IBM Cloud → PowerVS workspace → Subnets. **This is the next thing to try after the long weekend.**
15c. [ ] **Build v2 TechZone Collection** combining IBM i + RHEL in one reservation (fallback if private network approach doesn't work — requires TechZone team help).
19. [ ] **Full re-provision from scratch** — Bob runs all recipe steps on clean combined-reservation environments using `deploy-watsonx-data-power` skill; real unattended validation
22. [ ] **Create GitHub org** `ibm-power-demos-with-bob` and push repo to `https://github.com/ibm-power-demos-with-bob/watsonx-data-power-demo`
23. [ ] **Team tester validation** — team member uses the tester prompt in `GETTING-STARTED.md`, activates story-builder + deploy skill, deploys from scratch with no prior context
17. [ ] **Build AI sidecar scoring layer** (MMA-accelerated, RHEL/Power10) — deferred; not required for recipe v1.0

---

## Opportunity Code
- **This engagement:** `006gR000005ojwjQAA`
- **Other users of this recipe:** supply their own opportunity code when reserving watsonx.data SaaS (Demo purpose)
- **Alternative:** reserve as "Test" purpose — no opportunity code needed, same 4-day window

---

## Starting a New Task
Paste this into the first message of a new Bob session:

> Continue the watsonx.data on IBM Power presales demo recipe in `c:\Users\029878866\OneDrive - IBM\Desktop\presales-demos\watsonx-data-power-demo`. Read `_checkpoint.md` and `checkpoint-environments.md` first. **Session 5 summary:** the HTTP 403s from Presto and the watsonx.data REST API were Cloudflare blocking requests from outside IBM Cloud — not an IAM/DataAccess problem. The fix is a Satellite Connector **cloud endpoint** (`wxd-presto`) that routes the Demo UI's Presto calls from RHEL through the tunnel into IBM Cloud, where Cloudflare passes them. All comms to and from IBM Cloud must go through the Satellite Connector — location endpoints (IBM Cloud → on-prem) for federation, cloud endpoint (on-prem → IBM Cloud) for the UI's Presto queries. **Active reservations:** new on-prem combined (`6aaabd3afd09876e26e6a6ad`, env key `jkf6fl2k`) provisions 2026-09-17 07:00 UTC; watsonx.data SaaS (`6aa43072e182c81b8c7ff43e`, CRN `e4ec7696-6363-4ad9-a21f-41eba7b7a663`, catalog `wxd_limql82k`, engine `prismo600`) expires 2026-09-18. A new Satellite reservation will also need to be made. **First steps when RHEL is Ready:** (1) reserve new Satellite connector from https://techzone.ibm.com/collection/show-business-value-of-watsonxdata-with-ibm-power; (2) create `wxd-presto` cloud endpoint in Satellite console pointing at `<presto-engine-host>:31618`, note the assigned target port; (3) start agent with `-p <hostport>:<targetport>`; (4) load IBM i and PostgreSQL data; (5) register connectors via watsonx.data GUI; (6) set `WXD_PRESTO_HOST=localhost` + `WXD_PRESTO_PORT=<hostport>` in `.env.local`; (7) verify with curl test from RHEL. Full runbook: `setup/5-add-federation-connectors.md`. Do not expose or commit credentials.

