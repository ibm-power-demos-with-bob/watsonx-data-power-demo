# 🏗️ Checkpoint Topic — Architecture Decisions

_Referenced from `_checkpoint.md`. Content for agreed architecture and the customisable DB path only._

## Architecture Decisions (Agreed)

| Component | Technology | Where |
|---|---|---|
| **Lakehouse engine** | watsonx.data SaaS (Enterprise) | IBM Cloud, London (`eu-gb`) |
| **Source 1 — Core transactional** | Db2 for IBM i | IBM i LPAR on Power10 (TechZone, Poughkeepsie) |
| **Source 2 — Operational DB** | PostgreSQL 16 | RHEL VM on TechZone (Power10, ppc64le) — ✅ installed and loaded |
| **Source 3 — Streaming / events** | Apache Iceberg on COS | Built into watsonx.data SaaS reservation |
| **Power story** | Licensing calc + talking points | `power-advantage/` folder — narrative layer |
| **Real-time AI reaction layer** | Continuous scoring on a RHEL/Power10 "AI sidecar" VM, MMA-accelerated | Always present regardless of DB path chosen — see "Customisable DB path" below |

### Key decisions recorded
- **Not running on IBM Power** for the lakehouse itself — SaaS tells the same story visually
- **IBM i is the authentic Power element** — real Db2 for IBM i on a real Power10 LPAR
- **PostgreSQL replaces Oracle** — PostgreSQL connector in watsonx.data, no Oracle licensing risk. Using community PostgreSQL 16 (PGDG repo): EDB Advanced Server repo at `downloads.enterprisedb.com` is token-gated and publishes no ppc64le packages — 404 confirmed from the RHEL VM. Community PG16 is functionally identical for this demo.
- **PostgreSQL on RHEL** preferred over AIX — simpler, faster, audience never sees the OS
- **Demo purpose requires opportunity code** — use `006gR000005ojwjQAA` for this engagement; other users supply their own
- **IBM i TechZone reservation via MCP does not work** — must be reserved manually via TechZone UI
- **RHEL/Power10 VM(s) must also be reserved manually via TechZone UI** — same constraint as IBM i. Confirmed via `Carbon-GenAI-Demos` prior work: this environment type uses `systems-2` infrastructure with the v1 Provisioner; the TechZone MCP only supports v2 API collections, so MCP-based reservation will fail.
- **NL-to-SQL was explicitly rejected as the "AI" feature** — too feature/UX-level for the intended business-level narrative; the demo instead demonstrates the "map vs. satnav" metaphor as continuous real-time reaction, not a chatbot.

### Real-time AI reaction layer — "map vs. satnav" narrative
Continuous scoring (not NL-to-SQL/chatbot) running on Power, surfaced as dashboard alert cards, reinforcing Pillar 3 (MMA acceleration). Runs the existing per-vertical detector SQL continuously:
- `queries/retail/stockout-detection.sql`
- `queries/retail/cyber-supplier-incident.sql`   ← fires on CYBER_INCIDENT signal
- `queries/retail/wildfire-logistics-impact.sql` ← fires on LOGISTICS_DISRUPTION signal
- `queries/finance/fraud-flags.sql`
- `queries/healthcare/bed-availability.sql`
- `queries/telco/anomaly-detection.sql`

### External signal injection — "the event the static map can't see"
The demo narrative has two layers running simultaneously:

1. **Live background stream** — `retail-pos-events.py` emits POS transactions
   continuously (the "normal" stream the audience can see moving).
2. **Injected signal** — `event-generators/signal-injector.py` fires a
   pre-crafted `ExternalSignalEvent` into the same Iceberg table, triggering
   the sidecar's federated alert query.

**Why synthetic injection, not live APIs:**
- Reliable — no dependency on a news API returning something useful mid-demo
- Narrative control — the trigger is crafted to land the exact story
- Repeatable — every demo run tells the same clean arc
- Live API keys become optional colour if available; not required

**Two primary demo arc scenarios (aligned to real upstream source classes, synthetically injected):**

| Scenario key | Category | Upstream Source Channel | Reference / Class |
|---|---|---|---|
| `supplier-cyber-incident` | `CYBER_INCIDENT` | **Cybersecurity Threat Intelligence (Known Exploited Vulnerabilities)** | CISA AA23-187A / CVE-2023-34362 MOVEit zero-day pattern |
| `eu-wildfire` | `LOGISTICS_DISRUPTION` | **Route & Travel Disruption Intelligence** (Freight corridor telemetry) | Open-Meteo & road telemetry feed pattern (A9/AP-7 corridor closure) |

**The tier-2 visibility narrative (cyber scenario):**
The breach hits a company your ERP has never heard of — a tier-2 supplier
in your logistics network. Tier-1 direct suppliers live in the core ERP
(Source 1). Tier-2 relationships live in the operational supplier database
(Source 2). Without federation across both, you cannot even ask the question.
The query's final column — `NOT VISIBLE IN ERP WITHOUT FEDERATION` — is the
literal punchline. This narrative works regardless of whether Source 2 is
EDB, Oracle, Postgres, or any other system; the federation capability is the
point, not the specific technology.

**Why wildfire beats heatwave as the second trigger:**
The heatwave is *foreseeable* — a good analyst could scenario-plan for it.
A wildfire closing a specific road corridor at 6am is categorically unforeseeable.
The heatwave remains as context (it caused the conditions) and as an
*additional scenario* for FOOD_BEVERAGE/cold-chain audiences.

**Additional scenarios (not in default arc):**

| Scenario key | Best for |
|---|---|
| `ibm-profit-warning` | Finance/tech audiences — market signal story |
| `eu-heatwave` | FOOD_BEVERAGE/cold-chain audiences — demand spike angle |
| `port-closure` | Import-heavy retail or manufacturing verticals |
| `energy-price-spike` | Energy-intensive manufacturing verticals |

**Signal flow:**
```
signal-injector.py ──▶ ExternalSignalEvent ──▶ Iceberg retail_signals table
                                                        │
                                          AI sidecar polls every N seconds
                                                        │
                              ┌─────────────────────────┘
                              ▼
               CYBER_INCIDENT?        → cyber-supplier-incident.sql
                                      → "N tier-2 suppliers breached, £X
                                         exposure, NOT VISIBLE IN ERP"
               LOGISTICS_DISRUPTION?  → wildfire-logistics-impact.sql
                                      → "N freight POs at risk (can't move) +
                                         demand spike SKUs in adjacent regions"
```

**IBM i schema dependency:**
`OLIST.PRODUCTS.SECTOR` column — added by `setup/9-ibmi-add-sector.sql`
(ALTER + UPDATE, no data reload needed — run once against live IBM i).
Maps Olist English categories to sector codes matching `affected_sector`
in the signal event (e.g. `TECHNOLOGY`, `LOGISTICS`, `FOOD_BEVERAGE`).

**Demo arc (retail vertical):**
1. Show live POS stream — "this is the map, it shows what's happening now"
2. Fire `supplier-cyber-incident` — dashboard alert card 1 appears
3. Presenter: *"Four tier-2 suppliers. Eleven open orders. £47k exposure.
   Seven ship this week — and they can't move. Your ERP has never heard
   of any of these four companies. We found them because watsonx.data
   joined across the gap. Your static report cannot even ask this question."*
4. Fire `eu-wildfire` — dashboard alert card 2 appears alongside the first
5. Presenter: *"And at 6am this morning, a wildfire closed the A9. Seven
   freight POs can't move. Three SKUs in adjacent regions are already
   running low as consumers react. Your weekly freight report was printed
   last Friday."*
6. Pause. *"A static map could not have told you either of those things.
   Not because the data wasn't there — but because nothing was watching
   all of it, all at once, and joining it together in real time."*

### Customisable DB path — IBM i and/or EDB, not always both
Most real customers run **either** an IBM i shop **or** an Oracle-on-AIX shop, rarely both. Forcing both into every demo is less credible than letting the presenter pick the path that matches the prospect. Decided:

- **Iceberg (streaming) stays constant** in every path — always present.
- **The core/operational DB tier becomes a choice**, not a fixed pair:
  - **Path A — IBM i-centric**: Db2 for IBM i holds the core (and can absorb what EDB would otherwise hold) — for an IBM i shop.
  - **Path B — EDB-centric**: EDB Postgres on RHEL stands in for the Oracle-on-AIX estate — for an Oracle/AIX shop.
  - *(Both together remains a valid third option for prospects who genuinely run both.)*
- **Demo UI placement follows the DB choice:**
  - Path A → host the demo UI on **WebSphere Liberty running natively on the IBM i LPAR** — a strong secondary talking point in its own right: IBM i runs modern Java workloads, not just green-screen/RPG, which is often news to audiences who only know the legacy side.
  - Path B → host the demo UI on the **RHEL/Power10 VM**, same pattern already proven in `Carbon-GenAI-Demos` (Next.js/Carbon on RHEL).
- **The AI sidecar is decoupled from the DB choice — it is always a RHEL/Power10 VM**, present in every path (Path A, Path B, or both). Running the AI reaction layer inside IBM i's PASE (AIX/Linux) subsystem was considered and explicitly set aside — technically possible, since IBM i LPARs are Power10 hardware too, but not necessary. A RHEL sidecar VM alongside IBM i is simpler, reuses the already-proven `Carbon-GenAI-Demos` deployment pattern, and still counts as genuine Power hardware for the MMA/Pillar 3 story even when Path A (IBM i) is chosen for the DB tier.
