# From Demo to Recipe — watsonx.data on IBM Power

> This document captures the journey of turning the watsonx.data on IBM Power presales demo into
> a Client Engineering Bob Marketplace recipe. It is a living record — written session by session —
> so any team member picking this up later can understand why decisions were made, what was tried,
> what failed, and what the current state actually is.

---

## What We Are Building

A **Bob Marketplace recipe** that lets a seller or CE:

1. **Tailor the customer story** — guided by Bob, picking the right DB path variant (IBM i or AIX+EDB),
   adapting the scenario language to the target industry, and confirming the demo arc before touching
   any infrastructure.
2. **Deploy the demo environment** — Bob drives the full stack deployment via SSH onto fresh
   TechZone reservations: EDB Postgres install, IBM i data load, watsonx.data federation connector
   configuration, Next.js UI deploy.
3. **Run the demo** — a 6-step arc showing live federated signal detection across IBM i (or EDB),
   EDB Postgres, and an Apache Iceberg event stream.

The end state:
- A seller opens Bob, says "I want to run the watsonx.data Power demo for [customer]"
- Bob guides story tailoring (~15–30 minutes)
- Seller makes three manual TechZone reservations (~15 min effort, ~30–60 min provisioning wait)
- Bob deploys the full stack via SSH (~30–45 min automated)
- Demo is ready at `http://<fqdn>:3000` with no further manual steps

---

## Why This Demo, Why IBM Power

This demo was designed to answer a real pre-sales need: IBM i and Oracle on AIX customers who are
being asked "what does data modernisation actually look like on Power?" need more than a slide deck.

The demo shows:
- **IBM watsonx.data zero-ETL federation** — three live sources, one query, no data movement
- **IBM i as a live data asset** — not a legacy system to be replaced, but a co-equal source in
  a modern data fabric
- **EDB Postgres as Oracle-on-AIX equivalent** — EDB is the clean, license-free stand-in for what
  Oracle on AIX would be; no migration story required, the demo just works
- **IBM Power10 MMA readiness** — the RHEL VM running EDB and the UI is a Power10 node; the
  hardware acceleration story is built in without needing to add a separate AI component
- **A before/after narrative** — "static map" (Friday's report, Source 1 only) vs. "satnav"
  (real-time federated detection, all three sources) is the central metaphor

---

## Key Architecture Decisions

### 1. Two DB path variants from the start

**Decision made:** Build a single code base that supports both Path A (IBM i + EDB) and
Path B (AIX + EDB), controlled by which TechZone environments are reserved and which setup
scripts are run. The demo UI and federation queries are identical between paths.

**Why:** The IBM i audience and the AIX audience have different starting points but the same
demo arc. One recipe serves both. EDB is used in Path B not as a migration story but simply
as the cleanest license-free transactional DB on IBM Power — functionally equivalent to Oracle
on AIX without the licensing complexity that would make a real Oracle install impractical in a
demo environment.

**Path B (AIX+EDB) implementation note:** EDB holds the full Olist dataset (customers, orders,
products, suppliers, warehouses, POs). The IBM i setup scripts are simply skipped. The
watsonx.data EDB connector points to the extended EDB schema for Source 1 as well as Source 2.

### 2. Three TechZone environments, all v1 — no automated reservation

The TechZone MCP only supports v2 API collections. watsonx.data SaaS, IBM i on Power, and
RHEL on Power10 are all v1 environments. Automated reservation is not possible.

**Decision:** Make the manual reservation step short and clearly documented. Three forms,
~5 minutes each. Bob drives everything after the environments are Ready.

### 3. EDB replaces Oracle — not a new install complexity

EDB Postgres is a drop-in PostgreSQL-compatible replacement. The setup script
(`setup/8-load-edb-olist.py`) handles `dnf install` on RHEL 10 (no module streams needed),
schema creation, and data load via psycopg2 COPY from the Olist CSV files. This is a
one-command step once the RHEL VM is available.

**RHEL 10 note:** RHEL 10 (Coughlan) removed modularity/dnf module streams. EDB packages
install via direct `dnf install` from the EDB repository — the loader script handles repo setup.

### 4. Signal injection is synthetic, not live-API dependent

The two demo scenarios (cyber breach, wildfire logistics disruption) inject crafted synthetic
signals into the Iceberg event table. Live public feeds (CISA KEV, Open-Meteo corridor telemetry)
run in the background via `live-feed-fetcher.ts` as colour — but the demo trigger is always
the synthetic injection, giving narrative control and reliability.

**Upstream source channels are real classes:**
- Cyber signal → aligned to CISA Known Exploited Vulnerabilities / IBM X-Force Exchange category
- Wildfire signal → aligned to Route & Travel Intelligence / freight corridor disruption feeds

### 5. The tier-2 visibility punchline is the literal demo wow moment

The cyber scenario federation query returns a column:
`erp_visibility = 'NOT VISIBLE IN ERP WITHOUT FEDERATION'`

This is not a label added for demo purposes — it is the logical truth of the query. The
tier-2 sub-contractors exist only in EDB (Source 2). The IBM i ERP (Source 1) has no FK
to them. watsonx.data is the only system that can join across both. The column label makes
this unmissable to the audience.

### 6. The "map vs. satnav" AI narrative

The AI story is positioned as continuous real-time detection (the "satnav"), not a chatbot
or NL-to-SQL feature. The demo explicitly rejects NL-to-SQL as the "AI moment" — the AI
moment is the **sub-second federated detection** that would take a human analyst an hour
to replicate manually.

IBM Power10 MMA (Matrix Math Acceleration) is positioned as hardware readiness for on-box
AI scoring — always present, no extra configuration, already there when the customer wants to
add a scoring model later.

### 7. Next.js pinned to 13.4.9 for ppc64le

Next.js 14+ depends on the SWC compiler, which has no ppc64le binary. The demo UI is pinned
to Next.js 13.4.9 (same as Carbon-GenAI-Demos, which validated this on two separate RHEL 9.4
TechZone instances). This is a known constraint; it does not affect Carbon Design System usage.

### 8. File-based alert store — fixes Next.js worker isolation

In Next.js production mode, multiple worker processes do not share in-memory module-level state.
The alert store (`/tmp/wxd-demo-alerts.json`) and signal store (`/tmp/wxd-demo-signals.json`)
are file-based so all workers read and write a single shared state. DELETE + poll sequencing
ensures no race condition where a poll repopulates before a DELETE completes.

---

## Session Log

### Session 1–5 (2026-08-20 to 2026-08-21) — Foundation
- Kaggle Olist dataset downloaded and cached locally (`data/olist/`)
- IBM i DDL written (`setup/5-ibmi-olist-ddl.sql`) — SQL naming, RCDFMT, DFTRDBCOL, DROP+CREATE pattern
- IBM i loader written (`setup/6-load-ibmi-olist.py`) — paramiko SSH/SFTP, RUNSQLSTM, CPYFRMIMPF
- 99,441 CUSTOMERS, 32,951 PRODUCTS, 99,441 ORDERS, 112,650 ORDERITEMS loaded to IBM i
- SECTOR column added to PRODUCTS (`setup/9-ibmi-add-sector.sql`) — 9 sectors, 32,951 rows

### Session 6–8 (2026-08-21 to 2026-08-22) — EDB + Queries
- EDB DDL written (`setup/7-edb-olist-ddl.sql`) — SUPPLIERS, TIER2_SUPPLIERS, WAREHOUSES, PURCHASE_ORDERS
- 50 fictional tier-2 sub-contractors seeded (4 pre-seeded COMPROMISED: Nexaflow, Alderton, Castleton, Greystone)
- EDB loader written (`setup/8-load-edb-olist.py`) — install, DDL, psycopg2 COPY, GB/DE region maps
- Federation query for cyber incident written (`queries/retail/cyber-supplier-incident.sql`)
- Federation query for wildfire logistics impact written (`queries/retail/wildfire-logistics-impact.sql`)
- Signal injector written (`event-generators/signal-injector.py`)
- `ExternalSignalEvent` dataclass added (`event-generators/shared/event_schema.py`)

### Session 9–12 (2026-08-22) — UI Build and Deploy
- RHEL VM reserved (RHEL 10.2 / Power10): `pvm1-9cug2i0k.p1387.pok-systems.techzone.ibm.com`
- Next.js UI built with Carbon Design System — 4-panel dashboard, then refactored to 6-step arc
- Carbon `@carbon/react` 1.57.0 confirmed compatible; SCSS import path issue resolved
- Next.js pinned to 13.4.9 (SWC ppc64le constraint — same fix as Carbon-GenAI-Demos)
- UI deployed and running at `http://pvm1-9cug2i0k.p1387.pok-systems.techzone.ibm.com:3000`
- `restart.sh` added to demo-ui to cleanly kill orphan workers on port 3000
- nohup/disown deploy pattern documented — CANCELED status in Bob UI is cosmetic, verify with curl

### Session 13 (2026-08-25) — Signal Detection Split
- Signal injection and alert detection separated: `POST /api/inject-signal` writes to signal store;
  `POST /api/alerts` runs `detect-signals.ts` which checks business relevance before writing to alert store
- File-based stores for alerts and signals (fixes Next.js worker isolation in production)
- Alert cards for both scenarios get "What this enables" section bridging to `/outcome`
- Remote build validated on RHEL VM; stray file cleanup (api/SignalControlPanel.tsx, api/live.tsx)

### Session 14 (2026-08-25) — Demo Arc Refactor
- 5-step arc refactored to 6-step arc: `/` → `/sources` → `/live?scenario=cyber` → `/outcome?scenario=cyber` → `/live?scenario=wildfire` → `/outcome?scenario=wildfire`
- `/sources` Federation Architecture page added — three sources, blind spots, how watsonx.data bridges them
- `/live` and `/outcome` made scenario-aware via `?scenario=cyber|wildfire` query param
- `getServerSideProps` added to `/live` and `/outcome` to ensure query params available on first render
- Proportional timeline bars in `/outcome` — `toMinutes()` parser, shared scale, visually compressed green bar vs long red bar

### Session 15 (2026-08-25) — Live Feeds + Story Refinement
- Live background feeds connected: CISA KEV (`cisa.gov`) + Open-Meteo A9/AP-7 corridor telemetry
- `live-feed-fetcher.ts` — polls both feeds every 30s, writes enrichment context to Iceberg
- Acronyms expanded: "Cybersecurity Threat Intelligence · Known Exploited Vulnerabilities Feed" and "Route & Freight Corridor Telemetry"
- AI framing toned down: core value is zero-ETL federation speed + operational visibility; MMA positioned as hardware readiness
- Demo arc confirmed stable; UI running live

### Session 16 (2026-09-XX) — Recipe Packaging
- `RECIPE.md` written — CE Marketplace frontmatter, two DB path variants, quick-start
- `COLLECTION.md` written — full instructions, story phase, infra table, 6-step demo arc, resetting, customisation, known issues
- `RECIPE-JOURNEY.md` written — this file
- `.bob/skills/deploy-watsonx-data-power/SKILL.md` written — deploy skill for fresh environments
- `_checkpoint.md` updated — next step: install EDB on RHEL, configure federation connectors, then re-provision on clean environments

---

## Next Steps for Recipe Completion

The recipe files are written. The following steps remain before the recipe is fully deployable
on a clean set of environments:

1. [ ] **Install EDB Postgres on RHEL** — run `setup/8-load-edb-olist.py --install-edb` on a fresh RHEL VM, verify schema + data
2. [ ] **Configure watsonx.data federation connectors** — follow `setup/2-configure-federation.md` to wire IBM i + EDB + COS/Iceberg
3. [ ] **Wire POS event generator to Iceberg** — `event-generators/retail-pos-events.py` → COS bucket → Iceberg catalog
4. [ ] **Validate 3-source federated query** — run `queries/retail/cyber-supplier-incident.sql` end-to-end via Presto
5. [ ] **Reserve clean environments** — fresh watsonx.data SaaS + IBM i + RHEL/Power10 reservations
6. [ ] **Full re-provision from scratch** — Bob runs `setup/4-provision-via-rest-api.py` + all setup steps on the clean environments; this is the real unattended test of the recipe
7. [ ] **Publish to GitHub** — push to `https://github.com/ibm-power-demos-with-bob/watsonx-data-power-demo`
8. [ ] **Team tester validation** — team member follows recipe from the short prompt in `COLLECTION.md`, no prior context

---

## What a Tester Needs to Say to Bob

Once the recipe is published to the marketplace, a new team member should be able to start fresh with:

> *"I want to run the watsonx.data on IBM Power demo. My RHEL FQDN is [fqdn], my SSH key is at [path]. My IBM i is at [fqdn], my SSH key is at [path]. My watsonx.data API key is [key] and my instance CRN is [crn]. Deploy everything."*

Bob, with the `deploy-watsonx-data-power` skill active, should drive the full deployment from that
single prompt — no further instructions needed until the final `curl` returning `200` confirms the
demo is live.

---

*Maintained by the EMEA AI on IBM Power Squad.*
*Built with Bob (AI Assistant).*
