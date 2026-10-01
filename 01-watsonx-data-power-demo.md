# Use Case 1 — watsonx.data / Supply Chain & Manufacturing / "The data your ERP has never seen"
## Bob MODE: pre-sales-demo

Build Path: Infrastructure / Platform Reality Demo

Why this is a strong demo: The audience sees a Presto query return `erp_visibility = 'NOT VISIBLE IN ERP WITHOUT FEDERATION'` — a live result, not a mock. That single column, surfaced from a tier-2 supplier graph their ERP has literally never touched, is the "lean in" moment. It proves zero-ETL federation across IBM i, PostgreSQL, and a streaming event channel in a single SQL call. The credibility comes entirely from using real IBM Power infrastructure — no simulated data, no faked latency, no cloud AI dependency.

Cluster: Data & AI · Industry: Manufacturing / Retail / Financial Services · Output shape: live federated demo environment + Carbon Design System dashboard + automated deployment scripts

Build path guardrail. The deliverable is a live Presto query spanning two real databases on real Power hardware. If the only IBM i or PostgreSQL touchpoint is a hardcoded string in a React component, the build is WRONG. The demo must execute a real federated SQL statement and surface a real result row in the UI.

---

## EXECUTIVE NARRATIVE

Imagine the head of supply chain at a manufacturer running IBM i. It's Monday morning and there's a security alert on their desk — a tier-2 logistics sub-contractor has been breached. Not a direct supplier. A supplier's supplier.

They open their ERP. Nothing. The ERP doesn't know that supplier exists.
They call the procurement team. Spreadsheet. Two hours later.
They ask IT to pull a report. "That'll take until Thursday."
The breach is already 36 hours old.

The goal is not to add another dashboard to the noise.

The goal is to make the data those systems already hold — the IBM i order book, the operational supplier graph, the live threat signal — answer the question in the same room, in the same minute.

---

## USE CASE DESCRIPTION

The pitch in one line:

> "Your IBM i holds the order book your business runs on. Your operational team added a supplier database. Today those are two separate data islands. With watsonx.data, a single federated query spans both — instantly — the moment a supplier breach or freight disruption hits."

Two live scenarios run against real data. Each injects a synthetic signal into a monitored channel and watches the federated query system react. The UI is a Carbon Design System dashboard running on RHEL Power:

- **Scenario A — Cyber supplier incident:** A MOVEit-style zero-day hits a tier-2 logistics sub-contractor. watsonx.data joins across PostgreSQL (tier-2 supplier graph), IBM i Db2 (open orders), and the threat signal. The punchline column `erp_visibility = 'NOT VISIBLE IN ERP WITHOUT FEDERATION'` appears in the live Presto result.
- **Scenario B — Logistics disruption:** A wildfire closes the A9/AP-7 freight corridor. At-risk purchase orders and demand-spike candidates surface immediately across both sources.

**Data sources federated live:**
- IBM i Db2 (`ibmi_olist`) — 99,441 customers, 112,650 order items, 32,951 products
- PostgreSQL 16 on RHEL/Power (`pg_olist`) — 3,095 suppliers, 23 warehouses, 112,650 purchase orders
- Event channel — synthetic signal injected at demo time via `event-generators/signal-injector.py`

**The land-and-expand line:** This architecture slots directly into a real watsonx.data SaaS deployment. The Satellite Connector used here is the same mechanism that bridges on-prem IBM i to watsonx.data in production.

---

## PREPARATION

**Required:**

- IBM VPN active (all TechZone environments are intranet-only)
- IBM Bob with this repo cloned and the `deploy-watsonx-data-power` skill installed
- Python 3.9+ on your laptop (for running setup scripts)
- Three TechZone reservations from the [Show Business Value of watsonx.data with IBM Power](https://techzone.ibm.com/collection/show-business-value-of-watsonxdata-with-ibm-power) collection — see PROMPT #2 for what to reserve and what to note

**Required — one human step before running scripts:**

> After reserving the IBM Satellite environment, **check your "Other" inbox** (not Focused — Outlook filters
> it there). You will receive an email from *DTE DTE v2 Infrastructure* with subject "Action required: You are
> invited to join an account in IBM Cloud". Click **"Join now."** and log in with your IBMid. This accepts your
> invitation to the `ITZ-V2` IBM Cloud account and enables ICR authentication.
> If you skip this, `setup/_start_satellite_agent.py` will fail with `invalid username/password`.

**Not required:**

- No IAM API key or IBM Cloud token for the watsonx.data Dev Image — it uses Basic auth (`ibmlhadmin`/`password`)
- No local Docker, no local database, no local Node.js — everything runs on the TechZone VMs
- No IBM i expertise — the setup scripts handle all CL commands via SSH

**Environment variables (store in a gitignored file — never commit real values):**

```
IBMI_HOST=<ibmi-fqdn-from-reservation>
RHEL_HOST=<rhel-fqdn-from-reservation>
SSH_USER=<techzone-username>
SSH_KEY=<path-to-downloaded-pem-key>
IBMI_PASSWORD=<ibmi-os-password-from-reservation>
IBMI_RDB=<rdb-name-confirm-via-DSPRDBDIRE>
WXD_SSH_PORT=<port-from-dev-image-published-services>
WXD_PRESTO_PORT=<port-from-dev-image-published-services>
```

---

## PROMPT #1 — Story tailoring (no infrastructure needed)

Use the **pre-sales-demo** mode and the **deploy-watsonx-data-power** skill.

```
I want to run the watsonx.data on IBM Power demo. 

My customer is [company name / industry].
They run [IBM i / Oracle on AIX / both].
Their main concern is [supply-chain risk / data silos / real-time insight / modernisation].
The audience in the room will be [job titles].
Duration: [15 / 30] minutes.

Help me:
1. Choose the right DB path — Path A (IBM i + PostgreSQL) or Path B (PostgreSQL-only / EDB story)
2. Tailor the cyber and wildfire scenario framing to this customer's industry and risk language
3. Give me 3 talking points and 2 anticipated objections with responses
4. Write my opening sentence — the one I say out loud when I click to the first screen
```

**Stop point:** You have a tailored scenario framing, an opening sentence, and a decision on Path A vs Path B. If Path B (no IBM i), note that — it changes which setup steps you run. Proceed to PROMPT #2 only when you know which path you are taking.

---

## PROMPT #2 — Reserve and configure TechZone environments

Use the **pre-sales-demo** mode and the **deploy-watsonx-data-power** skill.

```
I am deploying the watsonx.data on IBM Power demo on fresh TechZone environments.
I have reserved all three environments from the collection:
  https://techzone.ibm.com/collection/show-business-value-of-watsonxdata-with-ibm-power

My reservation details:
  IBM i + RHEL host prefix: <pvm-XXXXXXXX>    (from reservation — e.g. pvm-4r13fr3k)
  SSH user:    <USER>                          (e.g. UHJ907M)
  SSH key:     <path-to-pem>                  (e.g. C:\Users\...\pvm-XXXXXXXX-key.pem)
  IBM i password:  <password>                 (from reservation details page)
  IBM i RDB name:  <RDBNAME>                  (run DSPRDBDIRE on IBM i if unknown)
  Dev Image SSH port:    <port>               (from Published Services tab)
  Dev Image Presto port: <port>               (from Published Services tab)

DB path: [Path A — IBM i + PostgreSQL / Path B — PostgreSQL only]

Please update setup/reservation.py with these values, then run all four phases
of setup/RUNBOOK.md in order. Confirm each phase before proceeding to the next.
```

**Stop point:** All four phases complete. You should have:
- `setup/test_federation_live.py` → `PG v_suppliers COUNT: [[3095]]` and `IBMi v_customers COUNT: [[99441]]`
- `setup/test_cross_catalog_join.py` → `Cross-catalog join rows: 5`
- Demo UI running at `http://<RHEL_HOST>:3000` returning HTTP 200 on all pages

If any phase fails, the RUNBOOK's Known Quirks table covers the most common causes. If you are stuck, paste the error and tell Bob which step failed.

---

## EXPECTED OUTPUT

**TechZone infrastructure:**
- `IBM i + RHEL` — RHEL 9 with PostgreSQL 16, Satellite agent running, demo UI on :3000
- `IBM Cloud Satellite` — Connector bridging `pg-olist` (:5432) and `ibmi-db2` (:8471) to eu-de
- `watsonx.data Dev Image` — two registered catalogs (`pg_olist`, `ibmi_olist`) linked to `presto-01`

**Data loaded:**
- IBM i: `OLIST.V_CUSTOMERS` (99,441), `V_ORDERS` (99,441), `V_ORDERITEMS` (112,650), `V_PRODUCTS` (32,951)
- PostgreSQL: `olist.v_suppliers` (3,095), `v_purchase_orders` (112,650), `v_compromised_exposure` (pre-aggregated)

**Demo UI pages (all HTTP 200):**
- `demo-ui/src/pages/index.tsx` — supply-chain overview
- `demo-ui/src/pages/sources.tsx` — federation architecture
- `demo-ui/src/pages/live.tsx` — live signal injection + alert cards
- `demo-ui/src/pages/outcome.tsx` — response timeline comparison

**Setup scripts (all in `setup/`):**
- `setup/reservation.py` — single credentials file, all other scripts read from here
- `setup/RUNBOOK.md` — authoritative phase-by-phase deployment guide

**Verification:**
```bash
python3 setup/test_federation_live.py     # → PG COUNT 3095, IBM i COUNT 99441
python3 setup/test_cross_catalog_join.py  # → Cross-catalog join rows: 5
python3 setup/_check_ui.py               # → all pages HTTP 200
```

---

## DEMO SCRIPT

**Pre-demo setup (5 minutes before):**
- IBM VPN connected
- Browser open to `http://<RHEL_HOST>:3000`
- Second terminal with `python3 event-generators/signal-injector.py --list` ready

**Step 1 — The static world (1 min)**
Navigate to `/`. Show the supply-chain overview — "this is the world most customers live in. Reports. Exports. Yesterday's data."

**Step 2 — Three live sources (2 min)**
Navigate to `/sources`. Walk the federation architecture — IBM i on the left, PostgreSQL on the right, Satellite in the middle. "No data has moved. watsonx.data knows where it lives."

**Step 3 — Inject the cyber signal (3 min)**
Navigate to `/live?scenario=cyber`. Pause. "I'm going to trigger a supplier breach now — the same way your security operations team would receive a CISA KEV alert." Inject the signal. Watch the alert card fire. Point to the latency spinner — "that 5 seconds is a live Presto query crossing three data sources. This is not a mock."

**Step 4 — The ERP gap (2 min)**
Navigate to `/outcome?scenario=cyber`. Point to the timeline — "old world: 80 hours to get this answer. New world: 4 hours including human response time." Read the `erp_visibility` value aloud. That is the punchline.

**Step 5 — Repeat for logistics (3 min)**
Navigate to `/live?scenario=wildfire` → inject → `/outcome?scenario=wildfire`. "Same architecture. Different signal. Same answer in under a second."

**Step 6 — Close (2 min)**
Back to `/sources`. "Every source you saw is real. The IBM i is real. The PostgreSQL is real. The Satellite tunnel is what you'd use in production. This is what your architecture looks like on day one of a watsonx.data deployment."

---

## SAMPLE PROMPTS FOR LIVE Q&A

**1.** "Can you show me the actual SQL?"

Expected: Navigate to `http://<RHEL_HOST>:3000/api/detect-signals` — the raw JSON response includes the federated query string. Alternatively, open the watsonx.data UI at `https://<WXD_HOST>:<WXD_UI_PORT>` and run `SHOW CATALOGS` in the Presto console.

**2.** "How long would this take to connect to our real IBM i?"

Expected: "The Satellite Connector is the same mechanism we used here. If your IBM i is reachable from IBM Cloud, the federation connector registration takes about 10 minutes. The DDL mapping and views take another hour. You could have a proof query running the same day."

---

## WHAT GOOD LOOKS LIKE

A strong run feels like the audience has just seen their own system answer a question it has never been asked.

It should:
- Return a live Presto result with `erp_visibility = 'NOT VISIBLE IN ERP WITHOUT FEDERATION'` in the alert card
- Show ~5s query latency on the cyber scenario — the spinner should be visible (faster looks fake, slower loses the room)
- Have the alert card fire within one poll cycle (500ms) of the signal injection completing
- Survive a "show me the SQL" challenge — the query is real and readable

It should correctly decline to:
- Pretend the event stream is live external telemetry — the signal is injected synthetically and should be described honestly if asked

The output should not just flash an alert card.

It should answer: *"Which of our open purchase orders are exposed to this supplier breach, and why didn't our ERP know about it?"*

---

## KNOWN ISSUES & WORKAROUNDS

| Issue | Cause | Workaround | Impact |
|---|---|---|---|
| `SQL0206: Column NULL not found` on IBM i | Presto JDBC sends `COUNT(*)` / `SELECT 1` as NULL literal | Always use `COUNT("column_name")` — this is already correct in all views | None if using views |
| Catalogs missing from `SHOW CATALOGS` after registration | `catalog_engine` rows not inserted — lhconsole-api doesn't do this automatically | Run `setup/_fix_catalog_engine.py` then wait 75s for Presto restart | Demo blocked until fixed |
| `pg_olist` registration fails with HTTP 400 | PostgreSQL not listening on `0.0.0.0` | Run `setup/_configure_pg_remote.py` + `setup/_restart_pg.py` (reload is not enough) | Demo blocked until fixed |
| Satellite connector not showing `WSR04 Connected` | ICR login expired or podman container exited | Re-run `setup/_start_satellite_agent.py` — ICR token is refreshed automatically | Demo blocked until fixed |
| Cyber query takes >30s | `v_compromised_exposure` view missing | Run `setup/_apply_pg_compat_views.py` — this view pushes aggregation into PostgreSQL | Latency unacceptable for demo |
| `authenticator was not loaded` (Presto 500) | Presto still booting after restart | Wait 75s after any Presto restart before querying | Temporary — resolves itself |
| Node 16 on RHEL ppc64le | NodeSource doesn't support ppc64le | Node.js installed from RHEL repos — works fine with Next.js 14 | None |
| IBM i column names have spaces | Db2 for i schema uses `"customer id"` not `customer_id` | Compat views (`V_CUSTOMERS` etc.) already handle this — never query raw tables | None if using views |

---

## EXECUTIVE TAKEAWAY

> "Every system you already own just became a real-time data source — without a migration project, without moving data, and without buying a separate analytics platform."

---

## ADDITIONAL MATERIAL

- [`setup/RUNBOOK.md`](setup/RUNBOOK.md) — authoritative phase-by-phase deployment guide
- [`COLLECTION.md`](COLLECTION.md) — full technical detail, both DB path variants, and the demo story
- [`GETTING-STARTED.md`](GETTING-STARTED.md) — three-step human guide (story → reserve → deploy)
- [`RECIPE-JOURNEY.md`](RECIPE-JOURNEY.md) — full development log: every decision, bug, and deployment milestone
- [`.bob/skills/deploy-watsonx-data-power.md`](.bob/skills/deploy-watsonx-data-power.md) — the Bob skill that drives automated deployment
- Related recipe: IBM-Power-GenAI
