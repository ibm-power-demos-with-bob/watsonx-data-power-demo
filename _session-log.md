# 📓 Session Log — watsonx.data on IBM Power Demo

> Archived from `_checkpoint.md`. Historical reference only — not read at session start.

---

## Session 12 (2026-09-29) — Clean-Slate Federation Validation

**Goal:** Prove the full recipe works on a brand-new TechZone reservation from scratch.

### What worked immediately
- Satellite agent still running on RHEL, endpoints active
- PostgreSQL data intact (112,650 rows), IBM i data intact (99k+ rows)
- `register_in_repo.py` correctly inserted database/catalog/catalog_engine rows into `ibm_lh_repo`

### Hard-won lessons from this session

**1. Dev Image API path changed in v2.2.0**
- `6-add-connectors-devimage.py` used `/v1/` — this is wrong for v2.2.0. Correct path is `/lakehouse/api/v2/`
- Auth for v2 API uses `secret: <LH_INSTANCE_SECRET>` header + `LhInstanceId: 0000-0000-0000-0000`
- `LH_INSTANCE_SECRET` is unique per reservation — get it via: `docker exec ibm-lh-presto env | grep LH_INSTANCE_SECRET`
- The `secret` header works for GET endpoints (engines, catalogs) but POST endpoints (database_registrations) also need a user JWT token — only obtainable via the browser UI

**2. Dev Image watsonx.data UI port is NOT always externally reachable**
- Previous reservation had UI port exposed externally. This reservation's UI (port 9443 on VM → 30355 external) was accessible at `https://eu-de.services.cloud.techzone.ibm.com:30355` but the `/lakehouse/api/v2/` path still requires a JWT for writes
- **The only reliable connector registration path is the browser GUI at the watsonx.data UI URL**
- `6-add-connectors-devimage.py` has been rewritten to use SSH→internal API for reads, but writes still require GUI

**3. AMS policy grants — GUI assigns them, direct DB inserts are overwritten**
- Inserting rows into `ams_0000_0000_0000_0000` directly works temporarily but `PolicySyncMgr` polls `lhconsole-api` every ~30s and overwrites the cache
- The authoritative path: register connector via GUI → go to catalog → Access control tab → add `ibmlhadmin` as Administrator
- `pg_olist` and `ibmi_olist` both needed manual access control grants in the UI before appearing in `SHOW CATALOGS`

**4. Presto catalog loading — `get_catalog.py` patches**
- `get_catalog.py` runs BEFORE `startPresto.py` in `entrypoint.sh` — files ARE present when JVM starts
- The `restpresto` Go server marks `db2fori` catalogs as `"invalid"` in its response — they don't appear in the AMS policy feed automatically
- Workaround: append catalog file restoration code to `get_catalog.py` AND write files to `/mnt/infra/ibm-lh-catalogs/` (the base catalog volume)
- **Simpler approach confirmed: register via GUI, grant access via GUI, then restart Presto once**

**5. IBM i connector type**
- Use `db2fori` (not `db2`) — uses JT400 driver (`jt400-20.0.7.jar`) in `/opt/presto/plugin/db2fori/`
- JDBC URL: `jdbc:as400://<satellite-host>:<port>;naming=sql;errors=full;fullErrors=true;`
- Do NOT include the RDB name (`PVM02XU9`) in the URL — leave database segment blank
- Use `naming=sql` not `naming=system` for SQL long names to work

**6. IBM i user password**
- The OS password (e.g. `.T+LvaASmx0w7si.`) changes with every TechZone reservation
- SSH uses key auth so the password isn't needed for SSH — but Db2 DRDA authentication uses it
- Must explicitly set the password on IBM i after each new reservation:
  `system "CHGUSRPRF USRPRF(<USER>) PASSWORD('<password>')"`
- Always pass `IBMI_PASSWORD` as an env var to setup scripts — never hardcode

**7. IBM i column names have spaces**
- IBM i DDS field names use spaces, not underscores: `"customer id"`, `"order id"`, `"seller id"`
- Always double-quote these in Presto SQL
- `pg_olist` columns use underscores normally
- `COUNT(*)` fails via JT400 (Presto translates to `COUNT(NULL)` which IBM i rejects) — use `SELECT *` or named columns instead

**8. Published services port list**
- Always get the full published services list from TechZone reservation page
- Key ports: Presto=25820, UI=30355, SSH=49753 (these change per reservation)

---

## Session 11 (2026-09-18) — UI Narrative Enhancements

- **`AudienceContext.tsx` (NEW)** — `AudienceProvider`, `useAudience` hook, floating `AudienceSelector` widget. Keys: `isTechnical`/`isSecurity`/`isExecutive`/`isOperations`. Reads `?audience=` query param (`ciso|architect|supply-chain|exec`).
- **`_app.tsx`** — Wrapped with `AudienceProvider` + `AudienceSelector`.
- **`index.tsx`** — Road Atlas narrative, KPI Blindspot Legend with audience badges, `Info` icon → `ℹ` Unicode.
- **`sources.tsx`** — Static Map cross-refs (`staticMapMissed`), audience relevance badges, `Info` imports removed → `ℹ`.
- **`live.tsx`** — Production pipeline indicator (✅), "How it Works" modal (ℹ), audience badge in header, conditional button, passes audience flags to components.
- **`outcome.tsx`** — Hero Metrics (80h→5h, ↓£14K), Business Actions, Power pillars, **audience-specific closing accordion**.
- **`AlertCardsPanel.tsx`** — Audience-specific enablement actions, audience badge in header.
- **`DataSourcePanel.tsx`** — Audience badges on source cards, conditional Live Query tab.
- **`STORY-BRIEFS.md` (NEW)** — 4 audience presenter briefs (CISO, Architect, Supply-Chain, Exec).
- **Fixed all TypeScript errors** — 13 rogue `]` syntax errors in `outcome.tsx`, `Info` import + 2 usages in `sources.tsx` → `ℹ`, `<2s` → `{'<2s'}`.
- **Deployed to RHEL** — `scp` → `npm run build` → `restart.sh`. All endpoints HTTP 200.

## Session 10 (2026-09-17/18) — Switch to Developer Base Image

- SaaS path definitively abandoned. Dev Image is primary path.
- **SKILL.md rewritten** — reflects Developer Base Image deployment path.
- **RECIPE.md updated** — Dev Image env ID `6aad32346d68a71f122a688d`, v1 manual reservation note.
- **`wxd-query-internal.ts`** — dual-mode auth: `WXD_PRESTO_USER` present → Basic auth (Dev Image); absent → IAM Bearer (SaaS legacy).
- **`.env.local.template`** — rewritten for Developer Base Image vars.
- **`setup/6-add-connectors-devimage.py`** — new automation script for Dev Image connector registration.
- **`setup/smoke-test.sh`** and **`setup/restart-ui.sh`** written.
- Catalogs registered via UI: `pg_olist` (PostgreSQL), `ibmi_olist` (IBM i).
- Federated queries confirmed working. `source: "live"` confirmed. Matched entity: `Nexaflow Logistics Ltd`.

## Session 9 (2026-09-17) — End-to-end live federation confirmed

- Full demo arc working on Dev Image 2.2.0 GA (VMware, TechZone `eu-de`).
- On-prem RHEL `129.40.125.69`, IBM i `129.40.125.73`.
- Presto `eu-de.services.cloud.techzone.ibm.com:46662` — Basic auth `ibmlhadmin`/`password`.
- IBM Cloud Satellite tunnel: PostgreSQL via `:33156`, IBM i via `:33180`.

## Sessions 7-8 — SaaS fight: root cause findings

Key hard-won lessons (kept for posterity):

- **IBMLH JWT** (`iss: *.lakehouse.saas.ibm.com`) is what Presto actually accepts — contains `lakehouse.data.access` — but is only obtainable via browser session, expires ~35 mins, not renewable via API.
- **Satellite `wxd-api` endpoint** does route through tunnel but Cloudflare resets the connection (ECONNRESET in agent logs) — management API not reachable this way.
- **GUI/API split:** GUI-registered catalogs invisible to `/v1/statement` API even after association. Root cause: multi-tenant shared instance ACL; service ID identity (`itz-110000sg2k`) doesn't have `lakehouse.data.access` in Presto's internal ACL regardless of grants. Irresolvable on shared instance.
- **`connection.name` breakthrough:** GUI Test connection payload uses `connection.name` for db name, not `connection.database`. API registration shape: `type: postgresql`, `connection: {name: "olist", hostname, port, username, password, ssl: false}`.
- **IBM i RDB name** must be the system relational database name (e.g. `PVM02XJK`), not `*LOCAL`.
- **Catalog name collision:** `iceberg_data` permanently taken in shared `itz-watsonx` MDS. Always use reservation-unique names (`wxd_<env-key-suffix>`).
- **Wizard is the only reliable setup path** — watsonx.data API schema changed Sep 2026; REST API provisioning script (`4-provision-via-rest-api.py`) is obsolete.

## Session 6 (2026-09-17) — RHEL + IBM i full data load

- PostgreSQL 16: `edbadmin`/`edbadmin1`, port 5432. 50 tier2_suppliers (4 COMPROMISED), 3095 suppliers, 23 warehouses, 112650 POs.
- IBM i: 99441 customers, 32951 products (SECTOR classified), 99441 orders, 112650 items. Compat views applied. RDB `PVM02XJK`.
- Demo UI deployed on RHEL: Node 20 (`dnf module enable nodejs:20`), all routes HTTP 200.

## Sessions 1-5 — Architecture foundations

- Bidirectional Satellite Connector architecture proven.
- Cloudflare blocks calls to `*.lakehouse.ibmappdomain.cloud` from outside IBM Cloud.
- CHAR→VARCHAR compat views required on IBM i and PostgreSQL for Prestissimo C++ connector.
- SSH + detached process pattern: **never** combine background server start and curl health-check in one SSH command — use two separate `execute_command` calls.
- Node.js on RHEL 9: `sudo dnf module enable -y nodejs:20` then install. On RHEL 10, `sudo dnf install -y nodejs` gives Node 22 directly.
- scp of demo-ui/ lands directories as `dr-x------` — always run `chmod -R u+rwX ~/watsonx-data-power-demo` before npm install.

---

## Hard-won lessons (permanent reference)

- **IBM Cloud Satellite tunnel direction:** on-prem RHEL runs the agent (podman, root required). Satellite cloud endpoints are for cloud→on-prem; location endpoints for on-prem→cloud.
- **Dev Image connector path:** GUI only (via `https://<host>:<ui-port>`). API connector registration is localhost-only from inside the VM.
- **Reservation-unique catalog names** required for SaaS shared instance. Not needed on Dev Image (isolated).
- **Pause/Resume Presto engine** after associating new catalogs — workers load lazily.
- **PostgreSQL GUI form:** Database name = `olist` — blank causes 400.
- **Cross-account Satellite connectivity proven** from `sftp-server` IBM Cloud VSI (`161.156.199.126`, account `7c7ab84cf29f2e005fd71e1635548059`).
