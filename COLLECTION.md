# watsonx.data on IBM Power — Demo Collection

> **One-sentence pitch:** Show your customer how watsonx.data federates across IBM i, PostgreSQL,
> and a live event stream — on IBM Power — reacting to a real-time cyber or logistics disruption
> in under a second, without moving a single byte of data.

---

## What This Is

A pre-sales demo that proves IBM watsonx.data's zero-ETL federation capability on IBM Power,
using a supply-chain intelligence scenario. The demo federates three live data sources:

| Source | Technology | What it holds |
|--------|-----------|---------------|
| Source 1 — Core ERP | Db2 for IBM i (or PostgreSQL, AIX path) | Customers, orders, products, sector classification |
| Source 2 — Operational DB | PostgreSQL 16 on RHEL/Power10 | Suppliers, tier-2 sub-contractors, warehouses, purchase orders |
| Source 3 — Event stream | Apache Iceberg on COS | Live cyber threat signals, route disruption events |

The demo runs on **real IBM Power TechZone infrastructure** using **actual watsonx.data**, **actual
IBM i** (or AIX), and **actual EDB Postgres**. There is no mock UI. The credibility comes from
showing real federation, real data, and real query response times.

**Audience:** Data architects, IT Directors, supply-chain leaders, and CISOs at organisations
running multi-source workloads on IBM Power who want to understand the IBM data modernisation story.

**Best fit:** Organisations running IBM i or Oracle on AIX/Power, with operational data siloed
in a separate system, wanting to drive real-time insight without ETL or data movement.

---

## Two DB Path Variants

This recipe supports two audience tracks. Choose the one that matches your customer.

### Path A — IBM i + PostgreSQL (Default)
**Use when:** The customer runs IBM i. The IBM i LPAR holds the core ERP data (orders, customers,
products). PostgreSQL holds the operational supplier data. watsonx.data federates across both.

**The story:** "Your IBM i holds the order book your business runs on. Your operational team added
a separate supplier database. Today those are two separate data islands. With watsonx.data, a single
federated query spans both — instantly — when a supplier breach or logistics disruption hits."

### Path B — AIX + EDB (Oracle replacement)
**Use when:** The customer runs Oracle on AIX and is considering modernisation. In this variant,
**IBM i is not used**. EDB Postgres (the Oracle-compatible build of PostgreSQL) plays the role
of the transactional database — replacing Oracle on IBM Power, without Oracle licensing cost or
application rewrite. EDB holds both the ERP-equivalent data (Customers, Orders, Products) and
the operational supplier data. The demo story and arc are identical to Path A.

**The EDB positioning:** EDB Postgres Advanced Server is Oracle-compatible — the same DDL,
the same stored procedure syntax, the same application-level behaviour your Oracle workloads
expect. The migration from Oracle to EDB on IBM Power is a real modernisation path. This demo
shows that EDB on IBM Power also participates in watsonx.data federation — so modernising to EDB
does not close the door on a data lakehouse strategy.

> **On deployment:** EDB Advanced Server is available for IBM Power (ppc64le) via EDB's customer
> portal (token-gated). For demo/recipe deployment, community PostgreSQL 16 from the PGDG repo
> is used as the underlying database engine — it is functionally identical for watsonx.data
> federation purposes, and requires no vendor account. The EDB story and positioning is accurate
> regardless of which binary is installed. If you have an EDB subscription that covers ppc64le,
> you may substitute the community PG16 install with EDB AS — the schema, data, and federation
> connector configuration are identical.

**Key difference for Path B:** The `setup/5-ibmi-olist-ddl.sql` and `setup/6-load-ibmi-olist.py`
steps are skipped. `setup/7-edb-olist-ddl.sql` and `setup/8-load-edb-olist.py` are extended with
`--full-dataset` to hold the complete Olist dataset (customers, orders, products, suppliers,
warehouses, POs) in PostgreSQL/EDB. The `pg_olist` federation connector covers all logical sources.
The watsonx.data SaaS reservation and Iceberg event stream are identical between both paths.

---

## The Demo Story

**The Problem:** Your customer has data in multiple places — a core ERP system (IBM i or Oracle),
a separate operational supplier database, and streaming event data arriving continuously. Each
system gives a partial view. When a tier-2 supplier is breached or a freight corridor closes, the
business can't connect the dots in real time without manual report-pulling that takes hours or days.

**The Demonstration:** Two live scenarios, each injecting a synthetic signal into a monitored
channel and watching the federated query system react:

| Scenario | Signal Type | Upstream Channel Class | Story |
|----------|-------------|----------------------|-------|
| **Cyber supplier incident** | `CYBER_INCIDENT` | Cybersecurity Threat Intelligence (CISA KEV / X-Force Exchange) | A MOVEit-style zero-day hits a tier-2 logistics sub-contractor your ERP has never heard of. watsonx.data joins across PostgreSQL (tier-2 supplier graph), IBM i (open orders), and the threat signal in under a second. The punchline: `erp_visibility = 'NOT VISIBLE IN ERP WITHOUT FEDERATION'`. |
| **Logistics disruption** | `LOGISTICS_DISRUPTION` | Route & Travel Intelligence (freight corridor telemetry) | A wildfire closes the A9/AP-7 corridor. At-risk purchase orders and demand-spike candidates surface immediately across both supplier and ERP sources. |

**The Wow Moment:** The audience sees a data source (the tier-2 supplier graph) that their ERP
system has literally never seen — surfaced live, in context, without any data movement.

**The Platform Story (3 pillars):**
- **Pillar 1 — Data Federation Speed:** Sub-second join across three sources, zero ETL
- **Pillar 2 — IBM i as a Live Data Asset:** The core ERP participates in real-time analytics without lifting data out
- **Pillar 3 — MMA Acceleration Readiness:** Power10 Matrix Math Acceleration hardware is already present on the RHEL node — the platform is AI-ready

---

## What Is Included

| Asset | Purpose |
|-------|---------|
| `deploy-watsonx-data-power` skill | Tells Bob how to deploy the full stack on fresh TechZone environments |
| `demo-ui/` | Next.js/Carbon dashboard — 6-step demo arc, live signal injection, federated alert cards |
| `setup/4-provision-via-rest-api.py` | watsonx.data SaaS provisioning via REST API (run once per fresh reservation) |
| `setup/5-ibmi-olist-ddl.sql` | IBM i DDL — CUSTOMERS, PRODUCTS, ORDERS, ORDERITEMS + SECTOR column |
| `setup/6-load-ibmi-olist.py` | SSH-driven loader for IBM i (paramiko + CPYFRMIMPF) |
| `setup/7-edb-olist-ddl.sql` | PostgreSQL DDL — SUPPLIERS, TIER2_SUPPLIERS, WAREHOUSES, PURCHASE_ORDERS, v_po_detail |
| `setup/8-load-edb-olist.py` | PostgreSQL loader — installs PostgreSQL 16 on RHEL, runs DDL, loads data via SSH + psql COPY |
| `setup/9-ibmi-add-sector.sql` | Adds SECTOR classification to IBM i PRODUCTS (idempotent ALTER + UPDATE) |
| `setup/2-configure-federation.md` | Step-by-step watsonx.data connector configuration for all three sources |
| `queries/retail/` | Federation SQL: stockout detection, cyber supplier incident, wildfire logistics impact |
| `event-generators/signal-injector.py` | Demo signal injector — fires `supplier-cyber-incident` or `eu-wildfire` scenarios |
| `demo-ui/src/pages/api/live-feed-fetcher.ts` | Background live feed ingestion (CISA KEV + Open-Meteo corridor telemetry) |
| `RECIPE-JOURNEY.md` | Full living log of every decision, bug, and deployment milestone |

---

## Before You Start — The Story Phase

**Do this before you touch any infrastructure.**

For every new customer, tell Bob:

> *"I want to run the watsonx.data Power demo. My customer is [name/industry]. They run [IBM i / Oracle on AIX]. Their main concern is [supply-chain risk / data silos / real-time insight / modernisation]."*

Bob will:
1. Help you choose the right DB path variant (A or B)
2. Tailor the scenario framing to your customer's industry and risk language
3. Confirm which of the two demo scenarios (cyber / wildfire) lands better for this audience
4. Produce talking points and anticipated objections

The story phase takes 15–30 minutes and is the single biggest factor in whether the demo lands.

---

## Infrastructure Requirements

**Three reservations are required. All must be made manually** — TechZone MCP cannot reserve
IBM Power environments.

### ⚠️ Critical networking requirement

**IBM i and RHEL must be reserved from the same TechZone collection** so they land in the same
PowerVS workspace and share a private network. Reservations from different collections land on
isolated network pods with no L3 routing between them — IBM i will be unreachable from RHEL,
and the federation connectors will fail.

The validated pattern uses **IBM Cloud PowerVS** for both IBM i and RHEL. PowerVS instances in
the same workspace share a private network and can also reach IBM Cloud services (watsonx.data
SaaS, COS) directly — no IBM VPN required for connectivity between services.

**IBM Cloud Satellite Connector** (running its agent as a Docker container on the RHEL VM)
bridges from IBM Cloud into the PowerVS workspace, allowing watsonx.data SaaS to reach the
IBM i and PostgreSQL endpoints via Satellite Link endpoints — without opening any inbound
firewall ports. Use Satellite **Connector** (lightweight Docker agent, minutes to set up), not
Satellite **Location** (full infrastructure deployment, requires worker nodes, overkill here).
The Connector must be in the same IBM Cloud account as watsonx.data SaaS.

### For Path A — IBM i + PostgreSQL

| Reservation | Where to reserve | What runs there |
|-------------|-----------------|----------------|
| watsonx.data SaaS | https://techzone.ibm.com/collection/watsonx-data | Presto engine, Iceberg catalog, COS storage |
| IBM i 7.6 PowerVS | [Certified PowerVS Base VMs](https://techzone.ibm.com/resource/69caf21433fe65185ca16a84) → **IBM i 7.6 IBM Cloud PowerVS VSI** | Db2 for IBM i — OLIST schema (ERP source) |
| RHEL 9 PowerVS | [Certified PowerVS Base VMs](https://techzone.ibm.com/resource/69caf21433fe65185ca16a84) → **Red Hat 9 IBM Cloud PowerVS VSI** | IBM Cloud Satellite Connector agent (Docker) + PostgreSQL 16 + demo UI |

### For Path B — AIX + EDB

| Reservation | Where to reserve | What runs there |
|-------------|-----------------|----------------|
| watsonx.data SaaS | Same as Path A | Same as Path A |
| RHEL 9 PowerVS | Same as Path A | IBM Cloud Satellite Connector agent (Docker) + PostgreSQL/EDB (all data) + demo UI |

> **IBM VPN** is not required for service-to-service connectivity when using PowerVS + Satellite.
> It is still needed for browser access to the demo UI during the presentation — the PowerVS RHEL
> VM is not publicly exposed.

### What to note from each reservation

**watsonx.data SaaS:**
- IBM Cloud API key (from IAM → Service credentials — use Student App ID, not your IBM ID)
- Instance CRN (from resource details)
- COS bucket name + endpoint
- Presto engine ID (from watsonx.data console → Infrastructure, after `4-provision-via-rest-api.py` runs)

**IBM i PowerVS reservation:**
- FQDN / IP address (from reservation details)
- SSH key (download "User Private SSH Key" from reservation details)
- IBM i `*SECOFR`-level user credentials

**RHEL 9 PowerVS reservation:**
- FQDN (from reservation details)
- SSH key (download from reservation details)
- Note: RHEL 9 from this collection — Node.js installed via NodeSource repo; deploy skill handles this

---

## How to Run This Recipe

### Step 1: Story Phase (15–30 minutes, no infrastructure needed)

```
Tell Bob:
  "I want to run the watsonx.data Power demo. My customer is [name/industry].
   They run [IBM i / Oracle on AIX]."

Bob will:
  - Confirm which DB path variant to use (A or B)
  - Tailor the scenario and talking points
  - Confirm the demo arc and punchline moments for your audience
```

### Step 2: Reserve TechZone Environments (15–45 minutes effort + provisioning wait)

Reserve **all required environments** (see Infrastructure Requirements above).

**For watsonx.data SaaS:**
- Go to https://techzone.ibm.com/collection/watsonx-data
- Select "Demo" purpose and enter your opportunity code (or "Test" — no code needed)
- Recommended geography: **Europe (London / eu-gb)** — confirmed region for watsonx.data SaaS in TechZone

**For IBM i 7.6 PowerVS (Path A only):**
- Go to https://techzone.ibm.com/resource/69caf21433fe65185ca16a84
- Click **IBM i 7.6 IBM Cloud PowerVS VSI** → Reserve
- Select geography **eu-gb (London)** to match watsonx.data SaaS region
- Download the private SSH key from reservation details

**For RHEL 9 PowerVS:**
- Go to https://techzone.ibm.com/resource/69caf21433fe65185ca16a84
- Click **Red Hat 9 IBM Cloud PowerVS VSI** → Reserve
- Select geography **eu-gb (London)** — must match IBM i reservation geography so they land in the same PowerVS workspace
- Download the private SSH key

> ⚠️ **Both PowerVS reservations must be in the same geography (eu-gb London preferred, or whichever is available).** This is what ensures they
> share the same PowerVS workspace and private network. Different geographies = different workspaces =
> no L3 connectivity between IBM i and RHEL.

**When all three are in Ready state, tell Bob:**

> *"All three environments are ready. watsonx.data is at [URL], IBM API key [key].
>   IBM i is at [FQDN], key at [path]. RHEL is at [FQDN], key at [path].
>   Deploy the watsonx.data Power demo."*

### Step 3: Deploy (Bob-driven, ~30–45 minutes)

Bob will execute the deploy skill (`deploy-watsonx-data-power`), which:

1. **Provisions watsonx.data** — runs `setup/4-provision-via-rest-api.py` to configure Presto engine, Iceberg catalog, and COS connector
2. **Loads IBM i data** (Path A) — runs `setup/5-ibmi-olist-ddl.sql` + `setup/6-load-ibmi-olist.py` + `setup/9-ibmi-add-sector.sql` via SSH to load 99k+ rows
3. **Installs and loads EDB** — runs `setup/8-load-edb-olist.py --install-edb` on the RHEL VM, then `setup/7-edb-olist-ddl.sql` + data load
4. **Configures federation connectors** — follows `setup/2-configure-federation.md` to wire all three sources in watsonx.data
5. **Deploys the demo UI** — rsync, `npm install`, `npm run build`, starts UI on port 3000 via `restart.sh`
6. **Verifies** — runs a smoke test federated query, confirms UI is reachable, confirms live feed fetcher is running

### Step 4: Demo Ready

Open `http://<rhel-fqdn>:3000` in your browser (IBM VPN must be active).

The demo runs a 6-step arc:

| Step | Route | What to show |
|------|-------|-------------|
| 1 | `/` | Static business report — "this is your Friday morning map" |
| 2 | `/sources` | Federation architecture — three sources, three blind spots, one join |
| 3 | `/live?scenario=cyber` | Inject the supplier cyber breach signal — watch the live stream react |
| 4 | `/outcome?scenario=cyber` | Cyber outcome — tier-2 visibility, ERP gap, IBM i order exposure |
| 5 | `/live?scenario=wildfire` | Inject the logistics disruption signal — watch at-risk POs surface |
| 6 | `/outcome?scenario=wildfire` | Wildfire outcome — route closure impact, demand-spike opportunity |

**Total elapsed time from fresh TechZone reservations:** ~90–120 minutes (mostly provisioning waits).
**Total human effort:** ~45 minutes.

---

## Resetting for Another Run

To clear signals and run the demo again:

```
Tell Bob: "Reset the demo for another run."

Bob will:
  - Call DELETE /api/alerts on the RHEL host (clears the alert store)
  - Confirm the POS stream is running cleanly
  - Confirm you are back at step 1 (/)
```

Alternatively, navigate directly to `/` on the demo UI — each live page clears its own alert store
on mount before polling begins.

---

## Customising for a Specific Customer

The demo is designed to be tailored in three ways:

### 1. Scenario selection
Use cyber only, wildfire only, or both — depending on audience. A CISO audience typically lands
better on the cyber scenario. A supply-chain or operations audience lands better on wildfire.

### 2. Industry language
The Olist dataset is a Brazilian retail dataset used as a generic supply-chain proxy. Bob can
help you remap the sector language, company names, and risk framing to your target industry
(manufacturing, pharma, automotive, retail) without touching any data or code.

### 3. DB path
Switch between Path A (IBM i + PostgreSQL) and Path B (AIX + EDB) by following the path selection
in the deploy skill. Both produce the same UI and the same demo arc — only the underlying data source
for Source 1 differs. For Path B, append `--full-dataset` to the PostgreSQL load step.

---

## Known Issues and Constraints

| Issue | Mitigation |
|-------|-----------|
| All TechZone PowerVS environments are v1 — Bob cannot auto-reserve | Manual reservation (~15 min total effort across three forms) |
| IBM i and RHEL **must** be in the same PowerVS workspace | Reserve both from [Certified PowerVS Base VMs](https://techzone.ibm.com/resource/69caf21433fe65185ca16a84) and select the **same geography**. Different geographies = different workspaces = no networking. |
| watsonx.data SaaS cannot reach PowerVS VMs directly | Deploy IBM Cloud Satellite **Connector** agent (Docker container) on the RHEL VM — Satellite Link bridges IBM Cloud → PowerVS private network. Use Connector (lightweight, minutes) not Location (full infrastructure, overkill). Agent makes outbound connections only — no inbound firewall rules needed. Must be in same IBM Cloud account as watsonx.data SaaS. |
| RHEL 9 (PowerVS collection) replaces RHEL 10 (earlier on-prem collection) | RHEL 9 is the validated platform for this recipe going forward. PostgreSQL 16 PGDG and Node.js 20/22 both support RHEL 9. Deploy skill updated accordingly. |
| Next.js 14+ fails on ppc64le (no SWC binary) | Pinned to Next.js 13.4.9 — same as Carbon-GenAI-Demos (validated on ppc64le) |
| PostgreSQL/EDB install requires internet from RHEL VM | PowerVS RHEL VMs have outbound internet. Uses PGDG repo (no token needed). EDB AS repo is token-gated and has no ppc64le packages — community PostgreSQL 16 is used; EDB positioning story is unaffected. |
| watsonx.data SaaS federation connector API — field names differ from UI labels | Confirmed via live API probing: `display_name` (not `database_display_name`), `type` (not `database_type`), `connection` (not `details`), `port` must be int not string. `5-add-federation-connectors.py` uses the correct names. |
| IBM i SSH key-based auth only — password does not work | Download "User Private SSH Key" from TechZone reservation details |
| nohup/disown restart pattern shows CANCELED in Bob UI | This is cosmetic — always follow with `curl` returning `200` to confirm |
| Live feeds (CISA KEV + Open-Meteo) require outbound internet from RHEL VM | PowerVS RHEL VMs have outbound internet — confirmed |

---

## Related Demos

| Demo | Story | When to use |
|------|-------|------------|
| **Carbon GenAI on IBM Power** | On-prem Granite AI / data sovereignty | AI capability, data residency, regulated industries |
| **PowerSC + Vault on IBM Power** | Automated certificate security | Security posture, compliance, certificate lifecycle risk |
| **watsonx.data on IBM Power (this demo)** | Zero-ETL data federation, supply-chain intelligence | Data modernisation, real-time insight, IBM i / Oracle modernisation |

All three run on TechZone IBM Power environments and can be positioned as a complementary
IBM Power pre-sales toolkit.

---

*Maintained by the EMEA AI on IBM Power Squad.*
*Built with Bob (AI Assistant).*
